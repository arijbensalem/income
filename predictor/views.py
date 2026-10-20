import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .forms import HoursForm, IncomeForm, SousEvalueForm
from .ml import (load, load_hours, load_sous_evalue, predict_hours, predict_income,
                 predict_sous_evalue)


def home(request):
    _, config = load()
    _, sous_evalue = load_sous_evalue()
    _, hours = load_hours()
    return render(request, "predictor/home.html", {
        "metrics": config["metrics"],
        "sous_evalue": sous_evalue,
        "hours": hours,
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


def hours_page(request):
    _, config = load_hours()
    classes = [{"label": c, "label_fr": config["labels_fr"][c],
                "share": round(config["distribution"][c] * 100)} for c in config["classes"]]
    return render(request, "predictor/hours.html", {
        "form": HoursForm(), "config": config, "classes": classes,
    })


@require_POST
def hours_api(request):
    """Reçoit le profil et renvoie la classe de temps de travail la plus probable."""
    payload, error = _read_payload(request)
    if error:
        return error
    form = HoursForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, **predict_hours(form.model_input())})
