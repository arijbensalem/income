import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
import pandas as pd

from .forms import IncomeForm, OccupationForm, RelationshipForm
from .ml import load, load_occupation, predict_income, predict_occupation, load_relationship, predict_relationship


def home(request):
    _, config = load()
    _, occupation = load_occupation()
    return render(request, "predictor/home.html", {
        "metrics": config["metrics"],
        "occupation": occupation,
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


def relationship_page(request):
    return render(request, "predictor/relationship.html", {"form": RelationshipForm()})


@require_POST
def relationship_api(request):
    """Reçoit le formulaire (JSON avec tirets) et retourne la relation familiale la plus probable."""
    payload, error = _read_payload(request)
    if error:
        return error
    
    # Convertir les tirets en underscores (comme le formulaire Django les attend)
    payload_converted = {}
    for key, value in payload.items():
        new_key = key.replace('-', '_')
        payload_converted[new_key] = value
    
    form = RelationshipForm(payload_converted)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, **predict_relationship(form.model_input())})
