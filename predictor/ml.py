import json
from functools import lru_cache

import joblib
import pandas as pd
from django.conf import settings

from .offers import OFFERS


@lru_cache(maxsize=None)
def load(target: str = "income"):
    """target = nom du sous-dossier dans ml_models/ (income, jeune, sous_evalue, hours…)."""
    model_dir = settings.MODEL_ROOT / target
    pipeline = joblib.load(model_dir / "pipeline.joblib")
    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    return pipeline, config


def load_sous_evalue():
    return load("sous_evalue")


def load_hours():
    return load("hours")


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


def predict_sous_evalue(data: dict) -> dict:
    """data : dict avec les 11 variables brutes d'un diplômé (sans education ni income)."""
    pipeline, config = load("sous_evalue")
    row = pd.DataFrame([data])[config["features"]]
    proba = float(pipeline.predict_proba(row)[0, 1])
    under = proba >= config["threshold"]
    return {
        "probability": round(proba * 100, 1),
        "threshold": round(config["threshold"] * 100, 1),
        "label": "sous-évalué" if under else "bien payé",
        "under": under,
    }


def predict_hours(data: dict) -> dict:
    """data : dict avec les variables brutes (le revenu est une entrée, les heures sont la cible)."""
    pipeline, config = load("hours")
    row = pd.DataFrame([data])[config["features"]]
    proba = pipeline.predict_proba(row)[0]
    classes = list(pipeline.named_steps["clf"].classes_)
    probs = {str(label): round(float(proba[i]) * 100, 1) for i, label in enumerate(classes)}
    # ordre naturel des classes (partiel → plein → heures sup.)
    ranked = [{"label": c, "label_fr": config["labels_fr"][c], "probability": probs[c]}
              for c in config["classes"]]
    top = max(ranked, key=lambda item: item["probability"])
    return {
        "label": top["label"],
        "label_fr": top["label_fr"],
        "probability": top["probability"],
        "classes": ranked,
    }

def load_occupation():
    return load("occupation")


def predict_occupation(data: dict) -> dict:
    """data : dict avec les variables brutes (le revenu est une entrée, pas la cible)."""
    pipeline, config = load_occupation()
    row = pd.DataFrame([data])[config["features"]]
    proba = pipeline.predict_proba(row)[0]
    classes = list(pipeline.named_steps["clf"].classes_)
    ranked = sorted(
        (
            {
                "label": str(label),
                "label_fr": config["labels_fr"][str(label)],
                "probability": round(float(proba[index]) * 100, 1),
            }
            for index, label in enumerate(classes)
        ),
        key=lambda item: item["probability"],
        reverse=True,
    )
    top = ranked[0]
    return {
        "label": top["label"],
        "label_fr": top["label_fr"],
        "probability": top["probability"],
        "classes": ranked,
    }
@lru_cache(maxsize=1)
def load_relationship():
    """Charge le modèle CatBoost (import paresseux : catboost n'est requis que pour cette cible)."""
    from catboost import CatBoostClassifier

    directory = settings.MODEL_ROOT / "relationship"
    config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
    model = CatBoostClassifier(verbose=0)
    model.load_model(str(directory / "pipeline.cbm"))
    return model, config


def predict_relationship(data: dict) -> dict:
    """data : dict avec les 14 variables brutes (la cible relationship n'en fait pas partie)."""
    model, config = load_relationship()

    # relationship est la cible, pas une variable d'entrée
    features = [col for col in config["feature_columns"] if col != "relationship"]
    row = pd.DataFrame([data])[features]            # même ordre de colonnes qu'à l'entraînement

    for col in config["cat_cols"]:
        if col in row.columns:
            row[col] = row[col].astype(str)

    probabilities = model.predict_proba(row)[0]
    classes = list(model.classes_)

    ranked = sorted(
        (
            {
                "label": str(label),
                "label_fr": config["labels_fr"].get(str(label), str(label)),
                "probability": round(float(proba) * 100, 1),
            }
            for label, proba in zip(classes, probabilities)
        ),
        key=lambda item: item["probability"],
        reverse=True,
    )
    top = ranked[0]
    return {
        "label": top["label"],
        "label_fr": top["label_fr"],
        "probability": top["probability"],
        "classes": ranked,
    }