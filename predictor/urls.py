from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required

from . import views
from .accounts import StyledAuthenticationForm, register
from .model_auth import model_login, require_model_login
from .occupation_auth import occupation_login, occupation_logout, occupation_register

urlpatterns = [
    path("", views.home, name="home"),

    path("prediction-revenu/", require_model_login("income")(views.income_page), name="income"),
    path("api/income/", require_model_login("income")(views.income_api), name="income_api"),
    path("prediction-revenu/connexion/", model_login("income"), name="income_login"),

    path("married/", require_model_login("married")(views.married_view), name="married"),
    path("api/married/", require_model_login("married")(views.married_api), name="married_api"),
    path("married/connexion/", model_login("married"), name="married_login"),

    path("jeune-actif/", require_model_login("jeune")(views.jeune_page), name="jeune"),
    path("api/jeune/", require_model_login("jeune")(views.jeune_api), name="jeune_api"),
    path("jeune-actif/connexion/", model_login("jeune"), name="jeune_login"),

    path("diplomes-sous-evalues/", require_model_login("sous_evalue")(views.sous_evalue_page), name="sous_evalue"),
    path("api/sous-evalue/", require_model_login("sous_evalue")(views.sous_evalue_api), name="sous_evalue_api"),
    path("diplomes-sous-evalues/connexion/", model_login("sous_evalue"), name="sous_evalue_login"),

    path("prediction-profession/", views.occupation_page, name="occupation"),
    path("prediction-profession/fiche/", views.occupation_sheet, name="occupation_sheet"),
    path("prediction-profession/connexion/", occupation_login, name="occupation_login"),
    path("prediction-profession/inscription/", occupation_register, name="occupation_register"),
    path("prediction-profession/deconnexion/", occupation_logout, name="occupation_logout"),

    path("prediction-relation/", require_model_login("relationship")(views.relationship_page), name="relationship"),
    path("api/relationship/", require_model_login("relationship")(views.relationship_api), name="relationship_api"),
    path("prediction-relation/connexion/", model_login("relationship"), name="relationship_login"),

    path("login/", login_not_required(auth_views.LoginView.as_view(
        template_name="predictor/login.html",
        authentication_form=StyledAuthenticationForm,
        redirect_authenticated_user=True)), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),
]
