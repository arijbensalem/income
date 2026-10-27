"""
Prépare le module « Ciblage premium » de la cible INCOME.

Lancer (après train_income.py, depuis le dossier qui contient manage.py) :
    python build_income_insights.py

Produit dans ml_models/income/ :
  - pipeline_fair.joblib : modèle SANS sexe / origine / pays d'origine (même Gradient Boosting)
  - background.csv       : échantillon de clients de référence (pour expliquer un score)
  - config.json          : on AJOUTE la clé "pro" (les anciennes clés ne changent pas)

Toutes les statistiques affichées dans l'application (précision par segment, lift, courbe de gain)
sont calculées sur le jeu de TEST, que le modèle n'a jamais vu : aucun chiffre n'est gonflé.
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE = Path(__file__).resolve().parent
OUT = BASE / "ml_models" / "income"
cfg = json.loads((OUT / "config.json").read_text(encoding="utf-8"))

SENSITIVE = ["sex", "race", "native-country"]          # exclues du modèle commercial
FEATURES = [c for c in cfg["features"] if c not in SENSITIVE]
PREMIUM_THRESHOLD = 0.60                               # au-dessus : segment « Premium »

# ---------- données (identiques à train_income.py) ----------
df = pd.read_csv(BASE / "data" / "adult_clean.csv").dropna().drop_duplicates().reset_index(drop=True)
y = (df["income"] == ">50K").astype(int)
X = df[FEATURES]
num_cols = X.select_dtypes(include="number").columns.tolist()
cat_cols = [c for c in FEATURES if c not in num_cols]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)


def make_model():
    return Pipeline([
        ("prep", ColumnTransformer([
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
        ])),
        ("clf", GradientBoostingClassifier(n_estimators=300, learning_rate=0.1, max_depth=3,
                                           subsample=0.85, random_state=42)),
    ])


# ---------- seuil « potentiel » (F1 max, validation croisée sur le train) ----------
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
proba_cv = cross_val_predict(make_model(), X_train, y_train, cv=cv, method="predict_proba", n_jobs=-1)[:, 1]
prec, rec, thr = precision_recall_curve(y_train, proba_cv)
f1 = 2 * prec * rec / (prec + rec + 1e-9)
threshold = float(thr[np.argmax(f1[:-1])])

# ---------- évaluation honnête : modèle entraîné sur le train, évalué sur le test ----------
eval_model = make_model().fit(X_train, y_train)
p = eval_model.predict_proba(X_test)[:, 1]
yt = y_test.to_numpy()
base_rate = float(yt.mean())
metrics = {"auc_roc": round(float(roc_auc_score(yt, p)), 3),
           "auc_pr": round(float(average_precision_score(yt, p)), 3)}

tiers = {}
for key, lo, hi in [("premium", PREMIUM_THRESHOLD, 1.01), ("potentiel", threshold, PREMIUM_THRESHOLD),
                    ("standard", 0.0, threshold)]:
    mask = (p >= lo) & (p < hi)
    tiers[key] = {"share": round(float(mask.mean()), 4),
                  "precision": round(float(yt[mask].mean()), 4),
                  "captured": round(float(yt[mask].sum() / yt.sum()), 4)}

order = np.argsort(-p)
gain = [{"k": 0, "precision": None, "recall": 0.0, "lift": None}]
for k in range(1, 101):
    n = max(1, int(round(len(p) * k / 100)))
    top = yt[order[:n]]
    gain.append({"k": k, "precision": round(float(top.mean()), 4),
                 "recall": round(float(top.sum() / yt.sum()), 4),
                 "lift": round(float(top.mean() / base_rate), 3)})

# ---------- modèle final (toutes les données) + échantillon de référence ----------
final = make_model().fit(X, y)
joblib.dump(final, OUT / "pipeline_fair.joblib")
X.sample(n=200, random_state=42).to_csv(OUT / "background.csv", index=False)

cfg["pro"] = {
    "features": FEATURES,
    "excluded_sensitive": SENSITIVE,
    "threshold": threshold,
    "premium_threshold": PREMIUM_THRESHOLD,
    "metrics": metrics,
    "metrics_with_sensitive": cfg.get("metrics", {}),
    "base_rate": round(base_rate, 4),
    "n_rows": int(len(df)),
    "n_test": int(len(y_test)),
    "tiers": tiers,
    "gain": gain,
    "options": {c: sorted(X[c].unique().tolist()) for c in cat_cols},
}
(OUT / "config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

print("Seuil potentiel :", round(threshold, 3), "| seuil premium :", PREMIUM_THRESHOLD)
print("Métriques (test, modèle équitable) :", metrics)
for k, v in tiers.items():
    print(f"  {k:10s} part {v['share']:.1%}  précision {v['precision']:.1%}  hauts revenus captés {v['captured']:.1%}")
print("Top 20 % :", gain[20])
print("Sauvegardé dans", OUT)
