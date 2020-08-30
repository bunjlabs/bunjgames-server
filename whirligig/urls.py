from django.urls import path

from whirligig import views

urlpatterns = [
    path('create', views.CreateGameAPI.as_view(), name='create_game'),
    path('game', views.GameAPI.as_view(), name='game'),
    path('state/next', views.NextStateAPI.as_view(), name='next_state')
]
