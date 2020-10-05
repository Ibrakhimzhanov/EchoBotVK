# !/usr/bin/env python3
import logging
import random

from pony.orm import db_session

import handlers
from models import UserState, Registration

try:
    import settings
except ImportError:
    exit('Do copy setting.py.default settings.py and set token!')

import vk_api  # TODO fix version!
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

log = logging.getLogger("bot")  # TODO добавить код  gitignore


def configure_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)

    file_handler = logging.FileHandler("bot.log", delay=False)
    file_handler.setFormatter(logging.Formatter(
        fmt='%(asctime)s %(levelno)s %(message)s',
        datefmt='%d-%m-%Y,%H:%M'))
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)
    log.setLevel(logging.DEBUG)


class Bot:
    """
    Сценарий регистрации на конференцию "UzwebBlog Conf" через vk.com
    Use python 3.8

    Поддерживает ответы на вопросы про дату, место проведения и сценарий регистрации:
    - спрашиваем имя
    - спрашиваем email
    - говорим об успешной регистрации
    Если шаг не пройдет, задаем уточняющий вопрос пока шаг не будет пройдет.
    """

    def __init__(self, GROUP_ID, TOKEN):
        """
        :param GROUP_ID: group id из группы vk
        :param TOKEN: секретный токен
        """
        self.GROUP_ID = GROUP_ID
        self.TOKEN = TOKEN
        self.vk = vk_api.VkApi(token=TOKEN)
        self.long_poller = VkBotLongPoll(self.vk, self.GROUP_ID)
        self.api = self.vk.get_api()

    def run(self):
        """
        Запускает бота.

        """
        for event in self.long_poller.listen():
            try:
                self.on_event(event)
            except Exception as err:
                log.exception("ошибка в обработке события")

    @db_session
    def on_event(self, event):
        """ Отправляет сообщение назад, если это текст.
        :param event: VkBotMessageEvent object
        :return None
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info("Мы не умеем обрабатывать событие такого типа %s", event.type)
            return

        user_id = event.message.peer_id
        text = event.message.text
        state = UserState.get(user_id=str(user_id))

        if state is not None:
            text_to_send = self.continue_scenario(text, state)
        else:
            # search intent
            for intent in settings.INTENTS:
                log.debug(f'User gets {intent}')
                if any(token in text.lower() for token in intent['tokens']):
                    if intent['answer']:
                        text_to_send = intent['answer']
                    else:
                        text_to_send = self.start_scenario(user_id, intent['scenario'])
                    break
            else:
                text_to_send = settings.DEFAULT_ANSWER

        self.api.messages.send(
            message=text_to_send,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )

    def start_scenario(self, user_id, scenario_name):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        text_to_send = step['text']
        UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step, context={})
        return text_to_send

    def continue_scenario(self, text, state):
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            # next step
            next_step = steps[step['next_step']]
            text_to_send = next_step['text'].format(**state.context)
            if next_step['next_step']:
                # switch to next step
                state.step_name = step['next_step']
            else:
                # finish scenario
                log.info('Зарегистрирован: {name} {email}'.format(**state.context))
                Registration(name=state.context['name'], email=state.context['email'])
                state.delete()
        else:
            # retry current step
            text_to_send = step['failure_text'].format(**state.context)

        return text_to_send


if __name__ == "__main__":
    configure_logging()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()
