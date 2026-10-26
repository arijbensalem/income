from django.contrib.auth.decorators import login_not_required, login_required
from django.contrib.auth.views import LoginView

from .accounts import StyledAuthenticationForm

MODEL_LOGIN_PAGES = {
    "income": {
        "area_label": "Revenu",
        "area_title": "prédiction de revenu",
        "area_lead": (
            "Cette page est réservée aux comptes connectés. "
            "Utilisez la connexion dédiée au modèle revenu."
        ),
    },
    "married": {
        "area_label": "Statut marital",
        "area_title": "statut marital",
        "area_lead": (
            "Cette page est réservée aux comptes connectés. "
            "Utilisez la connexion dédiée au modèle statut marital."
        ),
    },
    "jeune": {
        "area_label": "Jeune actif",
        "area_title": "jeune actif",
        "area_lead": (
            "Cette page est réservée aux comptes connectés. "
            "Utilisez la connexion dédiée au modèle jeune actif."
        ),
    },
    "sous_evalue": {
        "area_label": "Diplômé sous-évalué",
        "area_title": "diplômé sous-évalué",
        "area_lead": (
            "Cette page est réservée aux comptes connectés. "
            "Utilisez la connexion dédiée au modèle diplômé sous-évalué."
        ),
    },
    "hours": {
        "area_label": "Temps de travail",
        "area_title": "temps de travail",
        "area_lead": (
            "Cette page est réservée aux comptes connectés. "
            "Utilisez la connexion dédiée au modèle temps de travail."
        ),
    },
    "relationship": {
        "area_label": "Relation familiale",
        "area_title": "relation familiale",
        "area_lead": (
            "Cette page est réservée aux comptes connectés. "
            "Utilisez la connexion dédiée au modèle relation familiale."
        ),
    },
}


class ModelLoginView(LoginView):
    template_name = "predictor/model_login.html"
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True
    area_key = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(MODEL_LOGIN_PAGES[self.area_key])
        return context


def model_login(area_key):
    view = type(
        f"{area_key.title().replace('_', '')}LoginView",
        (ModelLoginView,),
        {"area_key": area_key},
    )
    return login_not_required(view.as_view())


def require_model_login(area_key):
    login_name = f"{area_key}_login"

    def apply(view):
        return login_required(view, login_url=login_name)

    return apply
