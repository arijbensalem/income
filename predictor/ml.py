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


OCCUPATION_FR = {
    "Adm-clerical": "Administration, secrétariat", "Armed-Forces": "Forces armées",
    "Craft-repair": "Artisanat, réparation", "Exec-managerial": "Cadre, management",
    "Farming-fishing": "Agriculture, pêche", "Handlers-cleaners": "Manutention, nettoyage",
    "Machine-op-inspct": "Conduite de machines", "Other-service": "Services divers",
    "Priv-house-serv": "Emploi domestique", "Prof-specialty": "Profession spécialisée",
    "Protective-serv": "Sécurité, protection", "Sales": "Vente, commerce",
    "Tech-support": "Support technique", "Transport-moving": "Transport",
}
WORKCLASS_FR = {
    "Private": "Secteur privé", "Self-emp-not-inc": "Indépendant (hors société)",
    "Self-emp-inc": "Indépendant (en société)", "Federal-gov": "Fonction publique fédérale",
    "State-gov": "Fonction publique d'État", "Local-gov": "Fonction publique locale",
    "Without-pay": "Sans rémunération",
}
MARITAL_FR = {
    "Married-civ-spouse": "mariés", "Never-married": "célibataires", "Divorced": "divorcés",
    "Separated": "séparés", "Widowed": "veufs", "Married-spouse-absent": "mariés (conjoint absent)",
    "Married-AF-spouse": "mariés (conjoint militaire)",
}
HIGH_RISK = 0.70        # au-delà : risque élevé
MIN_GAIN = 0.03         # un levier n'est proposé que s'il baisse le risque d'au moins 3 points


def _age_bin(age: int) -> str:
    for upper, label in [(25, "moins de 25 ans"), (35, "25-34 ans"), (45, "35-44 ans"),
                         (55, "45-54 ans")]:
        if age < upper:
            return label
    return "55 ans et plus"


def _levers(pipeline, config, data: dict, proba: float) -> list:
    """Teste des profils identiques où un seul levier change, et garde le meilleur par levier.

    Le modèle mesure une association observée dans les données, pas un effet causal :
    les résultats sont des pistes de réflexion, pas des garanties.
    """
    variants = []
    for value in config["levers"]["occupation"]:
        if value != data["occupation"]:
            variants.append(("Profession", OCCUPATION_FR.get(data["occupation"], data["occupation"]),
                             OCCUPATION_FR.get(value, value), {**data, "occupation": value}))
    for value in config["levers"]["workclass"]:
        if value != data["workclass"]:
            variants.append(("Secteur d'emploi", WORKCLASS_FR.get(data["workclass"], data["workclass"]),
                             WORKCLASS_FR.get(value, value), {**data, "workclass": value}))
    if data["hours-per-week"] < 35:
        variants.append(("Temps de travail", f"{data['hours-per-week']} h / semaine",
                         "40 h / semaine (temps plein)", {**data, "hours-per-week": 40}))
    if not variants:
        return []

    rows = pd.DataFrame([v[3] for v in variants])[config["features"]]
    probas = pipeline.predict_proba(rows)[:, 1]

    best = {}
    for (variable, current, target, _), p in zip(variants, probas):
        gain = proba - float(p)
        if gain >= MIN_GAIN and (variable not in best or gain > best[variable]["gain"]):
            best[variable] = {"variable": variable, "current": current, "target": target,
                              "probability": round(float(p) * 100, 1), "gain": gain}
    ranked = sorted(best.values(), key=lambda item: item["gain"], reverse=True)
    for item in ranked:
        item["gain"] = round(item["gain"] * 100, 1)
    return ranked


def _reperes(config, data: dict) -> list:
    """Part de sous-évalués observée chez les diplômés qui partagent un trait non modifiable."""
    rep = config["reperes"]
    sex_label = "Femmes diplômées" if data["sex"] == "Female" else "Hommes diplômés"
    age_label = _age_bin(int(data["age"]))
    items = [
        (sex_label, rep["sex"].get(data["sex"])),
        (f"Diplômés {MARITAL_FR.get(data['marital-status'], data['marital-status'])}",
         rep["marital-status"].get(data["marital-status"])),
        (f"Diplômés de {age_label}", rep["age"].get(age_label)),
    ]
    return [{"label": label, "rate": round(rate * 100, 1)} for label, rate in items if rate is not None]


def predict_sous_evalue(data: dict) -> dict:
    """data : dict avec les 11 variables brutes d'un diplômé (sans education ni income)."""
    pipeline, config = load("sous_evalue")
    row = pd.DataFrame([data])[config["features"]]
    proba = float(pipeline.predict_proba(row)[0, 1])
    under = proba >= config["threshold"]

    if proba >= HIGH_RISK:
        level, advice = "eleve", (
            "Accompagnement prioritaire : comparer la rémunération aux grilles du poste et du "
            "secteur, préparer un entretien de négociation ou un projet de mobilité.")
    elif under:
        level, advice = "modere", (
            "Suivi recommandé : faire le point sur l'évolution de carrière et vérifier que le "
            "poste correspond au niveau de diplôme.")
    else:
        level, advice = "faible", (
            "Profil cohérent avec le niveau d'études : pas d'action prioritaire.")

    equity = None
    if data["sex"] == "Female" and under:
        gap = config["reperes"]["sex"]["Female"] - config["reperes"]["sex"]["Male"]
        equity = (f"Dans les données, les femmes diplômées sont sous-évaluées "
                  f"{round(gap * 100)} points plus souvent que les hommes. Une partie du risque "
                  f"ne dépend donc pas de leviers individuels : le signaler au référent égalité "
                  f"professionnelle de l'employeur.")

    return {
        "probability": round(proba * 100, 1),
        "threshold": round(config["threshold"] * 100, 1),
        "label": "sous-évalué" if under else "bien payé",
        "under": under,
        "level": level,
        "advice": advice,
        "levers": _levers(pipeline, config, data, proba) if under else [],
        "reperes": _reperes(config, data),
        "mean_rate": round(config["rate"] * 100, 1),
        "equity": equity,
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