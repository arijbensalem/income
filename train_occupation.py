"""
Entraînement du modèle pour la cible OCCUPATION (3 familles de métiers).
Lancer :  python train_occupation.py
Produit : ml_models/occupation/pipeline.joblib  +  ml_models/occupation/config.json

Les 14 intitulés du recensement ne sont pas assez liés aux variables pour
dépasser ~36 % d'accuracy. Le modèle retenu prédit trois familles
(White-collar, Blue-collar, Service) avec un Hist Gradient Boosting.
"""
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from predictor.transformers import COLLAR_GROUPS, ENGINEERED_COLUMNS, LABELS_FR, RAW_FEATURES, OccupationFeatures

BASE = Path(__file__).resolve().parent
OUT = BASE / "ml_models" / "occupation"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(BASE / "data" / "adult_clean.csv")
df = df.dropna().drop_duplicates().reset_index(drop=True)
df = df[df["occupation"] != "Armed-Forces"].copy()
df["occupation_family"] = df["occupation"].map(COLLAR_GROUPS)
if df["occupation_family"].isna().any():
    missing = sorted(df.loc[df["occupation_family"].isna(), "occupation"].unique())
    raise SystemExit(f"Professions sans famille : {missing}")

X = df[RAW_FEATURES]
y = df["occupation_family"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

sample = OccupationFeatures().fit(X_train).transform(X_train.head(20))
cat_cols = [c for c in ENGINEERED_COLUMNS if sample[c].dtype == object]
num_cols = [c for c in ENGINEERED_COLUMNS if c not in cat_cols]

preprocess = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
    ("num", StandardScaler(), num_cols),
])

best_model = Pipeline([
    ("features", OccupationFeatures()),
    ("prep", preprocess),
    ("clf", HistGradientBoostingClassifier(
        max_iter=400,
        learning_rate=0.06,
        max_depth=6,
        min_samples_leaf=30,
        random_state=42,
    )),
])

best_model.fit(X_train, y_train)
pred = best_model.predict(X_test)
metrics = {
    "accuracy": round(float(accuracy_score(y_test, pred)), 3),
    "macro_f1": round(float(f1_score(y_test, pred, average="macro")), 3),
}
print(classification_report(y_test, pred, digits=3))
print(metrics)

# Sauvegarde finale : ré-entraînement sur toutes les données
best_model.fit(X, y)
joblib.dump(best_model, OUT / "pipeline.joblib")

options = {c: sorted(X[c].astype(str).unique().tolist()) for c in X.select_dtypes(exclude="number").columns}
(OUT / "config.json").write_text(json.dumps({
    "features": RAW_FEATURES,
    "metrics": metrics,
    "rows": int(len(df)),
    "model_name": "Hist Gradient Boosting",
    "label_scheme": "Collar groups",
    "labels_fr": LABELS_FR,
    "options": options,
}, indent=2, ensure_ascii=False), encoding="utf-8")
print("Modèle sauvegardé dans", OUT)
