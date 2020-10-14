from django.urls import path

from jeopardy import views

urlpatterns = [
    path('v1/create', views.CreateGameAPI.as_view()),
    path('v1/players/register', views.RegisterPlayerAPI.as_view()),
]
