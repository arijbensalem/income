import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .forms import IncomeForm
from .ml import load, predict_income


def home(request):
    _, config = load()
    return render(request, "predictor/home.html", {"metrics": config["metrics"]})


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
