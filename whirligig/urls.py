from django.urls import path

from whirligig import views

urlpatterns = [
    path('v1/create', views.CreateGameAPI.as_view(), name='create_game'),
]
