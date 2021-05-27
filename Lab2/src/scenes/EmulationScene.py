from .BaseScene import BaseScene
from src import constants, User, Message
from PyInquirer import ValidationError, Validator
from random import random
import math
import time
import multiprocessing
import lorem

USERS = ['Joey', 'Rachel', 'Monica', 'Chandler', 'Phoebe', 'Ross', 'JD', 'Turk', 'Cox', 'Elliot', 'Kelso', 'Janitor']


class NumberValidator(Validator):
    def validate(self, document):
        if not document.text or float(document.text) <= 0:
            raise ValidationError(
                message='Value must be positive number',
                cursor_position=len(document.text))  # Move cursor to end


class EmulationScene(BaseScene):
    def __init__(self, session, redis):
        super().__init__([
            {
                'type': 'input',
                'name': 'count',
                'message': 'Enter a count of users?',
                'validate': NumberValidator,
            },
            {
                'type': 'input',
                'name': 'delay',
                'message': 'Enter a delay between actions (in secs)?',
                'validate': NumberValidator,
            },
        ])
        self.redis = redis
        self.chat = session['chat']
        self.session = session
        self.users = []

    def perform_actions_as(self, user, delay):
        print('Hello, I\'m %s' % user.login)
        for _ in range(int(random() * 100)):
            time.sleep(random() * delay)
            if (random() < 0.4):
                print('💛 %s wants to read a message' % user.login)
                mid = self.redis.zpopmin('%s:%s' % (constants.SS_INCOMING_MESSAGES, user.login))
                if not mid or not mid[0]:
                    print('But %s has not a new message' % user.login)
                    continue
                mid = mid[0][0]
                msg = Message.load(mid, self.redis)
                self.chat.read_message(msg)
            else:
                to = USERS[math.floor(random() * len(USERS))]
                print('💙 %s writes a message to %s' % (user.login, to))
                msg = Message(author=user.login, to=to, body=lorem.sentence())
                self.chat.publish_message(msg)

    def enter(self):
        answers = self.ask()
        count = int(answers['count'])
        delay = int(answers['delay'])
        self.users = [
            User(login=USERS[math.floor(random() * len(USERS))], role='user', redis=self.redis)
            for _ in range(count)]
        for u in self.users:
            u.save()
        print('create %s users' % count)
        print('\n'.join(map(lambda u: u.login, self.users)))
        processes = []
        for user in self.users:
            processes.append(multiprocessing.Process(target=self.perform_actions_as, args=[user, delay]))
            processes[-1].start()
        for p in processes:
            p.join()
