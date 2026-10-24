import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .forms import IncomeForm, JeuneForm
from .ml import load, predict_income, predict_jeune


def home(request):
    _, config = load("income")
    _, jeune = load("jeune")
    return render(request, "predictor/home.html",
                  {"metrics": config["metrics"], "jeune": jeune["metrics"]})


def income_page(request):
    return render(request, "predictor/income.html", {"form": IncomeForm()})


@require_POST
def income_api(request):
    """Reçoit le formulaire (fetch / JSON) et renvoie la prédiction en JSON."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "errors": {"__all__": ["JSON invalide"]}}, status=400)
    form = IncomeForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, **predict_income(form.model_input())})


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
