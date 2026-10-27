"""Ciblage premium (cible income) : segments, offres, explication du score, leviers, portefeuille.

Le modèle utilisé ici est la version « équitable » : il n'utilise NI le sexe, NI l'origine, NI le
pays d'origine (voir build_income_insights.py). Sa performance est identique au modèle complet.
"""
import csv
import io
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from django import forms
from django.conf import settings

from .forms import EDUCATION, FR_LABELS
from .ml import load
from .offers_income import TIERS

EDU_LABELS = dict(EDUCATION)

# Facteurs affichés à l'utilisateur (variables regroupées par sens métier)
FACTORS = [
    ("Niveau d'études", ["education-num"]),
    ("Situation familiale", ["marital-status", "relationship"]),
    ("Emploi (profession, secteur)", ["occupation", "workclass"]),
    ("Temps de travail", ["hours-per-week"]),
    ("Âge", ["age"]),
    ("Patrimoine (gains / pertes en capital)", ["capital-gain", "capital-loss"]),
]

MAX_ROWS = 20000
MAX_BYTES = 5 * 1024 * 1024
ID_ALIASES = ["id", "client", "client-id", "customer-id", "nom", "name", "identifiant"]


# ----------------------------------------------------------------------
# Chargement (une seule fois)
# ----------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_pro():
    folder = settings.MODEL_ROOT / "income"
    pipeline = joblib.load(folder / "pipeline_fair.joblib")
    cfg = load("income")[1]
    if "pro" not in cfg:
        raise RuntimeError("config.json ne contient pas la clé 'pro' : lancez build_income_insights.py")
    background = pd.read_csv(folder / "background.csv")
    return pipeline, cfg["pro"], background


def tier_of(p: float, pro: dict) -> str:
    if p >= pro["premium_threshold"]:
        return "premium"
    return "potentiel" if p >= pro["threshold"] else "standard"


def _proba(pipeline, frame: pd.DataFrame) -> np.ndarray:
    return pipeline.predict_proba(frame)[:, 1]


# ----------------------------------------------------------------------
# Formulaire (9 variables, sans variable sensible)
# ----------------------------------------------------------------------
class IncomeProForm(forms.Form):
    age = forms.IntegerField(label="Âge", min_value=17, max_value=90)
    hours_per_week = forms.IntegerField(label="Heures travaillées / semaine", min_value=1, max_value=99)
    education_num = forms.TypedChoiceField(label="Niveau d'études", choices=EDUCATION, coerce=int)
    capital_gain = forms.IntegerField(label="Gains en capital (USD)", min_value=0, max_value=99999, initial=0)
    capital_loss = forms.IntegerField(label="Pertes en capital (USD)", min_value=0, max_value=4356, initial=0)
    workclass = forms.ChoiceField(label="Type d'employeur")
    occupation = forms.ChoiceField(label="Profession")
    marital_status = forms.ChoiceField(label="Situation familiale")
    relationship = forms.ChoiceField(label="Logement / foyer")

    MAPPING = {"workclass": "workclass", "occupation": "occupation",
               "marital_status": "marital-status", "relationship": "relationship"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opts = load_pro()[1]["options"]
        for field, key in self.MAPPING.items():
            labels = FR_LABELS[key]
            choices = sorted(((v, labels.get(v, v)) for v in opts[key]), key=lambda c: c[1])
            self.fields[field].choices = [("", "Choisir…")] + choices
        for f in self.fields.values():
            f.widget.attrs["class"] = "input"

    def model_input(self) -> dict:
        d = self.cleaned_data
        return {
            "age": d["age"], "workclass": d["workclass"], "education-num": d["education_num"],
            "marital-status": d["marital_status"], "occupation": d["occupation"],
            "relationship": d["relationship"], "capital-gain": d["capital_gain"],
            "capital-loss": d["capital_loss"], "hours-per-week": d["hours_per_week"],
        }


# ----------------------------------------------------------------------
# Explication : « pourquoi ce score ? »
# ----------------------------------------------------------------------
def explain(row: pd.DataFrame, p: float, pipeline, background: pd.DataFrame) -> list:
    """Pour chaque facteur : écart (en points de %) entre le score du client et le score qu'il aurait
    si ce facteur était celui d'un client pris au hasard dans la base. > 0 : le facteur fait monter."""
    n = len(background)
    items = []
    for label, cols in FACTORS:
        mod = pd.concat([row] * n, ignore_index=True)
        for c in cols:
            mod[c] = background[c].to_numpy()
        delta = (p - float(_proba(pipeline, mod).mean())) * 100
        strength = "fort" if abs(delta) >= 10 else "moyen" if abs(delta) >= 3 else "léger"
        items.append({"label": label, "points": round(delta, 1), "strength": strength,
                      "direction": "up" if delta >= 0.5 else "down" if delta <= -0.5 else "flat"})
    items.sort(key=lambda i: abs(i["points"]), reverse=True)
    return items


# ----------------------------------------------------------------------
# Leviers : scénarios « et si ? » (corrélations observées, pas des causes)
# ----------------------------------------------------------------------
NEXT_EDU = {1: 9, 2: 9, 3: 9, 4: 9, 5: 9, 6: 9, 7: 9, 8: 9, 9: 13, 10: 13, 11: 13, 12: 13, 13: 14, 14: 16, 15: 16}


def levers(data: dict, p: float, pipeline) -> list:
    scenarios = []
    edu = data["education-num"]
    if edu in NEXT_EDU:
        scenarios.append((f"Niveau d'études : {EDU_LABELS[NEXT_EDU[edu]]}", {"education-num": NEXT_EDU[edu]}))
    if data["hours-per-week"] < 45:
        scenarios.append(("Temps de travail : 45 h / semaine", {"hours-per-week": 45}))
    if data["occupation"] != "Exec-managerial":
        scenarios.append(("Poste : cadre / manager", {"occupation": "Exec-managerial"}))
    if data["occupation"] != "Prof-specialty":
        scenarios.append(("Poste : profession intellectuelle", {"occupation": "Prof-specialty"}))
    out = []
    for label, change in scenarios:
        new_p = float(_proba(pipeline, pd.DataFrame([{**data, **change}]))[0])
        if (new_p - p) * 100 >= 1.0:
            out.append({"label": label, "new_probability": round(new_p * 100, 1),
                        "gain": round((new_p - p) * 100, 1),
                        "new_score": round(new_p * 100), "gain_score": round((new_p - p) * 100)})
    out.sort(key=lambda i: i["gain"], reverse=True)
    return out[:3]


# ----------------------------------------------------------------------
# Prédiction pour un client
# ----------------------------------------------------------------------
def predict_pro(data: dict) -> dict:
    pipeline, pro, background = load_pro()
    row = pd.DataFrame([data])[pro["features"]]
    p = float(_proba(pipeline, row)[0])
    key = tier_of(p, pro)
    offer = TIERS[key]
    stats = pro["tiers"][key]
    gap = abs(p - pro["threshold"])
    return {
        "probability": round(p * 100, 1),
        "score": round(p * 100),
        "threshold": round(pro["threshold"] * 100, 1),
        "premium_threshold": round(pro["premium_threshold"] * 100, 1),
        "high": key != "standard",
        "tier": key,
        "tier_label": offer["label"],
        "segment": offer["segment"],
        "action": offer["action"],
        "pitch": offer["pitch"],
        "bank": offer["bank"],
        "insurance": offer["insurance"],
        "tier_precision": round(stats["precision"] * 100),
        "tier_share": round(stats["share"] * 100),
        "confidence": "élevée" if gap >= 0.25 else "moyenne" if gap >= 0.10 else "faible",
        "factors": explain(row, p, pipeline, background),
        "levers": levers(data, p, pipeline),
    }


# ----------------------------------------------------------------------
# Portefeuille : scoring d'un fichier CSV
# ----------------------------------------------------------------------
class BatchError(ValueError):
    pass


def _norm(name: str) -> str:
    return str(name).strip().lower().replace("_", "-").replace(" ", "-")


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise BatchError("Encodage du fichier non reconnu (utilisez UTF-8).")


def read_portfolio(raw: bytes):
    """Lit le CSV, valide les colonnes et les valeurs. Retourne (DataFrame valide, ids, notes, n_total)."""
    if len(raw) > MAX_BYTES:
        raise BatchError("Fichier trop volumineux (5 Mo maximum).")
    text = _decode(raw)
    if not text.strip():
        raise BatchError("Le fichier est vide.")
    first = text.splitlines()[0] if text.strip() else ""
    sep = ";" if first.count(";") > first.count(",") else ("\t" if first.count("\t") > first.count(",") else ",")
    try:
        df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str, keep_default_na=False)
    except Exception as exc:
        raise BatchError(f"Fichier CSV illisible : {exc}")
    if len(df) == 0:
        raise BatchError("Le fichier ne contient aucune ligne.")
    if len(df) > MAX_ROWS:
        raise BatchError(f"Trop de lignes ({len(df)}). Maximum : {MAX_ROWS}.")

    _, pro, _ = load_pro()
    df.columns = [_norm(c) for c in df.columns]
    missing = [c for c in pro["features"] if c not in df.columns]
    if missing:
        raise BatchError("Colonnes manquantes : " + ", ".join(missing) + ".")

    id_col = next((c for c in ID_ALIASES if c in df.columns), None)
    ids = df[id_col].astype(str) if id_col else pd.Series(range(1, len(df) + 1)).astype(str)
    n_total = len(df)

    data = df[pro["features"]].copy()
    notes, valid = [], pd.Series(True, index=data.index)
    ranges = {"age": (17, 90), "education-num": (1, 16), "hours-per-week": (1, 99),
              "capital-gain": (0, 99999), "capital-loss": (0, 4356)}
    for col, (lo, hi) in ranges.items():
        num = pd.to_numeric(data[col].str.replace(",", ".", regex=False), errors="coerce")
        bad = num.isna() | (num < lo) | (num > hi)
        if bad.any():
            notes.append(f"{int(bad.sum())} ligne(s) écartée(s) : « {col} » absent ou hors de [{lo} ; {hi}]")
        valid &= ~bad
        data[col] = num
    for col, allowed in pro["options"].items():
        bad = ~data[col].isin(allowed)
        if bad.any():
            example = data.loc[bad, col].iloc[0]
            notes.append(f"{int(bad.sum())} ligne(s) écartée(s) : « {col} » valeur inconnue (ex. « {example} »)")
        valid &= ~bad
    data = data[valid].copy()
    for col in ranges:
        data[col] = data[col].astype(int)
    if data.empty:
        raise BatchError("Aucune ligne valide. " + " ; ".join(notes))
    return data, ids[valid].to_numpy(), notes, n_total


def score_portfolio(data: pd.DataFrame) -> np.ndarray:
    pipeline, pro, _ = load_pro()
    return _proba(pipeline, data[pro["features"]])


def summarize(proba: np.ndarray, ids, n_total: int, notes: list) -> dict:
    _, pro, _ = load_pro()
    keys = np.array([tier_of(p, pro) for p in proba])
    n = len(proba)
    tiers = []
    for key in ("premium", "potentiel", "standard"):
        mask = keys == key
        tiers.append({
            "key": key, "label": TIERS[key]["label"], "count": int(mask.sum()),
            "share": round(float(mask.mean()) * 100, 1),
            "avg_probability": round(float(proba[mask].mean()) * 100, 1) if mask.any() else None,
        })
    order = np.argsort(-proba)[:15]
    hist, _ = np.histogram(proba, bins=10, range=(0, 1))
    return {
        "n_total": n_total, "n_scored": n, "n_rejected": n_total - n, "notes": notes,
        "tiers": tiers,
        "expected_high": int(round(float(proba.sum()))),
        "top": [{"id": str(ids[i]), "probability": round(float(proba[i]) * 100, 1),
                 "tier": keys[i], "tier_label": TIERS[keys[i]]["label"]} for i in order],
        "histogram": [int(h) for h in hist],
    }


def _safe(value: str) -> str:
    """Neutralise l'injection de formules dans Excel (=, +, -, @ en début de cellule)."""
    value = str(value)
    return "'" + value if value[:1] in ("=", "+", "-", "@") else value


def portfolio_csv(data: pd.DataFrame, proba: np.ndarray, ids) -> str:
    _, pro, _ = load_pro()
    order = np.argsort(-proba)
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["rang", "client_id", "score_pct", "segment", "action_recommandee"] + pro["features"])
    values = data.reset_index(drop=True)
    for rank, i in enumerate(order, start=1):
        key = tier_of(float(proba[i]), pro)
        writer.writerow([rank, _safe(ids[i]), f"{proba[i] * 100:.1f}".replace(".", ","),
                         TIERS[key]["label"], TIERS[key]["action"]]
                        + [_safe(values.loc[i, c]) for c in pro["features"]])
    return "﻿" + buf.getvalue()


def template_csv() -> str:
    _, pro, _ = load_pro()
    rows = [
        ["C001", 45, "Private", 14, "Married-civ-spouse", "Exec-managerial", "Husband", 0, 0, 50],
        ["C002", 24, "Private", 9, "Never-married", "Other-service", "Own-child", 0, 0, 30],
        ["C003", 38, "Self-emp-inc", 13, "Divorced", "Prof-specialty", "Not-in-family", 5000, 0, 45],
        ["C004", 52, "State-gov", 10, "Married-civ-spouse", "Adm-clerical", "Wife", 0, 0, 40],
        ["C005", 29, "Private", 12, "Never-married", "Sales", "Not-in-family", 0, 0, 40],
    ]
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["client_id"] + pro["features"])
    writer.writerows(rows)
    return "﻿" + buf.getvalue()
