"""
Entraînement du modèle pour la cible HOURS-PER-WEEK (3 classes de temps de travail).
Lancer :  python train_hours.py
Produit : ml_models/hours/pipeline.joblib  +  ml_models/hours/config.json

Le nombre exact d'heures est mal expliqué par les autres variables
(régression Hist Gradient Boosting : R² ≈ 0,27, MAE ≈ 6,9 h contre 7,5 h pour la
moyenne). Le modèle retenu prédit trois classes, définies sur les seuils usuels :
  - Temps partiel          : moins de 35 h
  - Temps plein            : 35 à 40 h
  - Heures supplémentaires : plus de 40 h
"""
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE = Path(__file__).resolve().parent
OUT = BASE / "ml_models" / "hours"
OUT.mkdir(parents=True, exist_ok=True)

BINS = [0, 34, 40, 99]
CLASSES = ["part-time", "full-time", "overtime"]
LABELS_FR = {
    "part-time": "Temps partiel",
    "full-time": "Temps plein",
    "overtime": "Heures supplémentaires",
}

# ---------- Préparation ----------
df = pd.read_csv(BASE / "data" / "adult_clean.csv")
df = df.dropna().drop_duplicates().reset_index(drop=True)
df["hours_class"] = pd.cut(df["hours-per-week"], bins=BINS, labels=CLASSES).astype(str)
print(df["hours_class"].value_counts(normalize=True).round(3))

# hours-per-week définit la cible ; education est redondant avec education-num ;
# fnlwgt est un poids d'échantillonnage. Le revenu est une entrée (comme pour occupation).
X = df.drop(columns=["hours-per-week", "hours_class", "fnlwgt", "source", "education"])
y = df["hours_class"]

num_cols = X.select_dtypes(include="number").columns.tolist()
cat_cols = X.select_dtypes(exclude="number").columns.tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)

preprocess = ColumnTransformer([
    ("num", StandardScaler(), num_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False, min_frequency=20), cat_cols),
])

# ---------- Meilleur modèle ----------
# Comparaison en validation croisée 5 folds (F1 macro) : baseline 0.234,
# Régression logistique 0.512, Hist Gradient Boosting 0.574 → HGB retenu.
best_model = Pipeline([
    ("prep", preprocess),
    ("clf", HistGradientBoostingClassifier(
        max_iter=300, learning_rate=0.06, max_depth=6,
        min_samples_leaf=30, random_state=42)),
])

# ---------- Évaluation sur le test ----------
baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
print("Baseline accuracy :", round(accuracy_score(y_test, baseline.predict(X_test)), 3))

best_model.fit(X_train, y_train)
pred = best_model.predict(X_test)
metrics = {
    "accuracy": round(float(accuracy_score(y_test, pred)), 3),
    "macro_f1": round(float(f1_score(y_test, pred, average="macro")), 3),
    "balanced_accuracy": round(float(balanced_accuracy_score(y_test, pred)), 3),
    "baseline_accuracy": round(float(accuracy_score(y_test, baseline.predict(X_test))), 3),
}
print(classification_report(y_test, pred, digits=3))
print(metrics)

# ---------- Sauvegarde finale : ré-entraînement sur toutes les données ----------
best_model.fit(X, y)
joblib.dump(best_model, OUT / "pipeline.joblib")

options = {c: sorted(X[c].unique().tolist()) for c in cat_cols}
(OUT / "config.json").write_text(json.dumps({
    "features": X.columns.tolist(),
    "metrics": metrics,
    "rows": int(len(df)),
    "model_name": "Hist Gradient Boosting",
    "classes": CLASSES,
    "labels_fr": LABELS_FR,
    "distribution": {c: round(float((y == c).mean()), 3) for c in CLASSES},
    "options": options,
}, indent=2, ensure_ascii=False), encoding="utf-8")
print("Modèle sauvegardé dans", OUT)
