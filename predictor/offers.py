"""Offres proposées selon le segment prédit (démo commerciale banque / assurance).

Le modèle sert UNIQUEMENT à choisir quelle offre marketing montrer.
Il ne décide jamais d'accorder ou de refuser un crédit, un contrat ou un prix.
"""

OFFERS = {
    "jeune": {
        "segment": "Jeune actif (moins de 30 ans)",
        "pitch": "Profil typique d'un jeune actif : c'est le moment de le conquérir, "
                 "avant qu'il ne choisisse une autre banque ou un autre assureur.",
        "bank": [
            ("Compte Jeune Actif", "0 frais de tenue de compte pendant 2 ans."),
            ("Carte + appli mobile", "Paiement et suivi du budget depuis le téléphone."),
            ("Épargne automatique", "Chaque achat arrondi, la différence est épargnée."),
        ],
        "insurance": [
            ("Assurance 1er logement", "Habitation simple et pas chère pour un studio ou une colocation."),
            ("Santé Jeune Actif", "Complémentaire santé à petit prix, résiliable à tout moment."),
        ],
    },
    "confirme": {
        "segment": "Actif confirmé (30 ans et plus)",
        "pitch": "Profil d'actif installé : les besoins portent sur la famille, "
                 "le patrimoine et la préparation de l'avenir.",
        "bank": [
            ("Épargne long terme", "Placements pour un projet ou les études des enfants."),
            ("Conseil projet immobilier", "Rendez-vous avec un conseiller pour un achat."),
        ],
        "insurance": [
            ("Prévoyance famille", "Protège les proches en cas d'accident ou d'invalidité."),
            ("Assurance vie / retraite", "Préparer sa retraite avec un capital qui grandit."),
        ],
    },
}
