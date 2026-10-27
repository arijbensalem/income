from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required

from . import jeune_tools, married_app, views, views_income
from .accounts import StyledAuthenticationForm, register
from .model_auth import model_login, require_model_login
from .occupation_auth import occupation_login, occupation_logout, occupation_register

urlpatterns = [
    path("", views.home, name="home"),

    path("prediction-revenu/", require_model_login("income")(views_income.income_page), name="income"),
    path("api/income/", require_model_login("income")(views_income.income_api), name="income_api"),
    path("ciblage-premium/", require_model_login("income")(views_income.ciblage_page), name="ciblage"),
    path("api/ciblage/", require_model_login("income")(views_income.ciblage_api), name="ciblage_api"),
    path("ciblage-premium/modele.csv", require_model_login("income")(views_income.ciblage_modele), name="ciblage_modele"),
    path("prediction-revenu/connexion/", model_login("income"), name="income_login"),

    path("married/", require_model_login("married")(married_app.married_view), name="married"),
    path("married/api", require_model_login("married")(married_app.married_api), name="married_api"),
    path("married/template", require_model_login("married")(married_app.married_template), name="married_template"),
    path("married/batch", require_model_login("married")(married_app.married_batch), name="married_batch"),
    path("married/connexion/", model_login("married"), name="married_login"),

    path("jeune-actif/", require_model_login("jeune")(views.jeune_page), name="jeune"),
    path("api/jeune/", require_model_login("jeune")(views.jeune_api), name="jeune_api"),
    path("api/jeune/explain/", require_model_login("jeune")(jeune_tools.explain_api), name="jeune_explain_api"),
    path("jeune-actif/connexion/", model_login("jeune"), name="jeune_login"),

    path("diplomes-sous-evalues/", require_model_login("sous_evalue")(views.sous_evalue_page), name="sous_evalue"),
    path("api/sous-evalue/", require_model_login("sous_evalue")(views.sous_evalue_api), name="sous_evalue_api"),
    path("diplomes-sous-evalues/connexion/", model_login("sous_evalue"), name="sous_evalue_login"),

    path("prediction-profession/", views.occupation_page, name="occupation"),
    path("prediction-profession/fiche/", views.occupation_sheet, name="occupation_sheet"),
    path("prediction-profession/connexion/", occupation_login, name="occupation_login"),
    path("prediction-profession/inscription/", occupation_register, name="occupation_register"),
    path("prediction-profession/deconnexion/", occupation_logout, name="occupation_logout"),

    path("prediction-relation/", views.relationship_page, name="relationship"),
    path("relation-familiale/login/", views.relationship_login, name="relationship_login"),
    path("relation-familiale/register/", views.relationship_register, name="relationship_register"),
    path("relation-familiale/logout/", views.relationship_logout, name="relationship_logout"),
    path("api/relationship/", views.relationship_api, name="relationship_api"),
    path("api/relationship/history/", views.relationship_history_api, name="relationship_history_api"),
    path("api/relationship/analytics/", views.relationship_analytics_api, name="relationship_analytics_api"),
    path("api/relationship/batch/", views.relationship_batch_api, name="relationship_batch_api"),
    path("api/relationship/pdf/", views.relationship_pdf_api, name="relationship_pdf_api"),

    path("login/", login_not_required(auth_views.LoginView.as_view(
        template_name="predictor/login.html",
        authentication_form=StyledAuthenticationForm,
        redirect_authenticated_user=True)), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),
]
