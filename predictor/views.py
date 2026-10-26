import json
from pathlib import Path

import joblib
import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .forms import (IncomeForm, JeuneForm, MarriedForm, OccupationForm,
                    RelationshipForm, SousEvalueForm)
from .ml import (load, load_sous_evalue, predict_income,
                 predict_jeune, predict_occupation, predict_relationship, predict_sous_evalue)


def home(request):
    _, config = load("income")
    _, jeune = load("jeune")
    _, sous_evalue = load_sous_evalue()
    return render(request, "predictor/home.html", {
        "metrics": config["metrics"],
        "jeune": jeune["metrics"],
        "sous_evalue": sous_evalue,
    })


def income_page(request):
    return render(request, "predictor/income.html", {"form": IncomeForm()})


def _read_payload(request):
    try:
        return json.loads(request.body), None
    except json.JSONDecodeError:
        return None, JsonResponse(
            {"ok": False, "errors": {"__all__": ["JSON invalide"]}}, status=400
        )


@require_POST
def income_api(request):
    """Reçoit le formulaire (fetch / JSON) et renvoie la prédiction en JSON."""
    payload, error = _read_payload(request)
    if error:
        return error
    form = IncomeForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, **predict_income(form.model_input())})


# ----------------------------------------------------------------------
# MARRIED
# ----------------------------------------------------------------------
# Charger le pipeline et la config de married au démarrage de la vue
MARRIED_MODEL_DIR = Path(__file__).resolve().parent.parent / "ml_models" / "married"
married_pipeline = joblib.load(MARRIED_MODEL_DIR / "pipeline.joblib")
married_config = json.loads((MARRIED_MODEL_DIR / "config.json").read_text(encoding="utf-8"))


def married_view(request):
    result = None
    probability = None
    metrics = married_config.get("metrics", {})

    if request.method == "POST":
        form = MarriedForm(request.POST)
        if form.is_valid():
            # Utiliser model_input() pour respecter l'ordre et les noms exacts des colonnes
            input_data = form.model_input()
            data = pd.DataFrame([input_data])

            proba = married_pipeline.predict_proba(data)[0, 1]
            threshold = married_config.get("threshold", 0.5)

            result = 1 if proba >= threshold else 0
            probability = round(proba * 100, 1)
    else:
        form = MarriedForm()

    context = {
        "form": form,
        "result": result,
        "probability": probability,
        "metrics": metrics,
    }
    return render(request, "predictor/married.html", context)


@require_POST
def married_api(request):
    """Reçoit le formulaire (fetch / JSON) et renvoie la prédiction en JSON."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "errors": {"__all__": ["JSON invalide"]}}, status=400)

    form = MarriedForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)

    # Calcul de la prédiction via le pipeline
    input_data = form.model_input()
    data = pd.DataFrame([input_data])

    proba = float(married_pipeline.predict_proba(data)[0, 1])
    threshold = float(married_config.get("threshold", 0.462))
    threshold_pct = round(threshold * 100, 1)
    probability_pct = round(proba * 100, 1)

    return JsonResponse({
        "ok": True,
        "high": proba >= threshold,
        "probability": probability_pct,
        "threshold": threshold_pct,
    })


# ----------------------------------------------------------------------
# JEUNE ACTIF
# ----------------------------------------------------------------------
def jeune_page(request):
    _, config = load("jeune")
    m = config["metrics"]
    # coût par jeune touché : 1/part_de_jeunes au hasard vs 1/précision avec le modèle
    savings = round((1 - m["share_young"] / m["precision"]) * 100)
    return render(request, "predictor/jeune.html",
                  {"form": JeuneForm(), "m": m, "savings": savings,
                   "n_rows": f"{config['n_rows']:,}".replace(",", "\u202f")})


@require_POST
def jeune_api(request):
    """Reçoit le profil client (JSON) et renvoie le segment + les offres à proposer."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "errors": {"__all__": ["JSON invalide"]}}, status=400)
    form = JeuneForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, **predict_jeune(form.model_input())})


# ----------------------------------------------------------------------
# DIPLÔMÉ SOUS-ÉVALUÉ
# ----------------------------------------------------------------------
def sous_evalue_page(request):
    _, config = load_sous_evalue()
    return render(request, "predictor/sous_evalue.html", {
        "form": SousEvalueForm(),
        "config": config,
    })


@require_POST
def sous_evalue_api(request):
    """Reçoit le profil d'un diplômé et renvoie la probabilité qu'il soit sous-évalué."""
    payload, error = _read_payload(request)
    if error:
        return error
    form = SousEvalueForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, **predict_sous_evalue(form.model_input())})


# ----------------------------------------------------------------------
# PROFESSION (occupation)
# ----------------------------------------------------------------------
def occupation_page(request):
    return render(request, "predictor/occupation.html", {"form": OccupationForm()})


@require_POST
def occupation_api(request):
    """Reçoit le formulaire et renvoie la famille professionnelle la plus probable."""
    payload, error = _read_payload(request)
    if error:
        return error
    form = OccupationForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, **predict_occupation(form.model_input())})
# ----------------------------------------------------------------------
# RELATION FAMILIALE (relationship, CatBoost)
# ----------------------------------------------------------------------
def relationship_page(request):
    return render(request, "predictor/relationship.html", {"form": RelationshipForm()})


@require_POST
def relationship_api(request):
    """Reçoit le formulaire (JSON avec tirets) et retourne la relation familiale la plus probable."""
    payload, error = _read_payload(request)
    if error:
        return error

    # Convertir les tirets en underscores (comme le formulaire Django les attend)
    payload_converted = {key.replace("-", "_"): value for key, value in payload.items()}

    form = RelationshipForm(payload_converted)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, **predict_relationship(form.model_input())})