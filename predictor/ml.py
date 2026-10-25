"""Chargement des modèles (une seule fois par cible) et prédictions."""
import json
from functools import lru_cache

import joblib
import pandas as pd
from django.conf import settings

from .offers import OFFERS


@lru_cache(maxsize=None)
def load(target: str = "income"):
    """target = nom du sous-dossier dans ml_models/ (income, jeune…)."""
    model_dir = settings.MODEL_ROOT / target
    pipeline = joblib.load(model_dir / "pipeline.joblib")
    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    return pipeline, config


def predict_income(data: dict) -> dict:
    """data : dict avec les 12 variables brutes (mêmes noms que dans le notebook)."""
    pipeline, config = load("income")
    row = pd.DataFrame([data])[config["features"]]      # même ordre de colonnes
    proba = float(pipeline.predict_proba(row)[0, 1])
    high = proba >= config["threshold"]
    return {
        "probability": round(proba * 100, 1),
        "threshold": round(config["threshold"] * 100, 1),
        "label": ">50K" if high else "<=50K",
        "high": high,
    }


def predict_jeune(data: dict) -> dict:
    """data : dict avec les 7 variables du modèle « jeune actif » (sans l'âge)."""
    pipeline, config = load("jeune")
    row = pd.DataFrame([data])[config["features"]]
    proba = float(pipeline.predict_proba(row)[0, 1])
    young = proba >= config["threshold"]
    gap = abs(proba - config["threshold"])
    segment = "jeune" if young else "confirme"
    return {
        "probability": round(proba * 100, 1),
        "threshold": round(config["threshold"] * 100, 1),
        "young": young,
        "confidence": "élevée" if gap >= 0.25 else "moyenne" if gap >= 0.10 else "faible",
        **OFFERS[segment],
    }
