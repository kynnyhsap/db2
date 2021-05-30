import random
from threading import Thread
from neo4jserver import Neo4jServer
import user
from faker import Faker
import redis
import atexit
from tags import Tags


class User(Thread):
    def __init__(self, connection, neo4j_server, username, users_list, users_count):
        Thread.__init__(self)
        self.neo4j_server = neo4j_server
        self.connection = connection
        self.users_list = users_list
        self.users_count = users_count
        user.register(conn, neo4j_server, username)
        self.user_id = user.sign_in(conn, neo4j_server, username)

    def __get_random_tags(self) -> list:
        tags = []
        num = random.randint(0, len(Tags))
        for i in range(num):
            tag = random.choice(list(Tags)).name
            if tag not in tags:
                tags.append(tag)
        return tags
        
    def run(self):
        for x in range(2):
            message_text = fake.sentence(nb_words=10, variable_nb_words=True,
                                         ext_word_list=None) if random.choice([True, False]) else 'spam'
            receiver = users[random.randint(0, users_count - 1)]
            print(f"Message {message_text} was sent to {receiver}")
            user.create_message(self.connection, self.neo4j_server, message_text, self.__get_random_tags(), self.user_id, receiver)


def exit_handler():
    redis_conn = redis.Redis(charset="utf-8", decode_responses=True)
    online = redis_conn.smembers("online:")
    for x in online:
        redis_conn.srem("online:", x)
    print("EXIT")


if __name__ == '__main__':
    atexit.register(exit_handler)
    fake = Faker()
    users_count = 10
    users = [fake.profile(fields=['username'], sex=None)['username'] for u in range(users_count)]
    threads = []
    for x in range(users_count):
        conn = redis.Redis(charset="utf-8", decode_responses=True)
        neo4j_server = Neo4jServer()

        print(users[x])
        threads.append(User(
            conn,
            neo4j_server,
            users[x], users, users_count))
    for t in threads:
        t.start()
