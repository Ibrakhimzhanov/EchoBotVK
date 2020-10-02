# !/usr/bin/env python3

import logging
import random

try:
    import settings
except ImportError:
    exit('Do copy setting.py.default settings.py and set token!')


import vk_api #TODO fix version!
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

log = logging.getLogger("bot") #TODO добавить код  gitignore


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
    Echo bot для vk.com

    Use python 3.8
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

    def on_event(self, event):
        """ Отправляет сообщение назад, если это текст.
        :param event: TODO
        :return None
        """
        if event.type == VkBotEventType.MESSAGE_NEW:
            log.debug("Отправляем сообщнеие назад")
            self.api.messages.send(
                message='Я тебя понял, ты спрашивал у меня: {}?'.format(event.message.text),
                random_id=random.randint(0, 2 ** 20),
                peer_id=event.message.peer_id,
            )
        else:
            log.info("Мы не умеем обрабатывать событие такого типа %s", event.type)


if __name__ == "__main__":
    configure_logging()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()
