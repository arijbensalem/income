"""
Entraînement du modèle pour la cible MARRIED — reprend le modèle des autres scripts.
Lancer : python train_married.py
Produit : ml_models/married/pipeline.joblib + ml_models/married/config.json
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (average_precision_score, classification_report,
                             precision_recall_curve, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE = Path(__file__).resolve().parent
OUT = BASE / "ml_models" / "married"
OUT.mkdir(parents=True, exist_ok=True)

# ---------- Préparation ----------
df = pd.read_csv(BASE / "data" / "adult_clean.csv")
df = df.dropna().drop_duplicates().reset_index(drop=True)

# Cible binaire pour Married (ex: si 'marital.status' contient Married)
df["married_high"] = df["marital-status"].str.contains("Married", case=False, na=False).astype(int)

X = df.drop(columns=["marital-status", "married_high", "fnlwgt", "source", "education", "income", "relationship"], errors="ignore")
y = df["married_high"]

num_cols = X.select_dtypes(include="number").columns.tolist()
cat_cols = X.select_dtypes(exclude="number").columns.tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)

preprocess = ColumnTransformer([
    ("num", StandardScaler(), num_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
])

# ---------- Modèle ----------
best_model = Pipeline([
    ("prep", preprocess),
    ("clf", GradientBoostingClassifier(
        n_estimators=300, learning_rate=0.1, max_depth=3,
        subsample=0.85, random_state=42)),
])

# ---------- Réglage du seuil ----------
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
proba_cv = cross_val_predict(best_model, X_train, y_train, cv=cv,
                             method="predict_proba", n_jobs=-1)[:, 1]
prec, rec, thr = precision_recall_curve(y_train, proba_cv)
f1 = 2 * prec * rec / (prec + rec + 1e-9)
best_thr = float(thr[np.argmax(f1[:-1])])
print("Seuil choisi :", round(best_thr, 3))

# ---------- Évaluation ----------
best_model.fit(X_train, y_train)
proba = best_model.predict_proba(X_test)[:, 1]
print(classification_report(y_test, (proba >= best_thr).astype(int),
                            target_names=["Non-marié", "Marié"]))
metrics = {"auc_roc": round(roc_auc_score(y_test, proba), 3),
           "auc_pr": round(average_precision_score(y_test, proba), 3)}
print(metrics)

# ---------- Sauvegarde finale ----------
best_model.fit(X, y)
joblib.dump(best_model, OUT / "pipeline.joblib")

options = {c: sorted(X[c].unique().tolist()) for c in cat_cols}
(OUT / "config.json").write_text(json.dumps({
    "threshold": best_thr,
    "features": X.columns.tolist(),
    "metrics": metrics,
    "options": options,
}, indent=2, ensure_ascii=False), encoding="utf-8")
print("Modèle sauvegardé dans", OUT)