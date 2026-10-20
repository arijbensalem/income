from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("prediction-revenu/", views.income_page, name="income"),
    path("api/income/", views.income_api, name="income_api"),
    path("prediction-profession/", views.occupation_page, name="occupation"),
    path("api/occupation/", views.occupation_api, name="occupation_api"),
    path("prediction-relation/", views.relationship_page, name="relationship"),
    path("api/relationship/", views.relationship_api, name="relationship_api"),
]
