"""
Entraînement du modèle pour la cible SOUS_EVALUE — reprend le notebook sous_evalue_modeling.
Lancer :  python train_sous_evalue.py
Produit : ml_models/sous_evalue/pipeline.joblib  +  ml_models/sous_evalue/config.json

Population : uniquement les diplômés (education-num >= 13 : Bachelors, Masters,
Prof-school, Doctorate). Parmi eux, sous_evalue = 1 si le revenu est <= 50K.
education, education-num et income définissent la cible : ils sont exclus des
variables d'entrée (fuite de données), comme fnlwgt (poids d'échantillonnage).
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (accuracy_score, average_precision_score, classification_report,
                             f1_score, precision_recall_curve, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE = Path(__file__).resolve().parent
OUT = BASE / "ml_models" / "sous_evalue"
OUT.mkdir(parents=True, exist_ok=True)

GRAD_MIN = 13          # Bachelors

# ---------- Préparation ----------
df = pd.read_csv(BASE / "data" / "adult_clean.csv")
df = df.dropna().drop_duplicates().reset_index(drop=True)

grad = df[df["education-num"] >= GRAD_MIN].copy()                 # diplômés uniquement
grad["sous_evalue"] = (grad["income"] == "<=50K").astype(int)      # cible binaire
print(f"Diplômés : {len(grad)} sur {len(df)}")
print(grad["sous_evalue"].value_counts(normalize=True).round(3))

X = grad.drop(columns=["income", "sous_evalue", "fnlwgt", "source",
                       "education", "education-num"])
y = grad["sous_evalue"]

num_cols = X.select_dtypes(include="number").columns.tolist()
cat_cols = X.select_dtypes(exclude="number").columns.tolist()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)

preprocess = ColumnTransformer([
    ("num", StandardScaler(), num_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
])

# ---------- Meilleur modèle (hyperparamètres trouvés par RandomizedSearchCV, scoring AUC) ----------
# Comparaison en validation croisée 5 folds (AUC-ROC) : Rég. logistique 0.875,
# Random Forest 0.892, Gradient Boosting 0.900 → Gradient Boosting retenu.
best_model = Pipeline([
    ("prep", preprocess),
    ("clf", GradientBoostingClassifier(
        n_estimators=300, learning_rate=0.1, max_depth=4,
        min_samples_leaf=30, random_state=42)),
])

# ---------- Réglage du seuil (sur le train, validation croisée) ----------
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
proba_cv = cross_val_predict(best_model, X_train, y_train, cv=cv,
                             method="predict_proba", n_jobs=-1)[:, 1]
prec, rec, thr = precision_recall_curve(y_train, proba_cv)
f1 = 2 * prec * rec / (prec + rec + 1e-9)
best_thr = float(thr[np.argmax(f1[:-1])])
print("Seuil choisi :", round(best_thr, 3))

# ---------- Évaluation sur le test ----------
best_model.fit(X_train, y_train)
proba = best_model.predict_proba(X_test)[:, 1]
pred = (proba >= best_thr).astype(int)
print(classification_report(y_test, pred, target_names=["bien payé (0)", "sous-évalué (1)"]))
metrics = {"auc_roc": round(roc_auc_score(y_test, proba), 3),
           "auc_pr": round(average_precision_score(y_test, proba), 3),
           "accuracy": round(accuracy_score(y_test, pred), 3),
           "f1": round(f1_score(y_test, pred), 3)}
print(metrics)

# Équité : performance par sexe sur le test
fair = pd.DataFrame({"sex": X_test["sex"].values, "y": y_test.values, "pred": pred})
for s, g in fair.groupby("sex"):
    tp = ((g["y"] == 1) & (g["pred"] == 1)).sum()
    print(f"{s:7s} N={len(g):5d}  taux réel={g['y'].mean():.3f}  taux prédit={g['pred'].mean():.3f}"
          f"  recall={tp / max(g['y'].sum(), 1):.3f}")

# ---------- Sauvegarde finale : on ré-entraîne sur TOUS les diplômés ----------
best_model.fit(X, y)
joblib.dump(best_model, OUT / "pipeline.joblib")

options = {c: sorted(X[c].unique().tolist()) for c in cat_cols}
(OUT / "config.json").write_text(json.dumps({
    "threshold": best_thr,
    "features": X.columns.tolist(),
    "metrics": metrics,
    "rows": int(len(grad)),
    "rate": round(float(y.mean()), 3),
    "grad_min": GRAD_MIN,
    "model_name": "Gradient Boosting",
    "options": options,
}, indent=2, ensure_ascii=False), encoding="utf-8")
print("Modèle sauvegardé dans", OUT)
