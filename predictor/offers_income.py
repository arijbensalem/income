"""Offres proposées selon le segment de revenu prédit (démo commerciale banque / assurance).

Le modèle sert UNIQUEMENT à prioriser des actions commerciales (quel client contacter,
quelle offre présenter). Il ne décide jamais d'accorder ou de refuser un crédit,
un contrat ou un prix.
"""

TIERS = {
    "premium": {
        "label": "Premium",
        "segment": "Client à fort potentiel : revenu élevé probable",
        "action": "Priorité 1 : appel d'un conseiller dédié sous 7 jours",
        "pitch": "Client à forte capacité d'épargne et d'investissement : c'est lui qui rapporte le "
                 "plus. Un contact personnalisé vaut mieux qu'un envoi de masse.",
        "bank": [
            ("Gestion privée / conseil patrimonial", "Rendez-vous avec un conseiller pour structurer son épargne."),
            ("Carte haut de gamme", "Plafonds élevés, assurances voyage, services de conciergerie."),
            ("Placements long terme", "Assurance-vie, plans de retraite, investissement diversifié."),
        ],
        "insurance": [
            ("Prévoyance renforcée", "Protège le niveau de vie de la famille en cas d'invalidité ou de décès."),
            ("Assurance habitation et auto premium", "Garanties étendues pour des biens de valeur."),
        ],
    },
    "potentiel": {
        "label": "Potentiel",
        "segment": "Client à potentiel d'évolution : proche du profil premium",
        "action": "Priorité 2 : campagne e-mail / SMS ciblée, puis relance conseiller",
        "pitch": "Profil proche du seuil : bon candidat pour une offre de montée en gamme "
                 "qui l'accompagne avant qu'il ne parte à la concurrence.",
        "bank": [
            ("Carte Gold", "Étape intermédiaire vers l'offre premium, sans frais la 1re année."),
            ("Épargne programmée", "Versement mensuel automatique, modulable à tout moment."),
        ],
        "insurance": [
            ("Pack habitation + santé", "Deux contrats, une seule cotisation réduite."),
            ("Assurance emprunteur", "À proposer au moment d'un projet immobilier."),
        ],
    },
    "standard": {
        "label": "Standard",
        "segment": "Client standard : revenu élevé peu probable",
        "action": "Priorité 3 : communication automatisée à faible coût (appli, e-mail)",
        "pitch": "Pas de campagne coûteuse : on privilégie des offres simples et "
                 "des canaux numériques pour garder un coût d'acquisition bas.",
        "bank": [
            ("Compte essentiel + appli mobile", "Frais réduits, suivi du budget depuis le téléphone."),
            ("Micro-épargne", "Épargner dès quelques unités par mois, sans minimum."),
        ],
        "insurance": [
            ("Assurance de base", "Couverture essentielle à tarif maîtrisé, résiliable à tout moment."),
        ],
    },
}
