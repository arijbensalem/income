"""Outils de la page « Jeune actif » : prédiction expliquée (pourquoi ce résultat ?).

Fichier séparé pour ne pas toucher aux fichiers partagés (views.py, ml.py, forms.py).

Méthode d'explication (simple et sans librairie externe) :
pour chaque variable, on remplace la valeur du client par celles de 300 profils réels
pris au hasard, et on regarde de combien la probabilité change en moyenne.
- contribution > 0 : cette réponse rapproche le client du profil « jeune actif » ;
- contribution < 0 : elle l'en éloigne.
C'est une mesure d'association observée dans les données, pas un lien de cause à effet.
"""
import json
from functools import lru_cache

import pandas as pd
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import JeuneForm
from .ml import load, predict_jeune

LABELS = {
    "occupation": "Profession",
    "workclass": "Type d'employeur",
    "hours-per-week": "Heures / semaine",
    "education-num": "Niveau d'études",
    "income_gt50k": "Revenu",
    "marital-status": "Situation familiale",
    "relationship": "Logement / foyer",
}
N_BACKGROUND = 300


@lru_cache(maxsize=1)
def background() -> pd.DataFrame:
    """300 profils réels tirés du dataset, utilisés comme point de comparaison."""
    _, config = load("jeune")
    df = pd.read_csv(settings.BASE_DIR / "data" / "adult_clean.csv").dropna()
    df["income_gt50k"] = (df["income"] == ">50K").astype(int)
    return df[config["features"]].sample(N_BACKGROUND, random_state=0).reset_index(drop=True)


def explain(data: dict) -> list:
    pipeline, config = load("jeune")
    row = pd.DataFrame([data])[config["features"]]
    proba = float(pipeline.predict_proba(row)[0, 1])
    bg = background()

    variants = []
    for feature in config["features"]:
        block = pd.concat([row] * len(bg), ignore_index=True)
        block[feature] = bg[feature].values
        variants.append(block)
    probas = pipeline.predict_proba(pd.concat(variants, ignore_index=True))[:, 1]

    out = []
    for i, feature in enumerate(config["features"]):
        avg = float(probas[i * len(bg):(i + 1) * len(bg)].mean())
        out.append({"feature": feature, "label": LABELS.get(feature, feature),
                    "contribution": round((proba - avg) * 100, 1)})
    return sorted(out, key=lambda d: abs(d["contribution"]), reverse=True)


@require_POST
def explain_api(request):
    """Comme /api/jeune/, plus la liste des contributions par variable."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "errors": {"__all__": ["JSON invalide"]}}, status=400)
    form = JeuneForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    data = form.model_input()
    return JsonResponse({"ok": True, **predict_jeune(data), "explanation": explain(data)})
