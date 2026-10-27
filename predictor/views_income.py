"""Vues du module « Ciblage premium » (cible income). Protégées par la connexion, comme le reste du site."""
import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from . import income_pro as pro_mod
from .income_pro import BatchError, IncomeProForm
from .offers_income import TIERS


def _context():
    _, pro, _ = pro_mod.load_pro()
    return pro


def income_page(request):
    pro = _context()
    return render(request, "predictor/income.html", {
        "form": IncomeProForm(), "pro": pro,
        "tiers": {k: {"label": TIERS[k]["label"], **pro["tiers"][k]} for k in TIERS},
        "top20": pro["gain"][20],
    })


@require_POST
def income_api(request):
    """Reçoit le profil (JSON) et renvoie score, segment, offres, explication et leviers."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "errors": {"__all__": [{"message": "JSON invalide"}]}}, status=400)
    form = IncomeProForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)
    return JsonResponse({"ok": True, **pro_mod.predict_pro(form.model_input())})


def ciblage_page(request):
    pro = _context()
    return render(request, "predictor/ciblage.html", {
        "pro": pro, "features": pro["features"],
        "gain_json": json.dumps(pro["gain"]),
        "tiers_json": json.dumps({k: pro["tiers"][k] for k in pro["tiers"]}),
        "tiers": {k: {"label": TIERS[k]["label"], **pro["tiers"][k]} for k in TIERS},
        "top20": pro["gain"][20],
        "max_rows": pro_mod.MAX_ROWS,
    })


@require_POST
def ciblage_api(request):
    """Reçoit un fichier CSV de clients. ?format=csv renvoie le classement complet en téléchargement."""
    upload = request.FILES.get("file")
    if upload is None:
        return JsonResponse({"ok": False, "error": "Aucun fichier reçu."}, status=400)
    try:
        data, ids, notes, n_total = pro_mod.read_portfolio(upload.read(pro_mod.MAX_BYTES + 1))
    except BatchError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    proba = pro_mod.score_portfolio(data)
    if request.GET.get("format") == "csv":
        response = HttpResponse(pro_mod.portfolio_csv(data, proba, ids), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="classement_clients.csv"'
        return response
    return JsonResponse({"ok": True, **pro_mod.summarize(proba, ids, n_total, notes)})


@require_GET
def ciblage_modele(request):
    response = HttpResponse(pro_mod.template_csv(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="modele_clients.csv"'
    return response
