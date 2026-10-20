"""Chargement des modèles (une seule fois) et prédiction pour les cibles income et sous_evalue."""
import json
from functools import lru_cache

import joblib
import pandas as pd
from django.conf import settings


@lru_cache(maxsize=1)
def load():
    pipeline = joblib.load(settings.MODEL_DIR / "pipeline.joblib")
    config = json.loads((settings.MODEL_DIR / "config.json").read_text(encoding="utf-8"))
    return pipeline, config


def predict_income(data: dict) -> dict:
    """data : dict avec les 12 variables brutes (mêmes noms que dans le notebook)."""
    pipeline, config = load()
    row = pd.DataFrame([data])[config["features"]]      # même ordre de colonnes
    proba = float(pipeline.predict_proba(row)[0, 1])
    high = proba >= config["threshold"]
    return {
        "probability": round(proba * 100, 1),
        "threshold": round(config["threshold"] * 100, 1),
        "label": ">50K" if high else "<=50K",
        "high": high,
    }


@lru_cache(maxsize=1)
def load_sous_evalue():
    directory = settings.BASE_DIR / "ml_models" / "sous_evalue"
    pipeline = joblib.load(directory / "pipeline.joblib")
    config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
    return pipeline, config


def predict_sous_evalue(data: dict) -> dict:
    """data : dict avec les 11 variables brutes d'un diplômé (sans education ni income)."""
    pipeline, config = load_sous_evalue()
    row = pd.DataFrame([data])[config["features"]]
    proba = float(pipeline.predict_proba(row)[0, 1])
    under = proba >= config["threshold"]
    return {
        "probability": round(proba * 100, 1),
        "threshold": round(config["threshold"] * 100, 1),
        "label": "sous-évalué" if under else "bien payé",
        "under": under,
    }
