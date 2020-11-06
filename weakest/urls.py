from django.urls import path

from weakest import api

urlpatterns = [
    path('v1/create', api.CreateGameAPI.as_view()),
    path('v1/players/register', api.RegisterPlayerAPI.as_view()),
]