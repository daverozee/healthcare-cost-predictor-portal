PROCEDURES = {
    "mri_brain": {
        "name": "MRI brain without contrast",
        "category": "Imaging",
        "base_cost": 1850,
        "notes": "Common shoppable imaging service.",
    },
    "ct_abdomen": {
        "name": "CT abdomen and pelvis with contrast",
        "category": "Imaging",
        "base_cost": 2450,
        "notes": "Often varies by facility type and contrast use.",
    },
    "colonoscopy_screening": {
        "name": "Screening colonoscopy",
        "category": "Endoscopy",
        "base_cost": 3200,
        "notes": "Facility, anesthesia, pathology, and polyp removal can change final cost.",
    },
    "mammogram_screening": {
        "name": "Screening mammogram",
        "category": "Imaging",
        "base_cost": 240,
        "notes": "Often covered as preventive care, depending on plan rules.",
    },
    "knee_arthroscopy": {
        "name": "Knee arthroscopy",
        "category": "Outpatient surgery",
        "base_cost": 12500,
        "notes": "Surgery estimates can include facility, surgeon, anesthesia, and supplies.",
    },
    "urgent_care_visit": {
        "name": "Urgent care visit",
        "category": "Office visit",
        "base_cost": 185,
        "notes": "Labs, imaging, injections, or procedures can add separate charges.",
    },
    "er_moderate": {
        "name": "Emergency department visit, moderate complexity",
        "category": "Emergency care",
        "base_cost": 1800,
        "notes": "ER costs are highly variable and may include separate physician charges.",
    },
}

PAYER_FACTORS = {
    "commercial": 1.25,
    "medicare": 0.82,
    "cash": 0.70,
    "unknown": 1.00,
}

SITE_FACTORS = {
    "hospital_outpatient": 1.45,
    "ambulatory_surgery_center": 1.00,
    "independent_imaging_center": 0.75,
    "office": 0.85,
    "emergency_department": 2.15,
    "unknown": 1.00,
}

COMPLEXITY_FACTORS = {
    "low": 0.82,
    "typical": 1.00,
    "elevated": 1.28,
    "high": 1.75,
}

ZIP_PREFIX_FACTORS = {
    "0": 1.18,
    "1": 1.14,
    "2": 1.05,
    "3": 0.96,
    "4": 0.93,
    "5": 0.91,
    "6": 0.97,
    "7": 0.94,
    "8": 1.04,
    "9": 1.22,
}

