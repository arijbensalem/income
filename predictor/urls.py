from django.urls import path
from . import views, views_income
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required

from .accounts import StyledAuthenticationForm, register

urlpatterns = [
    path("", views.home, name="home"),
    path("prediction-revenu/", views_income.income_page, name="income"),
    path("api/income/", views_income.income_api, name="income_api"),
    path("ciblage-premium/", views_income.ciblage_page, name="ciblage"),
    path("api/ciblage/", views_income.ciblage_api, name="ciblage_api"),
    path("ciblage-premium/modele.csv", views_income.ciblage_modele, name="ciblage_modele"),
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
    path("api/relationship/", views.relationship_api, name="relationship_api"),
        path("login/", login_not_required(auth_views.LoginView.as_view(
        template_name="predictor/login.html",
        authentication_form=StyledAuthenticationForm,
        redirect_authenticated_user=True)), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),
]