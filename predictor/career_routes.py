from .transformers import COLLAR_GROUPS, LABELS_FR

FAMILY_ORDER = ["White-collar", "Blue-collar", "Service"]

GOALS = [
    ("studies", "Poursuivre des études"),
    ("work", "Chercher un emploi ou une formation professionnelle"),
    ("change", "Changer de voie professionnelle"),
]
GOAL_LABELS = dict(GOALS)

INTERESTS = [
    ("office", "Bureau, organisation, écriture"),
    ("management", "Encadrement, responsabilité d'équipe"),
    ("tech_support", "Informatique, support technique"),
    ("sales", "Commerce et vente"),
    ("craft", "Travail manuel, réparation, fabrication"),
    ("machines", "Machines, production, conduite"),
    ("outdoor", "Agriculture, extérieur, transport"),
    ("care", "Accueil, aide aux personnes, services"),
    ("security", "Sécurité et protection"),
]
INTEREST_LABELS = dict(INTERESTS)

TITLE_FR = {
    "Prof-specialty": "Profession spécialisée",
    "Exec-managerial": "Encadrement / gestion",
    "Tech-support": "Support technique",
    "Adm-clerical": "Administration / secrétariat",
    "Sales": "Vente",
    "Craft-repair": "Artisanat et réparation",
    "Machine-op-inspct": "Conduite de machines",
    "Transport-moving": "Transport et manutention",
    "Handlers-cleaners": "Manutention et nettoyage",
    "Farming-fishing": "Agriculture et pêche",
    "Other-service": "Services divers (restauration, accueil…)",
    "Priv-house-serv": "Emploi de maison",
    "Protective-serv": "Services de protection",
}

INTEREST_TO_FAMILIES = {
    "office": ["White-collar"],
    "management": ["White-collar"],
    "tech_support": ["White-collar"],
    "sales": ["White-collar", "Service"],
    "craft": ["Blue-collar"],
    "machines": ["Blue-collar"],
    "outdoor": ["Blue-collar"],
    "care": ["Service"],
    "security": ["Service"],
}

FAMILY_INTERESTS = {
    "White-collar": {"office", "management", "tech_support", "sales"},
    "Blue-collar": {"craft", "machines", "outdoor"},
    "Service": {"care", "security", "sales"},
}

FAMILY_DETAILS = {
    "White-collar": {
        "why": (
            "Cette direction regroupe l'administration, l'encadrement, "
            "l'expertise et la vente recensée. Elle mérite d'être explorée "
            "si vous visez des études ou un travail de bureau."
        ),
        "next_steps": [
            "Lister 2 ou 3 métiers d'exemple ci-dessous et vérifier les diplômes demandés localement.",
            "Comparer une formation courte et une poursuite d'études plus longue.",
            "Parler à une personne déjà dans ce type de poste ou à un conseiller d'orientation.",
        ],
    },
    "Blue-collar": {
        "why": (
            "Cette direction regroupe les métiers techniques et manuels : "
            "réparation, production, transport, agriculture. Elle est utile "
            "si vous préférez un apprentissage concret ou une insertion plus directe."
        ),
        "next_steps": [
            "Repérer une filière professionnelle ou un apprentissage lié à un titre d'exemple.",
            "Vérifier les conditions d'entrée (âge, niveau, stages) auprès d'un organisme local.",
            "Tester une immersion courte ou un atelier avant de vous engager longtemps.",
        ],
    },
    "Service": {
        "why": (
            "Cette direction regroupe l'accueil, l'aide à la personne, "
            "l'emploi de maison et la protection. Explorez-la avec prudence : "
            "le modèle historique la reconnaît mal."
        ),
        "next_steps": [
            "Clarifier si vous visez l'accueil, le soin, la restauration ou la sécurité.",
            "Chercher une formation courte ou une certification reconnue localement.",
            "Vérifier les conditions de travail et les exigences d'accès avant de vous engager.",
        ],
    },
}


def _education_band(level):
    level = int(level)
    if level <= 8:
        return "early"
    if level <= 10:
        return "secondary"
    if level <= 12:
        return "vocational"
    return "higher"


def _training_for(family, education_num, goal):
    band = _education_band(education_num)
    routes = {
        "White-collar": {
            "early": [
                "Reprendre un socle scolaire (lecture, écriture, calcul) avant une filière administrative.",
                "Envisager une formation professionnelle courte en bureautique ou secrétariat.",
            ],
            "secondary": [
                "Explorer un bac professionnel ou une formation administrative.",
                "Vérifier les passerelles vers un BTS / diplôme technique de bureau.",
            ],
            "vocational": [
                "Comparer un diplôme professionnel court et une poursuite vers une licence appliquée.",
                "Investiguer des certifications en bureautique, comptabilité de base ou support utilisateur.",
            ],
            "higher": [
                "Affiner une spécialisation (gestion, droit appliqué, informatique de gestion…).",
                "Investiguer un master professionnel ou une certification sectorielle, selon le métier visé.",
            ],
        },
        "Blue-collar": {
            "early": [
                "Prioriser une formation professionnelle ou un apprentissage plutôt qu'un long cursus théorique.",
                "Investiguer les titres liés à la réparation, la production ou le transport.",
            ],
            "secondary": [
                "Explorer un CAP / bac pro / apprentissage dans un métier technique.",
                "Vérifier les stages en entreprise et les conditions d'accès locales.",
            ],
            "vocational": [
                "Consolider une spécialité technique déjà entamée, ou pivoter vers un métier voisin.",
                "Investiguer une certification de conduite d'engins, de maintenance ou de qualité.",
            ],
            "higher": [
                "Relier un diplôme supérieur à un métier technique (supervision, maintenance avancée).",
                "Investiguer des formations continues plutôt qu'un nouveau long cursus si vous travaillez déjà.",
            ],
        },
        "Service": {
            "early": [
                "Chercher une formation courte d'accueil, d'aide à la personne ou de restauration.",
                "Vérifier les prérequis de sécurité ou d'hygiène selon le métier.",
            ],
            "secondary": [
                "Explorer un diplôme professionnel de service ou une formation d'aide à domicile.",
                "Comparer emploi direct et formation courte avant de vous engager.",
            ],
            "vocational": [
                "Investiguer une spécialisation (petite enfance, sécurité, hôtellerie…).",
                "Vérifier les certifications reconnues localement pour l'emploi visé.",
            ],
            "higher": [
                "Relier un niveau d'études élevé à un rôle de coordination dans les services.",
                "Investiguer des formations continues plutôt qu'un nouveau diplôme long si l'objectif est l'emploi.",
            ],
        },
    }
    items = list(routes[family][band])
    if goal == "work":
        items.append(
            "Si vous voulez travailler rapidement, privilégiez les formations courtes et les stages, "
            "puis vérifiez les offres locales — ce site ne liste pas d'employeurs."
        )
    elif goal == "change":
        items.append(
            "Pour une reconversion, identifiez ce que vous gardez de votre expérience "
            "(organisation, technique, contact) et ce qu'il faut compléter."
        )
    elif goal == "studies":
        items.append(
            "Pour les études, choisissez d'abord une direction familiale, puis un diplôme précis "
            "reconnu dans votre pays — ce site ne prescrit pas d'établissement."
        )
    return items


def example_titles(family):
    return [
        TITLE_FR[title]
        for title, group in COLLAR_GROUPS.items()
        if group == family
    ]


def parse_goal(raw):
    if raw in GOAL_LABELS:
        return raw, None
    return None, "Choisissez un objectif."


def parse_interests(raw_list):
    if not raw_list:
        return None, "Choisissez au moins un centre d'intérêt."
    values = []
    for item in raw_list:
        if item not in INTEREST_LABELS:
            return None, "Un centre d'intérêt n'est pas reconnu."
        if item not in values:
            values.append(item)
    return values, None


def score_families(goal, interests, education_num):
    scores = {label: 0.0 for label in FAMILY_ORDER}
    for interest in interests:
        for family in INTEREST_TO_FAMILIES.get(interest, []):
            scores[family] += 2.0
    if goal == "studies":
        scores["White-collar"] += 1.0
        if int(education_num) <= 10:
            scores["Blue-collar"] += 0.5
            scores["Service"] += 0.5
    elif goal == "work":
        scores["Blue-collar"] += 1.0
        scores["Service"] += 1.0
        if int(education_num) <= 8:
            scores["Blue-collar"] += 0.5
    elif goal == "change":
        for family in FAMILY_ORDER:
            scores[family] += 0.5
    ranked = sorted(FAMILY_ORDER, key=lambda label: (-scores[label], FAMILY_ORDER.index(label)))
    return [label for label in ranked if scores[label] > 0][:3] or ranked[:2]


def build_direction(family, goal, interests, education_num, model_probability):
    matched = [
        INTEREST_LABELS[tag]
        for tag in interests
        if tag in FAMILY_INTERESTS[family]
    ]
    probability = round(float(model_probability), 1)
    probability_text = f"{probability:.1f}".replace(".", ",")
    why_parts = [FAMILY_DETAILS[family]["why"]]
    if matched:
        why_parts.append(
            "Vos centres d'intérêt retenus pour cette piste : " + ", ".join(matched) + "."
        )
    why_parts.append(
        f"Pour votre profil, le modèle historique estime environ "
        f"{probability_text} % pour « {LABELS_FR[family]} ». "
        "Ce chiffre est un indice issu d'un recensement ancien, pas une recommandation à lui seul."
    )
    return {
        "label": family,
        "label_fr": LABELS_FR[family],
        "why": " ".join(why_parts),
        "examples": example_titles(family),
        "training": _training_for(family, education_num, goal),
        "next_steps": list(FAMILY_DETAILS[family]["next_steps"]),
        "model_probability": probability,
        "model_probability_text": probability_text,
        "matched_interests": matched,
    }
