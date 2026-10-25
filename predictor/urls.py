from django.urls import path

from . import views

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
]