"""
Entraînement du modèle « JEUNE ACTIF » (cible : age < 30) — classification binaire.
Usage commercial : ciblage marketing des offres jeunes (banque / assurance).
Lancer :  python train_jeune.py
Produit : ml_models/jeune/pipeline.joblib  +  ml_models/jeune/config.json

Choix importants
- L'âge est la CIBLE : il est retiré des variables d'entrée (sinon leakage).
- Pas de variables sensibles (sexe, origine, pays) ni de données patrimoniales :
  le formulaire ne demande que 7 informations simples, et on perd seulement ~0,3 point
  d'accuracy par rapport au modèle complet du notebook.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, classification_report,
                             f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE = Path(__file__).resolve().parent
OUT = BASE / "ml_models" / "jeune"
OUT.mkdir(parents=True, exist_ok=True)
AGE_LIMIT = 30

# ---------- Préparation ----------
df = pd.read_csv(BASE / "data" / "adult_clean.csv")
df = df.dropna().drop_duplicates().reset_index(drop=True)

df["jeune"] = (df["age"] < AGE_LIMIT).astype(int)                # cible binaire
df["income_gt50k"] = (df["income"] == ">50K").astype(int)        # le revenu devient une variable d'entrée

NUM_COLS = ["education-num", "hours-per-week", "income_gt50k"]
CAT_COLS = ["workclass", "marital-status", "occupation", "relationship"]
FEATURES = NUM_COLS + CAT_COLS
assert "age" not in FEATURES                                      # anti-leakage

X, y = df[FEATURES], df["jeune"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)

preprocess = ColumnTransformer([
    ("num", StandardScaler(), NUM_COLS),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_COLS),
])

# ---------- Meilleur modèle (hyperparamètres trouvés par RandomizedSearchCV dans le notebook) ----------
best_model = Pipeline([
    ("prep", preprocess),
    ("clf", HistGradientBoostingClassifier(
        learning_rate=0.1, max_leaf_nodes=31, min_samples_leaf=100,
        max_iter=200, l2_regularization=10, random_state=42)),
])

# ---------- Seuil métier : maximiser le F1 de la classe « jeune » (sur le train, en CV) ----------
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
proba_cv = cross_val_predict(best_model, X_train, y_train, cv=cv,
                             method="predict_proba", n_jobs=-1)[:, 1]
grid = np.round(np.arange(0.20, 0.71, 0.01), 2)
best_thr = float(grid[np.argmax([f1_score(y_train, proba_cv >= t) for t in grid])])
print("Seuil choisi :", best_thr)

# ---------- Évaluation sur le test ----------
best_model.fit(X_train, y_train)
proba = best_model.predict_proba(X_test)[:, 1]
pred = (proba >= best_thr).astype(int)
baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
print(classification_report(y_test, pred, target_names=[f">= {AGE_LIMIT} ans", f"< {AGE_LIMIT} ans"]))

precision = precision_score(y_test, pred)
share_young = float(y_test.mean())
metrics = {
    "accuracy": round(accuracy_score(y_test, pred), 3),
    "accuracy_05": round(accuracy_score(y_test, proba >= 0.5), 3),
    "baseline_accuracy": round(accuracy_score(y_test, baseline.predict(X_test)), 3),
    "balanced_accuracy": round(balanced_accuracy_score(y_test, pred), 3),
    "auc_roc": round(roc_auc_score(y_test, proba), 3),
    "precision": round(precision, 3),          # parmi les clients ciblés, part de vrais jeunes
    "recall": round(recall_score(y_test, pred), 3),   # part des jeunes retrouvés
    "share_young": round(share_young, 3),      # part de jeunes si on cible au hasard
    "lift": round(precision / share_young, 1), # efficacité vs ciblage au hasard
}
print(metrics)

# ---------- Sauvegarde finale : ré-entraînement sur TOUTES les données ----------
best_model.fit(X, y)
joblib.dump(best_model, OUT / "pipeline.joblib")

options = {c: sorted(X[c].unique().tolist()) for c in CAT_COLS}
(OUT / "config.json").write_text(json.dumps({
    "target": f"age < {AGE_LIMIT}",
    "threshold": best_thr,
    "features": FEATURES,
    "n_rows": len(df),
    "metrics": metrics,
    "options": options,
}, indent=2, ensure_ascii=False), encoding="utf-8")
print("Modèle sauvegardé dans", OUT)
