"""Page « Statut marital » : analyse d'un profil, explication du résultat
et analyse d'un fichier clients (CSV).

Ce module est autonome : il ne modifie ni views.py ni ml.py (il utilise seulement
ml.load("married") pour charger le pipeline et sa configuration).
"""
import csv
import io
import json

import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .forms import MarriedForm
from .ml import load

# Colonnes attendues par le pipeline (mêmes noms que MarriedForm.model_input)
MODEL_COLUMNS = ["age", "workclass", "education-num", "occupation", "race", "sex",
                 "capital-gain", "capital-loss", "hours-per-week", "native-country", "income"]
NUMERIC = ["age", "education-num", "capital-gain", "capital-loss", "hours-per-week"]
CATEGORICAL = ["workclass", "occupation", "race", "sex", "native-country", "income"]

MAX_UPLOAD_BYTES = 2 * 1024 * 1024      # 2 Mo
MAX_ROWS = 5000

# (colonne, libellé affiché, variable sensible ?)
FACTORS = [
    ("age", "Âge", False),
    ("education-num", "Niveau d'études", False),
    ("hours-per-week", "Heures de travail", False),
    ("income", "Revenu annuel", False),
    ("occupation", "Profession", False),
    ("workclass", "Secteur d'emploi", False),
    ("capital-gain", "Gains en capital", False),
    ("capital-loss", "Pertes en capital", False),
    ("sex", "Sexe", True),
    ("race", "Origine", True),
    ("native-country", "Pays d'origine", True),
]

VERDICTS = {
    ("likely", "élevée"): ("Profil très probablement marié(e)",
                           "Plusieurs éléments du profil vont dans le même sens : l'estimation est solide."),
    ("likely", "moyenne"): ("Profil probablement marié(e)",
                            "Le profil ressemble davantage à celui de personnes mariées."),
    ("likely", "faible"): ("Plutôt marié(e), à confirmer",
                           "L'estimation est proche de la limite : mieux vaut la confirmer lors d'un échange."),
    ("unlikely", "élevée"): ("Profil très probablement non marié(e)",
                             "Plusieurs éléments du profil vont dans le même sens : l'estimation est solide."),
    ("unlikely", "moyenne"): ("Profil probablement non marié(e)",
                              "Le profil ressemble davantage à celui de personnes célibataires, divorcées ou veuves."),
    ("unlikely", "faible"): ("Plutôt non marié(e), à confirmer",
                             "L'estimation est proche de la limite : mieux vaut la confirmer lors d'un échange."),
}

RECOMMENDATIONS = {
    "banque": {
        "likely": [
            "Proposer un rendez-vous « projet de foyer » : crédit immobilier à deux, compte joint.",
            "Présenter une assurance habitation et une prévoyance famille.",
            "Parler d'épargne pour les enfants ou les études.",
        ],
        "unlikely": [
            "Proposer une offre « premier logement » ou un prêt personnel adapté à une seule personne.",
            "Présenter une assurance individuelle et un plan d'épargne souple.",
            "Offrir un bilan budgétaire personnalisé.",
        ],
        "uncertain": [
            "Ne pas présumer de la situation : poser la question lors du prochain contact.",
            "Présenter d'abord les offres communes à tous les profils (épargne, assurance de base).",
        ],
    },
    "association": {
        "likely": [
            "Informer sur les activités et ateliers pour familles (parentalité, loisirs).",
            "Présenter les aides au logement et à la garde d'enfants.",
            "Proposer un accompagnement de la vie de famille (budget, scolarité).",
        ],
        "unlikely": [
            "Proposer des groupes d'entraide et des activités de rencontre.",
            "Orienter vers la formation, l'insertion et les solutions de logement partagé.",
            "Présenter les aides individuelles disponibles.",
        ],
        "uncertain": [
            "Ne pas présumer de la situation : échanger d'abord avec la personne.",
            "Présenter l'ensemble des services de l'association.",
        ],
    },
}


# ----------------------------------------------------------------------
# Outils internes
# ----------------------------------------------------------------------
def _model():
    return load("married")          # (pipeline, config), mis en cache par ml.load


def _frame(rows, config):
    df = pd.DataFrame(rows)
    cols = config.get("features")
    if cols and all(c in df.columns for c in cols):
        df = df[cols]
    return df


def _proba(rows):
    pipeline, config = _model()
    return pipeline.predict_proba(_frame(rows, config))[:, 1]


def _threshold(config):
    return float(config.get("threshold", 0.5))


def _fmt_pct(x):
    """Formate une métrique (fraction 0-1 ou pourcentage) en texte « 81,6 »."""
    if not isinstance(x, (int, float)):
        return None
    v = x * 100 if x <= 1 else x
    return f"{v:.1f}".replace(".", ",")


def _fmt_auc(x):
    """Formate un AUC en texte « 0,89 »."""
    if not isinstance(x, (int, float)):
        return None
    return f"{x:.2f}".replace(".", ",")


def _confidence(p, thr):
    gap = abs(p - thr)
    return "élevée" if gap >= 0.25 else "moyenne" if gap >= 0.10 else "faible"


def _reference_values(config):
    """Valeurs de référence (profil « moyen ») pour mesurer l'influence de chaque variable."""
    options = config.get("options", {})
    return {
        "age": [25, 33, 41, 49, 57],
        "education-num": [9, 10, 13],
        "hours-per-week": [35, 40, 45],
        "capital-gain": [0],
        "capital-loss": [0],
        "income": ["<=50K"],
        "workclass": ["Private"],
        "race": ["White"],
        "native-country": ["United-States"],
        "sex": options.get("sex") or ["Male", "Female"],
        "occupation": options.get("occupation") or [],
    }


def _display_values(form):
    """Texte lisible de chaque valeur saisie (pour afficher « Âge : 45 ans »)."""
    d = form.cleaned_data

    def choice(field, value):
        return dict(form.fields[field].choices).get(value, str(value))

    return {
        "age": f"{d['age']} ans",
        "education-num": choice("education_num", d["education_num"]),
        "hours-per-week": f"{d['hours_per_week']} h par semaine",
        "income": choice("income", d["income"]),
        "occupation": choice("occupation", d["occupation"]),
        "workclass": choice("workclass", d["workclass"]),
        "capital-gain": f"{d['capital_gain']:,} $".replace(",", "\u202f"),
        "capital-loss": f"{d['capital_loss']:,} $".replace(",", "\u202f"),
        "sex": choice("sex", d["sex"]),
        "race": choice("race", d["race"]),
        "native-country": choice("native_country", d["native_country"]),
    }


def _influences(profile, p, display):
    """Influence de chaque variable : probabilité du profil moins probabilité moyenne
    si cette variable avait une valeur de référence (en points de pourcentage)."""
    _, config = _model()
    refs = _reference_values(config)
    rows, owners = [], []
    for key, _label, _sensitive in FACTORS:
        for value in refs.get(key) or []:
            rows.append({**profile, key: value})
            owners.append(key)
    if not rows:
        return []
    probs = _proba(rows)
    sums, counts = {}, {}
    for key, prob in zip(owners, probs):
        sums[key] = sums.get(key, 0.0) + float(prob)
        counts[key] = counts.get(key, 0) + 1

    out = []
    for key, label, sensitive in FACTORS:
        if key not in sums:
            continue
        points = (p - sums[key] / counts[key]) * 100
        out.append({
            "key": key,
            "label": label,
            "value": display.get(key, ""),
            "points": round(points, 1),
            "sensitive": sensitive,
        })
    out.sort(key=lambda item: abs(item["points"]), reverse=True)
    return out[:7]


def _age_curve(profile):
    ages = list(range(18, 81, 2))
    probs = _proba([{**profile, "age": a} for a in ages])
    return {"ages": ages, "probabilities": [round(float(x) * 100, 1) for x in probs]}


def _error(message, status=400):
    return JsonResponse({"ok": False, "errors": {"__all__": [{"message": message}]}}, status=status)


# ----------------------------------------------------------------------
# Vues
# ----------------------------------------------------------------------
def married_view(request):
    _, config = _model()
    metrics = config.get("metrics") or {}
    accuracy = metrics.get("accuracy")
    reliability = None
    if isinstance(accuracy, (int, float)):
        acc = accuracy / 100 if accuracy > 1 else accuracy
        reliability = round(acc * 10)          # « 8 profils sur 10 »
    stats = {
        "model": config.get("model"),
        "accuracy": _fmt_pct(metrics.get("accuracy")),
        "precision": _fmt_pct(metrics.get("precision")),
        "recall": _fmt_pct(metrics.get("recall")),
        "f1": _fmt_pct(metrics.get("f1")),
        "auc": _fmt_auc(metrics.get("auc")),
        "train_rows": config.get("train_rows"),
        "test_rows": config.get("test_rows"),
        "threshold": round(_threshold(config) * 100),
    }
    return render(request, "predictor/married.html", {
        "form": MarriedForm(),
        "reliability": reliability,
        "stats": stats,
        "required_columns": MODEL_COLUMNS,
        "max_rows": MAX_ROWS,
    })


@require_POST
def married_api(request):
    """Analyse d'un profil : probabilité, verdict, explication, courbe selon l'âge, actions."""
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return _error("JSON invalide")
    if not isinstance(payload, dict):
        return _error("JSON invalide")

    form = MarriedForm(payload)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)

    _, config = _model()
    thr = _threshold(config)
    profile = form.model_input()
    p = float(_proba([profile])[0])
    likely = p >= thr
    confidence = _confidence(p, thr)
    kind = "likely" if likely else "unlikely"
    title, text = VERDICTS[(kind, confidence)]
    bucket = "uncertain" if confidence == "faible" else kind
    display = _display_values(form)

    return JsonResponse({
        "ok": True,
        "probability": round(p * 100, 1),
        "threshold": round(thr * 100, 1),
        "married": likely,
        "high": likely,                      # compatibilité avec l'ancienne API
        "confidence": confidence,
        "title": title,
        "text": text,
        "influences": _influences(profile, p, display),
        "age_curve": _age_curve(profile),
        "age": profile["age"],
        "profile_label": f"{display['age']} · {display['occupation']}",
        "recommendations": {aud: RECOMMENDATIONS[aud][bucket] for aud in RECOMMENDATIONS},
    })


@require_GET
def married_template(request):
    """Fichier modèle à remplir pour l'analyse de fichier."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["client_id"] + MODEL_COLUMNS)
    writer.writerow(["C001", 24, "Private", 10, "Adm-clerical", "White", "Female", 0, 0, 30, "United-States", "<=50K"])
    writer.writerow(["C002", 45, "Private", 13, "Exec-managerial", "White", "Male", 5000, 0, 48, "United-States", ">50K"])
    writer.writerow(["C003", 38, "Private", 9, "Craft-repair", "White", "Male", 0, 0, 40, "United-States", "<=50K"])
    response = HttpResponse("\ufeff" + buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="modele_clients.csv"'
    return response


def _read_upload(upload):
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            upload.seek(0)
            return pd.read_csv(upload, sep=None, engine="python", encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("encodage illisible")


@require_POST
def married_batch(request):
    """Analyse d'un fichier clients : un score par ligne + synthèse pour les graphiques."""
    upload = request.FILES.get("file")
    if upload is None:
        return _error("Aucun fichier reçu.")
    if upload.size > MAX_UPLOAD_BYTES:
        return _error("Fichier trop volumineux (2 Mo maximum).")
    try:
        raw = _read_upload(upload)
    except Exception:
        return _error("Fichier illisible : utilisez un CSV (séparateur « , » ou « ; »).")
    if raw.empty:
        return _error("Le fichier ne contient aucune ligne.")

    raw.columns = [str(c).strip().lower().replace("_", "-").replace(" ", "-") for c in raw.columns]
    missing = [c for c in MODEL_COLUMNS if c not in raw.columns]
    if missing:
        return _error("Colonnes manquantes : " + ", ".join(missing) + ".")

    n_read = len(raw)
    truncated = n_read > MAX_ROWS
    raw = raw.head(MAX_ROWS).copy()

    work = raw[MODEL_COLUMNS].copy()
    for col in NUMERIC:
        work[col] = pd.to_numeric(work[col], errors="coerce")
    for col in CATEGORICAL:
        work[col] = work[col].astype("string").str.strip()
    valid = work.notna().all(axis=1)

    # Valeurs de catégories inconnues du modèle
    _, config = _model()
    options = dict(config.get("options") or {})
    options.setdefault("income", ["<=50K", ">50K"])
    unknown = {}
    for col in CATEGORICAL:
        if col in options:
            bad = valid & ~work[col].isin(options[col])
            if bad.any():
                unknown[col] = sorted(set(work.loc[bad, col].astype(str)))[:3]
                valid &= ~bad

    n_scored = int(valid.sum())
    if n_scored == 0:
        detail = ""
        if unknown:
            detail = " Valeurs inconnues : " + "; ".join(f"{c} = {', '.join(v)}" for c, v in unknown.items()) + "."
        return _error("Aucune ligne exploitable." + detail)

    rows = work[valid].astype(object).to_dict(orient="records")
    probs = _proba(rows)
    thr = _threshold(config)
    likely = probs >= thr

    scored = raw[valid].copy()
    scored["probabilite_marie_%"] = [round(float(x) * 100, 1) for x in probs]
    scored["profil_estime"] = ["Probablement marié(e)" if x else "Probablement non marié(e)" for x in likely]
    scored["confiance"] = [_confidence(float(x), thr) for x in probs]

    # Histogramme des probabilités (10 classes de 10 points)
    hist = [0] * 10
    for x in probs:
        hist[min(int(float(x) * 10), 9)] += 1

    # Part de profils « probablement mariés » par tranche d'âge
    ages = work.loc[valid, "age"].astype(float).reset_index(drop=True)
    bands = pd.cut(ages, bins=[0, 24, 34, 44, 54, 64, 200],
                   labels=["< 25 ans", "25-34", "35-44", "45-54", "55-64", "65 +"])
    frame = pd.DataFrame({"band": bands, "likely": [bool(x) for x in likely]})
    by_age = []
    for label, group in frame.groupby("band", observed=True):
        by_age.append({"label": str(label), "count": int(len(group)),
                       "share": round(float(group["likely"].mean()) * 100, 1)})

    preview = []
    for pos in range(min(25, n_scored)):
        row = scored.iloc[pos]
        preview.append({
            "row": int(scored.index[pos]) + 2,        # numéro de ligne dans le fichier (en-tête = 1)
            "age": int(float(row["age"])),
            "occupation": str(row["occupation"]),
            "probability": float(row["probabilite_marie_%"]),
            "likely": bool(likely[pos]),
        })

    out = io.StringIO()
    scored.to_csv(out, index=False, sep=";", decimal=",")

    return JsonResponse({
        "ok": True,
        "n_read": n_read,
        "n_scored": n_scored,
        "n_skipped": int(len(raw) - n_scored),
        "truncated": truncated,
        "max_rows": MAX_ROWS,
        "unknown": unknown,
        "n_likely": int(likely.sum()),
        "threshold": round(thr * 100, 1),
        "share_likely": round(float(likely.mean()) * 100, 1),
        "mean_probability": round(float(probs.mean()) * 100, 1),
        "histogram": hist,
        "by_age": by_age,
        "preview": preview,
        "csv": out.getvalue(),
    })
