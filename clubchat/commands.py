import abc
import datetime

from django.utils import timezone
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater

from clubchat.models import User, Club, GroupMessage, PersonalMessage
from django.conf import settings

from common.utils import BadFormatException


class Commands:
    START = '/start'
    CHANGE_NAME = '/change_name'
    START_PUBLIC_CHAT = '/public_chat'
    START_PRIVATE_CHAT = '/private_chat'
    SETTINGS = '/settings'


class ChatStates:
    DEFAULT = 0
    WAITING_FOR_NAME = 1
    IN_PUBLIC_CHAT = 2
    IN_PRIVATE_CHAT = 3


COMMANDS_LIST = (
    Commands.START, Commands.CHANGE_NAME, Commands.START_PUBLIC_CHAT, Commands.START_PRIVATE_CHAT, Commands.SETTINGS
)


class CommandHandler:
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractmethod
    def get_user(self):
        pass

    @abc.abstractmethod
    def get_user(self):
        pass

    @abc.abstractmethod
    def create_user(self, name, club):
        pass

    @abc.abstractmethod
    def send_message(self, text, buttons=None):
        pass

    def send_message_to_user(self, user, text, buttons=None):
        updater = Updater(token=settings.TELEGRAM_BOT_API_KEY)
        handler = TelegramCommandHandler(user.telegram_chat_id, updater)
        handler.send_message(text, buttons)

    def __generate_main_buttons(self):
        return [
            ("Сменить имя", Commands.CHANGE_NAME),
            ("Написать в общий чат", Commands.START_PUBLIC_CHAT),
            ("Написать в личный чат", Commands.START_PRIVATE_CHAT),
            # ("Настройки", Commands.SETTINGS)
        ]

    def print_no_text_allowed_data(self, user):
        self.send_message(
            'Пожалуйста, выберите один из пунктов меню\nВы в заведении "{}"\nВаше имя - "{}"'.format(
                user.club.name, user.name),
            buttons=self.__generate_main_buttons()
        )

    def process_command_start(self, command):
        if len(command.params) < 1:
            raise BadFormatException('Чтобы начать работу с ботом, пожалуйста, просканируйте QR код заведения')
        club = Club.get_by_invite_token(command.params[0])
        if club is None:
            raise BadFormatException('Указанное заведение не найдено')
        user = self.get_user()
        if user is None:
            user = self.create_user('Гость', club)
        else:
            self.check_user_not_banned_or_rise(user)
            user.last_activity = timezone.now()
            user.club = club
            user.save()
        self.send_message(
            'Вы в заведении "{}"\nВаше имя - "{}"'.format(user.club.name, user.name),
            buttons=self.__generate_main_buttons()
        )

    def process_command_name_sent(self, command):
        if not command.text:
            raise BadFormatException('Имя не может быть пустым')
        user = self.get_user()
        user.name = command.text
        user.state = ChatStates.DEFAULT
        user.save()
        self.send_message(
            'Ваше имя изменено на "{}"'.format(user.name),
            buttons=self.__generate_main_buttons()
        )

    def process_command_change_name(self, command):
        user = self.get_user()
        if len(command.params) > 0 and ' '.join(command.params):
            self.send_message(
                'Ваше имя изменено на "{}"'.format(user.name),
                buttons=self.__generate_main_buttons()
            )
            user.name = ' '.join(command.params)
            user.state = ChatStates.DEFAULT
        else:
            self.send_message(
                'Для смены имени напишите его в чат'
            )
            user.state = ChatStates.WAITING_FOR_NAME
        user.save()

    def check_user_last_activity(self, user):
        if user is None:
            raise BadFormatException('Чтобы начать работу с ботом, пожалуйста, просканируйте QR код заведения')
        if user.last_activity + datetime.timedelta(minutes=user.club.user_logout_minutes) < timezone.now():
            raise BadFormatException(
                'Вы слишком долго отсутствовали в чате. Если вы все еще находитесь в заведении, '
                'пожалуйста, просканируйте QR код заведения еще раз'
            )

    def check_user_not_banned(self, user):
        if user.is_banned or user in user.club.banned_users.all():
            raise BadFormatException('Ваш аккаунт заблокирован в данном заведении')

    def check_public_messages_allowed(self, user):
        if not user.club.is_public_messages_allowed:
            raise BadFormatException('В настоящий момент сообщения в общий чат не принимаются')

    def check_private_messages_allowed(self, user):
        if not user.club.is_private_messages_allowed:
            raise BadFormatException('В настоящий момент сообщения в личные чаты не принимаются')

    def is_public_messages_verified(self, user):
        if user.club.is_public_messages_verification_required:
            return user in user.club.verified_users
        return True

    def process_command_start_public_chat(self, command):
        user = self.get_user()
        self.check_user_not_banned(user)
        self.check_public_messages_allowed(user)
        self.send_message(
            'Теперь вы можете писать сообщения в общий чат.\n'
            'Для других действий используйте меню выше.'
        )
        if not self.is_public_messages_verified(user):
            self.send_message(
                'В данном заведении действует предварительная модерация сообщений.\n'
                'Перед тем как появиться в общем чате, все Ваши сообщения должны быть '
                'верифицированы администрацией заведения.'
            )
        user.state = ChatStates.IN_PUBLIC_CHAT
        user.save()

    def process_command_start_private_chat(self, command):
        cur_user = self.get_user()
        self.check_user_not_banned(cur_user)
        self.check_private_messages_allowed(cur_user)
        if len(command.params) > 0 and command.params[0].isnumeric() \
                and User.get(command.params[0], check_ban=True) is not None:
            user = User.get(command.params[0], check_ban=True)
            try:
                self.check_user_last_activity(user)
            except BadFormatException:
                self.send_message(
                    'К сожалению, данный пользователь покинул чат.'
                )
                return
            self.send_message(
                'Теперь вы можете писать сообщения пользователю {}.\n'
                'Для других действий используйте меню выше.'.format(user.name)
            )
            cur_user.state = ChatStates.IN_PRIVATE_CHAT
            cur_user.private_chat_user = user
            user.save()
        else:
            users = User.get_active_users(cur_user.club).exclude(id=cur_user.id)
            if users.count() == 0:
                self.send_message(
                    'В настоящий момент в заведении отсутствуют активные пользователи.\n'
                    'Вы все еще можете писать сообщения в общий чат.'
                )
                return
            self.send_message(
                'Выберите пользователя',
                buttons=[
                    (user.name, '/{} {}'.format(Commands.START_PRIVATE_CHAT, user.id)) for user in users
                ]
            )

    def process_command_name_send_public_message(self, command):
        user = self.get_user()
        self.check_user_not_banned(user)
        self.check_public_messages_allowed(user)
        GroupMessage.objects.create(
            is_verified=self.is_public_messages_verified(user),
            user=user,
            club=user.club,
            text=command.text
        )

    def process_command_name_send_private_message(self, command):
        user = self.get_user()
        self.check_user_not_banned(user)
        self.check_private_messages_allowed(user)
        if user.private_chat_user is None:
            user.state = ChatStates.DEFAULT
            user.save()
            self.process_command_start_private_chat(command)
            return
        try:
            self.check_user_last_activity(user.private_chat_user)
        except BadFormatException:
            user.state = ChatStates.DEFAULT
            user.save()
            self.send_message(
                'К сожалению, данный пользователь покинул чат.'
            )
            return
        self.send_message_to_user(
            user.private_chat_user,
            command.text,
            buttons=[
                ('Ответить пользователю', '/{} {}'.format(Commands.START_PRIVATE_CHAT, user.private_chat_user.id))
            ]
        )
        PersonalMessage.objects.create(
            sender=user,
            receiver=user.private_chat_use,
            club=user.club,
            text=command.text
        )


class TelegramCommandHandler(CommandHandler):
    chat_id = 0
    tg_updater = None

    def __init__(self, chat_id, tg_updater):
        super().__init__()
        self.chat_id = chat_id
        self.tg_updater = tg_updater

    def get_user(self):
        return User.get_by_telegram_chat_id(self.chat_id)

    def get_user_or_rise(self):
        return User.get_by_telegram_chat_id_or_rise(self.chat_id)

    def create_user(self, name, club):
        return User.objects.create(
                name=name,
                telegram_chat_id=self.chat_id,
                club=club
        )

    def send_message(self, text, buttons=None):
        if buttons is not None:
            inline_keyboard_buttons = [
                InlineKeyboardButton(button_text, callback_data=button_command)
                for button_text, button_command in buttons
            ]
            reply_markup = InlineKeyboardMarkup(TelegramCommandHandler.build_menu(inline_keyboard_buttons, n_cols=1))
            self.tg_updater.bot.send_message(chat_id=self.chat_id, text=text, reply_markup=reply_markup)
        else:
            self.tg_updater.bot.send_message(chat_id=self.chat_id, text=text)

    @staticmethod
    def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        if header_buttons:
            menu.insert(0, header_buttons)
        if footer_buttons:
            menu.append(footer_buttons)
        return menu


class Command:
    text = None
    command = None
    params = []
    is_command = False
    command_handler = None

    def __init__(self, command_text, command_handler):
        self.text = command_text if command_text else ''
        self.command_handler = command_handler
        params = self.text.split(' ')
        self.is_command = len(params) and params[0] in COMMANDS_LIST
        if self.is_command:
            self.command = params[0]
            self.params = params[1:]

    def handle(self):
        print(self.text)
        user = self.command_handler.get_user()
        if not self.is_command or self.command != Commands.START:
            self.command_handler.check_user_last_activity_or_rise(user)
        if self.is_command:
            if self.command == Commands.START:
                self.command_handler.process_command_start(self)
            elif self.command == Commands.CHANGE_NAME:
                self.command_handler.process_command_change_name(self)
            elif self.command == Commands.START_PUBLIC_CHAT:
                self.command_handler.process_command_start_public_chat(self)
            elif self.command == Commands.START_PRIVATE_CHAT:
                self.command_handler.process_command_start_private_chat(self)
            else:
                raise BadFormatException('Unknown bot command')
        else:
            if user.state == ChatStates.DEFAULT:
                self.command_handler.print_no_text_allowed_data(user)
            elif user.state == ChatStates.WAITING_FOR_NAME:
                self.command_handler.process_command_name_sent(self)
            elif user.state == ChatStates.IN_PUBLIC_CHAT:
                self.command_handler.process_command_name_send_public_message(self)
            elif user.state == ChatStates.IN_PRIVATE_CHAT:
                self.command_handler.process_command_name_send_private_message(self)
        user = self.command_handler.get_user()
        if user is not None:
            user.last_activity = timezone.now()
            user.save()
