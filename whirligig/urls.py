from django.urls import path

from whirligig import views

urlpatterns = [
    path('v1/create', views.CreateGameAPI.as_view(), name='create_game'),
    path('v1/game', views.GameAPI.as_view(), name='game'),
    path('v1/state/next', views.NextStateAPI.as_view(), name='next_state'),
    path('v1/score', views.ChangeScoreAPI.as_view(), name='score')
]
