const form = document.querySelector("#estimateForm");
const procedureSelect = document.querySelector("#procedure");
const apiStatus = document.querySelector("#apiStatus");
const lowEstimate = document.querySelector("#lowEstimate");
const pointEstimate = document.querySelector("#pointEstimate");
const highEstimate = document.querySelector("#highEstimate");
const confidenceBadge = document.querySelector("#confidenceBadge");
const procedureName = document.querySelector("#procedureName");
const resultNotes = document.querySelector("#resultNotes");
const factorList = document.querySelector("#factorList");
const caveats = document.querySelector("#caveats");
const meterFill = document.querySelector("#meterFill");

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

async function loadProcedures() {
  const health = await fetch("/api/health");
  if (!health.ok) throw new Error("API health check failed");
  apiStatus.textContent = "API online";
  apiStatus.className = "status ok";

  const response = await fetch("/api/procedures");
  const procedures = await response.json();
  procedureSelect.innerHTML = procedures
    .map((procedure) => `<option value="${procedure.id}">${procedure.name}</option>`)
    .join("");
}

function readForm() {
  const data = new FormData(form);
  return Object.fromEntries(data.entries());
}

function renderEstimate(estimate) {
  lowEstimate.textContent = currency.format(estimate.low_estimate);
  pointEstimate.textContent = currency.format(estimate.point_estimate);
  highEstimate.textContent = currency.format(estimate.high_estimate);
  procedureName.textContent = estimate.procedure_name;
  resultNotes.textContent = `${estimate.category} estimate with ${estimate.confidence} confidence.`;

  confidenceBadge.textContent = `${estimate.confidence} confidence`;
  confidenceBadge.className = `badge ${estimate.confidence}`;
  meterFill.style.width = estimate.confidence === "low" ? "46%" : "72%";

  factorList.innerHTML = Object.entries(estimate.factors)
    .map(([key, value]) => `<dt>${key.replaceAll("_", " ")}</dt><dd>${Number(value).toFixed(2)}</dd>`)
    .join("");

  caveats.innerHTML = estimate.caveats.map((caveat) => `<li>${caveat}</li>`).join("");
}

async function estimate(event) {
  event.preventDefault();
  const response = await fetch("/api/estimate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(readForm()),
  });

  if (!response.ok) {
    throw new Error(`Estimate failed: ${response.status}`);
  }

  renderEstimate(await response.json());
}

loadProcedures()
  .then(() => estimate(new Event("submit")))
  .catch((error) => {
    apiStatus.textContent = "API offline";
    apiStatus.className = "status error";
    resultNotes.textContent = error.message;
  });

form.addEventListener("submit", (event) => {
  estimate(event).catch((error) => {
    resultNotes.textContent = error.message;
  });
});

