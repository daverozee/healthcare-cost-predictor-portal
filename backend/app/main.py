from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.predictor import estimate_cost, list_procedures
from app.schemas import EstimateRequest


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

app = FastAPI(
    title="Healthcare Cost Predictor",
    version="0.1.0",
    description="Consumer-friendly healthcare cost estimation API and portal prototype.",
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def portal():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/procedures")
def procedures():
    return list_procedures()


@app.post("/api/estimate")
def estimate(request: EstimateRequest):
    try:
        return estimate_cost(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

