from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class Club(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    invite_token = models.CharField(max_length=255)
    user_logout_minutes = models.IntegerField(default=60)
    is_public_messages_verification_required = models.BooleanField(default=False)
    is_public_messages_allowed = models.BooleanField(default=True)
    is_private_messages_allowed = models.BooleanField(default=True)

    @staticmethod
    def get_by_invite_token(invite_token):
        try:
            return Club.objects.get(invite_token=invite_token)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def get_by_email_password(email, password):
        try:
            return Club.objects.get(email=email, password=password)
        except ObjectDoesNotExist:
            return None


class ClubSession(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=255)
    expired = models.DateTimeField(default=None, null=True)

    @staticmethod
    def get_club_by_token(token):
        try:
            return ClubSession.objects.get(token=token).club
        except ObjectDoesNotExist:
            return None


class User(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now_add=True)
    is_banned = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    telegram_chat_id = models.IntegerField(default=0)
    state = models.IntegerField(default=0)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='users')
    private_chat_user = models.ForeignKey('User', null=True, blank=True, on_delete=models.CASCADE, related_name='+')
    banned_clubs = models.ManyToManyField(Club, related_name='banned_users')
    verified_clubs = models.ManyToManyField(Club, related_name='verified_users')

    @staticmethod
    def get(id, check_ban=False):
        try:
            user = User.objects.get(id=id)
            if check_ban and user.is_banned:
                return None
            return user
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def get_or_rise(id, check_ban=False):
        user = User.get(id, check_ban)
        if user is None:
            raise AppException(BAD_OBJECT_ID, params=('User', id))
        return user

    @staticmethod
    def get_by_telegram_chat_id(telegram_chat_id, check_ban=False):
        try:
            user = User.objects.get(telegram_chat_id=telegram_chat_id)
            if check_ban and user.is_banned:
                return None
            return user
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def get_by_telegram_chat_id_or_rise(telegram_chat_id, check_ban=False):
        user = User.get_by_telegram_chat_id(telegram_chat_id, check_ban)
        if user is None:
            raise AppException(AUTHORISATION_REQUIRED)
        return user

    @staticmethod
    def get_active_users(club):
        return User.objects.filter(
            club=club,
            is_banned=False,
        ).exclude(
            banned_clubs=club
        )


class GroupMessage(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    is_verified = models.BooleanField()
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, related_name='group_messages')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='group_messages')
    text = models.TextField()


class PersonalMessage(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    sender = models.ForeignKey(User, null=True, on_delete=models.CASCADE, related_name='+')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='private_messages')
    text = models.TextField()
