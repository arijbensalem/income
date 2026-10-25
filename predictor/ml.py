"""Chargement du modèle (une seule fois) et prédiction pour les cibles income, occupation et relationship."""
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
def load_occupation():
    directory = settings.BASE_DIR / "ml_models" / "occupation"
    pipeline = joblib.load(directory / "pipeline.joblib")
    config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
    return pipeline, config


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
    """Charger le modèle CatBoost pour la prédiction de relation."""
    from catboost import CatBoostClassifier
    
    directory = settings.BASE_DIR / "ml_models" / "relationship"
    config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
    
    model = CatBoostClassifier(verbose=0)
    model_path = directory / "pipeline.cbm"
    model.load_model(str(model_path))
    
    return model, config


def predict_relationship(data: dict) -> dict:
    """data : dict avec les 14 variables brutes pour la prédiction de relation."""
    model, config = load_relationship()
    
    # Filtrer les colonnes pour exclure 'relationship' (c'est la cible, pas une feature)
    features_for_prediction = [col for col in config["feature_columns"] if col != "relationship"]
    
    # Créer un DataFrame avec les bonnes colonnes dans le bon ordre
    row = pd.DataFrame([data], columns=features_for_prediction)
    
    # Convertir les colonnes catégoriques en string
    for col in config["cat_cols"]:
        if col in row.columns:
            row[col] = row[col].astype(str)
    
    # Faire la prédiction
    prediction = model.predict(row)[0]
    probabilities = model.predict_proba(row)[0]
    classes = list(model.classes_)
    
    # Créer la liste classée par probabilité (comme occupation)
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
