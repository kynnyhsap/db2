from .BaseScene import BaseScene
from .MessageCreationScene import MessageCreationScene
from .LogsViewerScene import LogsViewerScene
from .ModerateMessagesScene import ModerateMessagesScene
from .SpammersViewerScene import SpammersViewerScene
from .SendersViewerScene import SendersViewerScene
from .OnlineUsersViewerScene import OnlineUsersViewerScene
from .IncomingMessagesViewerScene import IncomingMessagesViewerScene
from .SentMessagesViewerScene import SentMessagesViewerScene
from .ReadMessageScene import ReadMessageScene
from .OnModerationMessagesViewerScene import OnModerationMessagesViewerScene
from .WaitForModerationMessagesViewerScene import WaitForModerationMessagesViewerScene
from .DeliveredMessagesViewerScene import DeliveredMessagesViewerScene
from .BlockedMessagesViewerScene import BlockedMessagesViewerScene
from .ApprovedMessagesViewerScene import ApprovedMessagesViewerScene

SEND_A_MESSAGE = '📧 send a new message'
MODERATE = '🦸 moderate messages'
READ_MESSAGE = '📨 read messages'
VIEW_INCOMING_MESSAGES = '📥 view incoming messages'
VIEW_SENT_MESSAGES = '📥 view sent messages'
VIEW_MY_MESSAGES_ON_MODERATION = '⏳ view messages, which are being on moderation'
VIEW_WAIT_FOR_MODERATION = '🆕 view messages, that are waiting for moderation'
VIEW_DELIVERED = '🔷 view messages, that are delivered (read)'
VIEW_APPROVED = '✅ view approved messages'
VIEW_BLOCKED = '⛔️ view blocked messages'

VIEW_LOGS = '👀 view actions logs'
VIEW_SPAMMERS = '🚷 view top spammers'
VIEW_SENDERS = '📭 view top senders'
VIEW_ONLINE = '⚡️ view who is online'
BACK = '◀️ back'


class UserActionsScene(BaseScene):
    def __init__(self, session, redis):
        super().__init__([
            {
                'type': 'list',
                'name': 'action',
                'message': 'What do you want to do next?',
                'choices': self.get_choices
            },
        ])
        self.session = session
        self.redis = redis

    def get_choices(self, answers):
        if self.session['me'].role == 'admin':
            return [SEND_A_MESSAGE,
                    READ_MESSAGE,
                    VIEW_INCOMING_MESSAGES,
                    VIEW_SENT_MESSAGES,
                    VIEW_WAIT_FOR_MODERATION,
                    VIEW_MY_MESSAGES_ON_MODERATION,
                    VIEW_APPROVED,
                    VIEW_BLOCKED,
                    VIEW_DELIVERED,
                    MODERATE,
                    VIEW_ONLINE,
                    VIEW_LOGS,
                    VIEW_SENDERS,
                    VIEW_SPAMMERS, BACK]
        else:
            return [SEND_A_MESSAGE,
                    READ_MESSAGE,
                    VIEW_INCOMING_MESSAGES,
                    VIEW_SENT_MESSAGES,
                    VIEW_WAIT_FOR_MODERATION,
                    VIEW_MY_MESSAGES_ON_MODERATION,
                    VIEW_APPROVED,
                    VIEW_BLOCKED,
                    VIEW_DELIVERED,
                    BACK]

    def enter(self):
        scenes = {
            SEND_A_MESSAGE: MessageCreationScene,
            MODERATE: ModerateMessagesScene,
            VIEW_ONLINE: OnlineUsersViewerScene,
            VIEW_LOGS: LogsViewerScene,
            VIEW_SENDERS: SendersViewerScene,
            VIEW_SPAMMERS: SpammersViewerScene,
            VIEW_INCOMING_MESSAGES: IncomingMessagesViewerScene,
            VIEW_SENT_MESSAGES: SentMessagesViewerScene,
            READ_MESSAGE: ReadMessageScene,
            VIEW_WAIT_FOR_MODERATION: WaitForModerationMessagesViewerScene,
            VIEW_MY_MESSAGES_ON_MODERATION: OnModerationMessagesViewerScene,
            VIEW_BLOCKED: BlockedMessagesViewerScene,
            VIEW_APPROVED: ApprovedMessagesViewerScene,
            VIEW_DELIVERED: DeliveredMessagesViewerScene
        }
        while True:
            answers = {
                'action': VIEW_ONLINE
            }
            answers = self.ask()
            if 'action' not in answers:
                return
            scene = scenes.get(answers['action']) if answers['action'] in scenes else None
            if not scene:
                return
            else:
                scene(self.session, self.redis).enter()
