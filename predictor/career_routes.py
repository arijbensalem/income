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
            "Cette famille regroupe l'administration, l'encadrement, "
            "l'expertise et la vente recensée."
        ),
        "next_steps": [
            "Choisir un métier d'exemple, puis vérifier le diplôme demandé auprès d'une source locale.",
            "Comparer une formation courte et une poursuite d'études plus longue.",
            "En parler avec une personne du métier ou un conseiller d'orientation.",
        ],
    },
    "Blue-collar": {
        "why": (
            "Cette famille regroupe la réparation, la production, "
            "le transport et l'agriculture."
        ),
        "next_steps": [
            "Choisir un métier d'exemple, puis chercher la filière ou l'apprentissage qui y mène.",
            "Vérifier les conditions d'entrée auprès d'un organisme local, sans les supposer ici.",
            "Tester un atelier ou un stage court avant un cursus long.",
        ],
    },
    "Service": {
        "why": (
            "Cette famille regroupe l'accueil, l'aide à la personne, "
            "l'emploi de maison et la protection. Le modèle historique la reconnaît mal."
        ),
        "next_steps": [
            "Choisir un seul métier d'exemple avant de chercher une formation.",
            "Vérifier les conditions d'accès locales. Ce site ne les garantit pas.",
            "Croiser cette piste avec une source locale : le modèle reconnaît mal les services.",
        ],
    },
}

INTEREST_TITLES = {
    "office": ["Adm-clerical"],
    "management": ["Exec-managerial", "Prof-specialty"],
    "tech_support": ["Tech-support"],
    "sales": ["Sales"],
    "craft": ["Craft-repair"],
    "machines": ["Machine-op-inspct"],
    "outdoor": ["Transport-moving", "Farming-fishing"],
    "care": ["Other-service", "Priv-house-serv"],
    "security": ["Protective-serv"],
}

INTEREST_STEPS = {
    "office": [
        "Comparer secrétariat, gestion administrative et comptabilité de base, puis vérifier le diplôme demandé localement.",
        "Mettre en regard une formation courte en bureautique et un cursus plus long.",
    ],
    "management": [
        "Repérer un rôle d'encadrement compatible avec votre niveau indiqué, et les compléments à investiguer.",
        "Parler à une personne qui encadre une équipe pour comparer le métier réel et l'intitulé.",
    ],
    "tech_support": [
        "Chercher une formation au dépannage et à l'assistance utilisateur, plutôt qu'un diplôme général d'informatique.",
        "Vous entraîner à expliquer un problème technique, étape par étape, à une personne non spécialiste.",
        "Vérifier localement les prérequis d'un certificat court de support, sans supposer qu'il est obligatoire.",
    ],
    "sales": [
        "Comparer la vente en magasin et un rôle commercial de bureau : les horaires et les diplômes diffèrent.",
        "Vérifier s'il existe une formation courte à la vente près de chez vous. Ce site ne cite ni école ni employeur.",
    ],
    "craft": [
        "Partir d'un métier de réparation ou de fabrication dans les exemples, puis chercher l'apprentissage correspondant.",
        "Vérifier les conditions d'un stage ou d'un atelier d'essai avant un cursus long.",
    ],
    "machines": [
        "Repérer une formation à la conduite de machines ou à la production, avec les règles de sécurité du poste.",
        "Vérifier les conditions d'accès locales (âge, aptitude, stage) auprès d'un organisme. Elles ne sont pas listées ici.",
    ],
    "outdoor": [
        "Distinguer transport et agriculture : les permis, les saisons et les lieux ne sont pas les mêmes.",
        "Vérifier les titres demandés localement avant de vous engager.",
    ],
    "care": [
        "Choisir un cadre parmi l'accueil, l'aide à domicile et la restauration, puis la formation courte qui va avec.",
        "Vérifier les règles d'hygiène et les prérequis de ce cadre auprès d'une source locale.",
    ],
    "security": [
        "Chercher les formations et habilitations locales liées à la sécurité et à la protection.",
        "Vérifier les conditions d'accès (âge, aptitudes, procédure) auprès d'un organisme local. Ce site ne les garantit pas.",
        "Ne pas confondre un poste d'accueil et un métier de protection : les exigences diffèrent.",
    ],
}

INTEREST_SKILLS = {
    "office": [
        "Organisation de documents et écriture claire.",
        "Usage courant d'un tableur et d'un traitement de texte.",
    ],
    "management": [
        "Répartition du travail dans une petite équipe.",
        "Suivi d'un planning et explication d'une consigne.",
    ],
    "tech_support": [
        "Dépannage pas à pas et reformulation d'un problème technique.",
        "Bases de bureautique et d'assistance à un utilisateur.",
    ],
    "sales": [
        "Présentation d'un produit et écoute d'un besoin.",
        "Tenue d'un échange simple avec un client.",
    ],
    "craft": [
        "Geste de réparation ou de fabrication, à pratiquer en atelier.",
        "Lecture d'un plan ou d'une notice simple.",
    ],
    "machines": [
        "Conduite ou surveillance d'une machine, avec les règles de sécurité du poste.",
        "Repérage d'un défaut simple sur une chaîne ou un engin.",
    ],
    "outdoor": [
        "Repérage d'un itinéraire ou d'une parcelle, et travail en extérieur.",
        "Entretien de base d'un outil ou d'un véhicule.",
    ],
    "care": [
        "Accueil d'une personne et explication d'une consigne simple.",
        "Gestes d'hygiène et d'aide du quotidien, à vérifier selon le métier visé.",
    ],
    "security": [
        "Application d'une consigne de sécurité et d'un contrôle d'accès.",
        "Repérage des formations et habilitations demandées localement pour la protection.",
    ],
}


def _family_study_line(family, level):
    if level <= 8:
        lines = {
            "White-collar": "Côté bureau, une formation courte en bureautique ou secrétariat se vérifie avant un long cursus.",
            "Blue-collar": "Côté technique, un apprentissage ou une formation professionnelle est la piste à comparer en premier.",
            "Service": "Côté services, une formation courte d'accueil, d'aide ou de restauration se vérifie selon le métier, pas en bloc.",
        }
    elif level <= 10:
        lines = {
            "White-collar": "Côté bureau, comparez un bac professionnel, une formation administrative et une passerelle vers un diplôme de technicien.",
            "Blue-collar": "Côté technique, comparez un bac professionnel, un apprentissage et les conditions de stage locales.",
            "Service": "Côté services, comparez un diplôme professionnel et une formation courte avant de vous engager.",
        }
    elif level <= 12:
        lines = {
            "White-collar": "Avec un diplôme court déjà indiqué, comparez une spécialisation (bureautique, comptabilité, support) et une poursuite vers une licence.",
            "Blue-collar": "Avec un diplôme court déjà indiqué, comparez une certification de maintenance, de conduite ou de qualité et un métier voisin.",
            "Service": "Avec un diplôme court déjà indiqué, comparez une spécialisation (accueil, aide, sécurité, hôtellerie) reconnue localement.",
        }
    elif level == 13:
        lines = {
            "White-collar": "Après une licence, la piste bureau à vérifier est une spécialisation (gestion, droit appliqué, informatique de gestion) ou un master, pas un nouveau premier cycle.",
            "Blue-collar": "Après une licence, la piste technique à vérifier est la supervision ou la maintenance avancée, pas un diplôme de base.",
            "Service": "Après une licence, la piste services à vérifier est un rôle de coordination, pas un nouveau diplôme d'accueil.",
        }
    elif level == 14:
        lines = {
            "White-collar": "Avec un master indiqué, cherchez une certification de métier ou une spécialisation ciblée plutôt qu'un autre diplôme général.",
            "Blue-collar": "Avec un master indiqué, vérifiez une passerelle vers la supervision technique ou la qualité, sans repartir d'un cursus initial.",
            "Service": "Avec un master indiqué, vérifiez un rôle d'organisation dans les services plutôt qu'une formation d'exécution.",
        }
    elif level == 15:
        lines = {
            "White-collar": "Avec une école professionnelle indiquée, comparez une certification complémentaire et une évolution de rôle. Aucun concours n'est supposé ici.",
            "Blue-collar": "Avec une école professionnelle indiquée, comparez une certification de pratique et un rôle de supervision. Aucun ordre professionnel n'est supposé ici.",
            "Service": "Avec une école professionnelle indiquée, comparez une habilitation de pratique et un rôle de coordination. Aucun concours n'est supposé ici.",
        }
    else:
        lines = {
            "White-collar": "Avec un doctorat indiqué, la question utile est le type de rôle visé (expertise, enseignement, gestion), pas un nouveau diplôme de base.",
            "Blue-collar": "Avec un doctorat indiqué, la question utile est le lien avec un métier technique (méthode, qualité, supervision), pas un diplôme de départ.",
            "Service": "Avec un doctorat indiqué, la question utile est le cadre d'application, pas une formation d'accueil de premier niveau.",
        }
    return lines[family]


def _training_for(family, education_num, goal, education_label, age):
    level = int(education_num)
    age = int(age)
    items = [
        f"Niveau indiqué : {education_label}.",
        _family_study_line(family, level),
    ]
    if age < 20 and level <= 9:
        items.append(
            "Vous indiquez moins de 20 ans et un niveau de fin de scolarité ou en dessous : "
            "comparez une poursuite d'études et une formation professionnelle. "
            "L'âge ne dit pas si une place est disponible."
        )
    elif age >= 40 and goal == "studies":
        items.append(
            "Vous indiquez 40 ans ou plus et un projet d'études : comparez un cursus long "
            "et une formation plus courte. L'âge ne dit pas le temps dont vous disposez."
        )
    if goal == "work":
        items.append(
            "Pour un objectif d'emploi, privilégiez les formations courtes et les stages à vérifier localement. "
            "Ce site ne liste pas d'employeurs."
        )
    elif goal == "change":
        items.append(
            "Pour une reconversion, listez ce que vous voulez garder (organisation, technique, contact) "
            "et ce qu'il resterait à compléter. Ce texte ne connaît pas votre expérience."
        )
    elif goal == "studies":
        items.append(
            "Pour des études, choisissez ensuite un diplôme précis reconnu dans votre pays. "
            "Ce site ne prescrit pas d'établissement."
        )
    return items


def example_titles(family):
    return [
        TITLE_FR[title]
        for title, group in COLLAR_GROUPS.items()
        if group == family
    ]


def _matched_tags(family, interests):
    return [tag for tag in interests if tag in FAMILY_INTERESTS[family]]


def examples_for(family, interests, role):
    if role != "primary":
        return example_titles(family)
    ordered = []
    for tag in _matched_tags(family, interests):
        for title in INTEREST_TITLES.get(tag, []):
            if COLLAR_GROUPS.get(title) != family:
                continue
            label = TITLE_FR[title]
            if label not in ordered:
                ordered.append(label)
    return ordered or example_titles(family)


def steps_for(family, interests, role):
    if role == "primary":
        steps = []
        for tag in _matched_tags(family, interests):
            for step in INTEREST_STEPS.get(tag, []):
                if step not in steps:
                    steps.append(step)
        if steps:
            return steps
    return list(FAMILY_DETAILS[family]["next_steps"])


def skills_for(family, interests, role):
    if role != "primary":
        return []
    lines = []
    for tag in _matched_tags(family, interests):
        for line in INTEREST_SKILLS.get(tag, []):
            if line not in lines:
                lines.append(line)
    return lines


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


def _goal_points(goal, education_num):
    points = {label: 0.0 for label in FAMILY_ORDER}
    level = int(education_num)
    if goal == "studies":
        points["White-collar"] += 1.0
        if level <= 10:
            points["Blue-collar"] += 0.5
            points["Service"] += 0.5
    elif goal == "work":
        points["Blue-collar"] += 1.0
        points["Service"] += 1.0
        if level <= 8:
            points["Blue-collar"] += 0.5
    return points


def rank_families(goal, interests, education_num):
    """Rank families from interests first. Goal points never invent a primary card."""
    interest_points = {label: 0.0 for label in FAMILY_ORDER}
    for interest in interests:
        for family in INTEREST_TO_FAMILIES.get(interest, []):
            interest_points[family] += 2.0
    goal_points = _goal_points(goal, education_num)
    primary = [label for label in FAMILY_ORDER if interest_points[label] > 0]
    primary.sort(key=lambda label: (
        -(interest_points[label] + goal_points[label]),
        FAMILY_ORDER.index(label),
    ))
    secondary = [
        label for label in FAMILY_ORDER
        if interest_points[label] == 0 and goal_points[label] > 0
    ]
    secondary.sort(key=lambda label: (-goal_points[label], FAMILY_ORDER.index(label)))
    rows = [
        {
            "label": label,
            "role": "primary",
            "interest_points": interest_points[label],
            "goal_points": goal_points[label],
        }
        for label in primary
    ]
    for label in secondary:
        if len(rows) >= 3:
            break
        rows.append({
            "label": label,
            "role": "secondary",
            "interest_points": 0.0,
            "goal_points": goal_points[label],
        })
    if rows:
        return rows[:3]
    return [
        {
            "label": label,
            "role": "secondary",
            "interest_points": 0.0,
            "goal_points": 0.0,
        }
        for label in FAMILY_ORDER[:2]
    ]


def score_families(goal, interests, education_num):
    return [row["label"] for row in rank_families(goal, interests, education_num)]


def _why(family, goal, rank, matched_labels):
    goal_label = GOAL_LABELS[goal]
    description = FAMILY_DETAILS[family]["why"]
    if rank["role"] == "primary":
        parts = [
            "Cette direction suit vos centres d'intérêt : " + ", ".join(matched_labels) + "."
        ]
        if rank["goal_points"] > 0:
            parts.append(
                f"L'objectif « {goal_label} » renforce cette piste. "
                "Il ne remplace pas les intérêts cochés."
            )
        parts.append(description)
        return " ".join(parts)
    return " ".join([
        "Piste secondaire : aucun centre d'intérêt coché ne correspond à cette famille.",
        f"Elle est seulement ouverte par l'objectif « {goal_label} ».",
        "Elle n'a pas le même rang que les pistes portées par vos intérêts.",
        description,
    ])


def build_direction(family, goal, interests, education_num, education_label, age, rank):
    matched = [INTEREST_LABELS[tag] for tag in _matched_tags(family, interests)]
    role = rank["role"]
    return {
        "label": family,
        "label_fr": LABELS_FR[family],
        "role": role,
        "role_label": "Direction recommandée" if role == "primary" else "Piste secondaire",
        "why": _why(family, goal, rank, matched),
        "examples": examples_for(family, interests, role),
        "training": _training_for(family, education_num, goal, education_label, age),
        "next_steps": steps_for(family, interests, role),
        "skills": skills_for(family, interests, role),
        "matched_interests": matched,
        "interest_points": float(rank["interest_points"]),
        "goal_points": float(rank["goal_points"]),
    }
