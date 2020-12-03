from django.urls import path

from common import api

urlpatterns = [
    path('v1/time', api.TimeAPI.as_view()),
]
