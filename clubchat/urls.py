from django.urls import path

from clubchat import api

urlpatterns = [
    path('clubchat/telegram/<str:token>', api.on_telegram_message_callback),
]
