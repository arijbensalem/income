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
    rank_families,
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
NOTE_NOTICE = (
    "Cette note est conservée pour vous. Elle n'a pas été utilisée pour classer "
    "les pistes ni pour rédiger les recommandations."
)
RANKING_NOTE = (
    "L'ordre des recommandations suit vos centres d'intérêt, puis votre objectif. "
    "Les probabilités du modèle ne changent pas cet ordre."
)


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


def _skill_lines(directions):
    lines = []
    for direction in directions:
        for line in direction["skills"]:
            if line not in lines:
                lines.append(line)
    return lines


def _disagreement(prediction_label, first_label, by_label):
    if prediction_label == first_label:
        return ""
    return (
        f"Le modèle historique place « {LABELS_FR[prediction_label]} » en tête "
        f"({by_label[prediction_label]['text']} %). "
        "Ce n'est pas l'ordre des pistes : celui-ci suit vos centres d'intérêt et votre objectif."
    )


def build_recommendation(form, goal, interests, note):
    model_input = form.model_input()
    if set(model_input) != set(MODEL_FEATURES):
        raise ValueError("Le profil transmis au modèle est incomplet.")
    education_num = int(model_input["education-num"])
    age = int(model_input["age"])
    education_label = EDUCATION_LABELS[education_num]
    ranked = rank_families(goal, interests, education_num)
    prediction = predict_occupation(model_input)
    evidence = _ordered(prediction)
    by_label = {row["label"]: row for row in evidence}
    directions = [
        build_direction(
            item["label"],
            goal,
            interests,
            education_num,
            education_label,
            age,
            item,
        )
        for item in ranked
    ]
    return {
        "goal": goal,
        "goal_label": GOAL_LABELS[goal],
        "interests": interests,
        "interest_labels": [INTEREST_LABELS[tag] for tag in interests],
        "note": note,
        "note_notice": NOTE_NOTICE,
        "ranking_note": RANKING_NOTE,
        "profile": profile_rows(form),
        "age": age,
        "education_num": education_num,
        "education_label": education_label,
        "income_code": str(model_input["income"]),
        "income_label": str(_display(form, "income")),
        "directions": directions,
        "skill_lines": _skill_lines(directions),
        "evidence": evidence,
        "model_top_label": prediction["label"],
        "model_top": LABELS_FR[prediction["label"]],
        "model_top_probability": by_label[prediction["label"]]["text"],
        "disagreement": _disagreement(prediction["label"], directions[0]["label"], by_label),
        "service_recall": service_recall_text(),
        "family_note": FAMILY_NOTE,
    }


def _points_ok(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return value >= 0


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
    if data.get("note_notice") != NOTE_NOTICE or data.get("ranking_note") != RANKING_NOTE:
        return False
    if not isinstance(data.get("disagreement"), str):
        return False
    try:
        age = int(data["age"])
    except (KeyError, TypeError, ValueError):
        return False
    if not 17 <= age <= 90:
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
    if not isinstance(profile, list) or len(profile) != 10:
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
    skill_lines = data.get("skill_lines")
    if not isinstance(skill_lines, list) or any(not isinstance(line, str) or not line for line in skill_lines):
        return False
    if data.get("model_top_label") not in FAMILY_ORDER:
        return False
    if data.get("model_top") != LABELS_FR[data["model_top_label"]]:
        return False
    directions = data.get("directions")
    if not isinstance(directions, list) or not 1 <= len(directions) <= 3:
        return False
    seen_secondary = False
    for direction in directions:
        if direction.get("label") not in FAMILY_ORDER:
            return False
        if direction.get("label_fr") != LABELS_FR[direction["label"]]:
            return False
        role = direction.get("role")
        if role not in ("primary", "secondary"):
            return False
        if role == "secondary":
            seen_secondary = True
        elif seen_secondary:
            return False
        if direction.get("role_label") not in ("Direction recommandée", "Piste secondaire"):
            return False
        if not isinstance(direction.get("why"), str) or not direction["why"]:
            return False
        if not isinstance(direction.get("examples"), list) or not direction["examples"]:
            return False
        if not isinstance(direction.get("training"), list) or not direction["training"]:
            return False
        if not isinstance(direction.get("next_steps"), list) or not direction["next_steps"]:
            return False
        skills = direction.get("skills")
        if not isinstance(skills, list) or any(not isinstance(line, str) or not line for line in skills):
            return False
        if not isinstance(direction.get("matched_interests"), list):
            return False
        if not _points_ok(direction.get("interest_points")) or not _points_ok(direction.get("goal_points")):
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
