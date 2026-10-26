import json

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .career_routes import (
    FAMILY_ORDER,
    GOAL_LABELS,
    GOALS,
    INTEREST_LABELS,
    INTERESTS,
    build_direction,
    parse_goal,
    parse_interests,
    score_families,
)
from .forms import EDUCATION, OccupationForm
from .ml import predict_occupation
from .occupation_auth import occupation_account_required
from .transformers import LABELS_FR

PATH_KEY = "occupation_pathway"
MODEL_FEATURES = [
    "age",
    "workclass",
    "education-num",
    "marital-status",
    "relationship",
    "race",
    "sex",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
    "native-country",
    "income",
]
EDUCATION_LABELS = dict(EDUCATION)
FAMILY_NOTE = (
    "Ces trois libellés regroupent les intitulés du recensement pour ce site. "
    "Ce ne sont pas des catégories officielles. La vente recensée (Sales) est "
    "rangée avec les métiers de bureau."
)
SHEET_MISSING = (
    "Aucune recommandation n'est disponible. Remplissez le formulaire sur "
    "« Trouver mon parcours », puis consultez à nouveau cette fiche."
)
NOTE_MAX = 280


def service_recall_text():
    path = settings.BASE_DIR / "ml_models" / "occupation" / "holdout_evaluation_report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    recall = next(item["recall"] for item in report["per_class"] if item["label"] == "Service")
    return f"{float(recall) * 100:.1f}".replace(".", ",")


def _fr_number(value):
    return f"{float(value):.1f}".replace(".", ",")


def _ordered(result):
    found = {item["label"]: item for item in result["classes"]}
    rows = []
    for label in FAMILY_ORDER:
        probability = round(float(found[label]["probability"]), 1)
        rows.append({
            "label": label,
            "label_fr": LABELS_FR[label],
            "probability": probability,
            "text": _fr_number(probability),
        })
    return rows


def _display(form, name):
    value = form.cleaned_data[name]
    choices = getattr(form.fields[name], "choices", None)
    if choices:
        return dict(choices).get(value, value)
    return value


def profile_rows(form):
    rows = []
    for name in form.fields:
        rows.append({
            "name": name,
            "label": str(form.fields[name].label),
            "display": str(_display(form, name)),
            "model_value": str(form.cleaned_data[name]),
        })
    return rows


def parse_note(raw):
    text = (raw or "").strip()
    if len(text) > NOTE_MAX:
        return None, f"Le texte libre doit faire au plus {NOTE_MAX} caractères."
    return text, None


def build_recommendation(form, goal, interests, note):
    model_input = form.model_input()
    if set(model_input) != set(MODEL_FEATURES):
        raise ValueError("Le profil transmis au modèle est incomplet.")
    education_num = int(model_input["education-num"])
    shortlist_labels = score_families(goal, interests, education_num)
    prediction = predict_occupation(model_input)
    evidence = _ordered(prediction)
    by_label = {row["label"]: row for row in evidence}
    directions = [
        build_direction(
            family,
            goal,
            interests,
            education_num,
            by_label[family]["probability"],
        )
        for family in shortlist_labels
    ]
    return {
        "goal": goal,
        "goal_label": GOAL_LABELS[goal],
        "interests": interests,
        "interest_labels": [INTEREST_LABELS[tag] for tag in interests],
        "note": note,
        "profile": profile_rows(form),
        "education_num": education_num,
        "education_label": EDUCATION_LABELS[education_num],
        "income_code": str(model_input["income"]),
        "income_label": str(_display(form, "income")),
        "directions": directions,
        "evidence": evidence,
        "model_top": LABELS_FR[prediction["label"]],
        "model_top_probability": by_label[prediction["label"]]["text"],
        "service_recall": service_recall_text(),
        "family_note": FAMILY_NOTE,
    }


def pathway_is_valid(data):
    if not isinstance(data, dict):
        return False
    goal = data.get("goal")
    if goal not in GOAL_LABELS or data.get("goal_label") != GOAL_LABELS[goal]:
        return False
    interests = data.get("interests")
    if not isinstance(interests, list) or not interests:
        return False
    if any(tag not in INTEREST_LABELS for tag in interests):
        return False
    if data.get("interest_labels") != [INTEREST_LABELS[tag] for tag in interests]:
        return False
    if not isinstance(data.get("note"), str) or len(data["note"]) > NOTE_MAX:
        return False
    try:
        education_num = int(data["education_num"])
    except (KeyError, TypeError, ValueError):
        return False
    if education_num not in EDUCATION_LABELS:
        return False
    if data.get("education_label") != EDUCATION_LABELS[education_num]:
        return False
    profile = data.get("profile")
    if not isinstance(profile, list) or len(profile) != 12:
        return False
    for row in profile:
        if not isinstance(row, dict):
            return False
        if not all(isinstance(row.get(key), str) and row.get(key) for key in ("label", "display", "model_value")):
            return False
    if not isinstance(data.get("income_code"), str) or not data.get("income_label"):
        return False
    evidence = data.get("evidence")
    if not isinstance(evidence, list) or [row.get("label") for row in evidence] != FAMILY_ORDER:
        return False
    for row in evidence:
        if row.get("label_fr") != LABELS_FR[row["label"]]:
            return False
        try:
            probability = float(row["probability"])
        except (KeyError, TypeError, ValueError):
            return False
        if not 0 <= probability <= 100:
            return False
    directions = data.get("directions")
    if not isinstance(directions, list) or not 1 <= len(directions) <= 3:
        return False
    for direction in directions:
        if direction.get("label") not in FAMILY_ORDER:
            return False
        if direction.get("label_fr") != LABELS_FR[direction["label"]]:
            return False
        if not isinstance(direction.get("why"), str) or not direction["why"]:
            return False
        if not isinstance(direction.get("examples"), list) or not direction["examples"]:
            return False
        if not isinstance(direction.get("training"), list) or not direction["training"]:
            return False
        if not isinstance(direction.get("next_steps"), list) or not direction["next_steps"]:
            return False
    if data.get("service_recall") != service_recall_text():
        return False
    if data.get("family_note") != FAMILY_NOTE:
        return False
    return True


@occupation_account_required
@require_http_methods(["GET", "POST"])
def occupation_page(request):
    form = OccupationForm(request.POST or None)
    goal_raw = request.POST.get("goal", "") if request.method == "POST" else ""
    interest_raw = request.POST.getlist("interests") if request.method == "POST" else []
    note_raw = request.POST.get("note", "") if request.method == "POST" else ""
    goal_error = None
    interest_error = None
    note_error = None
    pathway = None
    if request.method == "POST" and form.is_valid():
        goal, goal_error = parse_goal(goal_raw)
        interests, interest_error = parse_interests(interest_raw)
        note, note_error = parse_note(note_raw)
        if goal_error is None and interest_error is None and note_error is None:
            pathway = build_recommendation(form, goal, interests, note)
            request.session[PATH_KEY] = pathway
            request.session.modified = True
    return render(request, "predictor/occupation.html", {
        "form": form,
        "page": "explorer",
        "goals": GOALS,
        "interests": INTERESTS,
        "selected_goal": goal_raw,
        "selected_interests": interest_raw,
        "note": note_raw,
        "goal_error": goal_error,
        "interest_error": interest_error,
        "note_error": note_error,
        "pathway": pathway,
        "service_recall": service_recall_text(),
        "family_note": FAMILY_NOTE,
        "occupation_account": request.occupation_account,
    })


@occupation_account_required
@require_http_methods(["GET"])
def occupation_sheet(request):
    pathway = request.session.get(PATH_KEY)
    if not pathway_is_valid(pathway):
        request.session.pop(PATH_KEY, None)
        messages.error(request, SHEET_MISSING)
        return redirect("occupation")
    return render(request, "predictor/occupation_sheet.html", {
        "page": "fiche",
        "pathway": pathway,
        "occupation_account": request.occupation_account,
    })
