from django.urls import path

from whirligig import api

urlpatterns = [
    path('v1/create', api.CreateGameAPI.as_view(), name='create_game'),
]
