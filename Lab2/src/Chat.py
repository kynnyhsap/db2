from src import constants, Message
import time


def now():
    return int(round(time.time() * 1000))


class Chat:
    def __init__(self, redis):
        self.redis = redis

    def publish_message(self, message):
        p = self.redis.pipeline()
        # save message data
        message.save(p)
        # push event about created message
        p.publish('%s:%s' % (constants.EVENT_MESSAGE_CREATED, message.author), message.id)
        # add message to list of unprocessed messages for workers
        p.sadd(constants.SET_UNPROCESSED_MESSAGES, message.id)
        # add message to list of author's sent messages
        p.zadd('%s:%s' % (constants.SS_SENT_MESSAGES, message.author), {message.id: now()})
        # add message to the group 'created messages'
        p.zadd('%s:%s' % (constants.SS_WAIT_FOR_MODERATION_MESSAGES, message.author), {message.id: now()})
        # save to action log
        p.lpush(constants.LIST_ACTION_LOGS, 'user "%s" publish message "%s"' % (message.author, message.id))
        p.execute()

    def listen_events(self, events_handlers):
        p = self.redis.pubsub()
        p.psubscribe(**events_handlers)
        thread = p.run_in_thread(sleep_time=0.001)
        return thread

    def get_next_unprocessed_message(self, admin_login):
        mid = self.redis.srandmember(constants.SET_UNPROCESSED_MESSAGES, 1)
        if not mid or not mid[0]:
            return
        mid = mid[0]
        message_key = '%s:%s' % (constants.MESSAGES_STORAGE, mid)
        author = self.redis.hget(message_key, 'author')
        message = Message.load(mid, self.redis)
        p = self.redis.pipeline()
        # delete message from list of unprocessed messages
        p.srem(constants.SET_UNPROCESSED_MESSAGES, mid)
        # delete message from group 'created messages'
        p.zrem('%s:%s' % (constants.SS_WAIT_FOR_MODERATION_MESSAGES, author), mid)
        # update status of a message
        message.status = constants.STATUS_MESSAGE_ON_MODERATION
        message.save(p)
        # add message to group with messages 'on moderation'
        p.zadd('%s:%s' % (constants.SS_MESSAGES_ON_MODERATION, author), {mid: now()})
        # write logs
        p.lpush(constants.LIST_ACTION_LOGS, '"%s" took message "%s" on moderation' % (admin_login, mid))
        p.execute()
        return message

    def approve_message(self, admin_login, message):
        p = self.redis.pipeline()
        # mark message as approved
        message.status = constants.STATUS_MESSAGE_APPROVED
        message.save(p)
        # delete message from list of unprocessed messages
        p.srem(constants.SET_UNPROCESSED_MESSAGES, message.id)
        # append event to log
        p.lpush(constants.LIST_ACTION_LOGS, 'admin "%s" approve message "%s"' % (admin_login, message.id))
        # delete message from group 'on moderation'
        p.zrem('%s:%s' % (constants.SS_MESSAGES_ON_MODERATION, message.author), message.id)
        # add message to the group 'approved messages'
        p.zadd('%s:%s' % (constants.SS_APPROVED_MESSAGES, message.author), {message.id: now()})
        # increase number of sent messages of the message author
        p.zincrby(constants.SS_ACTIVE_SENDERS, 1, message.author)
        # add message to queue of incoming messages receiver
        p.zadd('%s:%s' % (constants.SS_INCOMING_MESSAGES, message.to), {message.id: message.created_at})
        # publish event, message approved to author
        p.publish('%s:%s' % (constants.EVENT_MESSAGE_APPROVED, message.author), message.id)
        # publish event, incoming message to addresser
        p.publish('%s:%s' % (constants.EVENT_INCOMING_MESSAGE, message.to), message.id)
        p.execute()

    def block_message(self, admin_login, message):
        p = self.redis.pipeline()
        # mark message as spam
        message.status = constants.STATUS_MESSAGE_BLOCKED
        message.save(p)
        # delete message from list of unprocessed messages
        p.srem(constants.SET_UNPROCESSED_MESSAGES, message.id)
        # delete message from list 'on moderation'
        p.zrem('%s:%s' % (constants.SS_MESSAGES_ON_MODERATION, message.author), message.id)
        # add message to the list of blocked messages
        p.zadd('%s:%s' % (constants.SS_BLOCKED_MESSAGES, message.author), {message.id: now()})
        # increase number of sent messages of the message author
        p.zincrby(constants.SS_SPAMMERS, 1, message.author)
        # publish event, message approved to author
        p.publish('%s:%s' % (constants.EVENT_MESSAGE_BLOCKED, message.author), message.id)
        # append event to log
        p.lpush(constants.LIST_ACTION_LOGS, 'admin "%s" block message "%s"' % (admin_login, message.id))
        p.execute()

    def read_message(self, message):
        if not message:
            return
        p = self.redis.pipeline()
        # mark message as read
        message.status = constants.STATUS_MESSAGE_READ
        message.save(p)
        # delete message from group 'approved'
        p.zrem('%s:%s' % (constants.SS_APPROVED_MESSAGES, message.author), message.id)
        # add message to list of addresser read message
        p.sadd('%s:%s' % (constants.SET_READ_MESSAGES, message.to), message.id)
        # add message to group with 'delivered messages'
        p.zadd('%s:%s' % (constants.SS_DELIVERED_MESSAGES, message.author), {message.id: now()})
        # append event to log
        p.lpush(constants.LIST_ACTION_LOGS, 'user "%s" read message "%s"' % (message.to, message.id))
        # publish event, message approved to author
        p.publish('%s:%s' % (constants.EVENT_MESSAGE_DELIVERED, message.author), message.id)
        p.execute()
