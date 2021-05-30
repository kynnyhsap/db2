import datetime
import logging

logging.basicConfig(filename="messenger.log", level=logging.INFO)


def sign_in(conn, neo4j_server, username) -> int:
    user_id = conn.hget("users:", username)

    if not user_id:
        print("No user with such username exists. Please, register first")
        return -1

    conn.sadd("online:", username)
    logging.info(f"{datetime.datetime.now()} Actor: {username} Action: log in \n")

    neo4j_server.sign_in(user_id)
    return int(user_id)


def sign_out(conn, neo4j_server, user_id) -> int:
    username = conn.hmget("user:%s" % user_id, ["login"])[0];
    logging.info(f"{datetime.datetime.now()} Actor: {username} Action: sign out \n")
    neo4j_server.sign_out(user_id)
    return conn.srem("online:", conn.hmget("user:%s" % user_id, ["login"])[0])


def create_message(conn, neo4j_server, message_text, tags: list, sender_id, consumer) -> int:
    try:
        message_id = int(conn.incr('message:id:'))
        consumer_id = int(conn.hget("users:", consumer))
    except TypeError:
        print("No user with %s username exists, can't send a message" % consumer)
        return -1

    pipeline = conn.pipeline(True)

    pipeline.hmset('message:%s' % message_id, {
        'text': message_text,
        'id': message_id,
        'sender_id': sender_id,
        'consumer_id': consumer_id,
        'tags': ','.join(tags),
        'status': "created"
    })

    pipeline.lpush("queue:", message_id)
    pipeline.hmset('message:%s' % message_id, {
        'status': 'queue'
    })

    pipeline.zincrby("sent:", 1, "user:%s" % conn.hmget("user:%s" % sender_id, ["login"])[0])
    pipeline.hincrby("user:%s" % sender_id, "queue", 1)
    pipeline.execute()

    neo4j_server.create_message(sender_id, consumer_id, {"id": message_id, "tags": tags})
    return message_id


def register(conn, neo4j_server, username):
    if conn.hget('users:', username):
        print(f"User {username} exists");
        return None

    user_id = conn.incr('user:id:')

    pipeline = conn.pipeline(True)

    pipeline.hset('users:', username, user_id)

    pipeline.hmset('user:%s' % user_id, {
        'login': username,
        'id': user_id,
        'queue': 0,
        'checking': 0,
        'blocked': 0,
        'sent': 0,
        'delivered': 0
    })
    pipeline.execute()
    logging.info(f"{datetime.datetime.now()} Actor: {username} Action: register \n")
    neo4j_server.registration(username, user_id)

    return user_id
