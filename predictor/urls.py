from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required

from .accounts import StyledAuthenticationForm, register

urlpatterns = [
    path("", views.home, name="home"),
    path("prediction-revenu/", views.income_page, name="income"),
    path("api/income/", views.income_api, name="income_api"),
    path("married/", views.married_view, name="married"),
    path("api/married/", views.married_api, name="married_api"),
    path("jeune-actif/", views.jeune_page, name="jeune"),
    path("api/jeune/", views.jeune_api, name="jeune_api"),
    path("diplomes-sous-evalues/", views.sous_evalue_page, name="sous_evalue"),
    path("api/sous-evalue/", views.sous_evalue_api, name="sous_evalue_api"),
    path("temps-de-travail/", views.hours_page, name="hours"),
    path("api/hours/", views.hours_api, name="hours_api"),
    path("prediction-profession/", views.occupation_page, name="occupation"),
    path("api/occupation/", views.occupation_api, name="occupation_api"),
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