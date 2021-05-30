from neo4j import GraphDatabase

from tags import Tags


class Neo4jServer(object):
    def __init__(self):
        self.__driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "1111"))

    def close(self):
        self.__driver.close()

    def registration(self, username, redis_id):
        with self.__driver.session() as session:
            session.run("MERGE (u:user {name: $username, redis_id: $redis_id})"
                        "ON CREATE SET u.online = false", username=username, redis_id=redis_id)

    def sign_in(self, redis_id):
        with self.__driver.session() as session:
            session.run("MATCH (u:user {redis_id: $redis_id}) SET u.online = true", redis_id=redis_id)

    def sign_out(self, redis_id):
        with self.__driver.session() as session:
            session.run("MATCH (u:user {redis_id: $redis_id}) SET u.online = false", redis_id=redis_id)

    def create_message(self, sender_id, consumer_id, message: dict):
        with self.__driver.session() as session:
            try:
                # session.write_transaction(self.__create_message_as_node, message["id"], message["tags"])
                messages_id = session.write_transaction(self.__create_message_as_relation, int(sender_id),
                                                        int(consumer_id), message["id"])
                for tag in message["tags"]:
                    session.write_transaction(self.__add_tag_to_messages, messages_id, tag)
            except Exception as e:
                print(str(e))

    @staticmethod
    def __create_message_as_relation(tx, sender_id, consumer_id, message_id):
        result = tx.run("MATCH(a: user {redis_id: $sender_id}), (b:user {redis_id: $consumer_id})"
                        "MERGE(a) - [r: messages]->(b)"
                        "ON CREATE SET r.all = [$message_id], r.spam = [], r.tags = []"
                        "ON MATCH SET r.all = r.all + $message_id "
                        "RETURN id(r)",
                        sender_id=sender_id, consumer_id=consumer_id, message_id=message_id)
        return result.single()[0]

    @staticmethod
    def __add_tag_to_messages(tx, messages_id, tag):
        tx.run("MATCH ()-[r]-() where ID(r) = $messages_id "
               "FOREACH(x in CASE WHEN $tag in r.tags THEN [] ELSE [1] END | "
               "SET r.tags = coalesce(r.tags,[]) + $tag)", messages_id=messages_id, tag=tag)

    def deliver_message(self, redis_id):
        with self.__driver.session() as session:
            session.run("MATCH (m:messages {redis_id: $redis_id }) SET m.delivered = true", redis_id=redis_id)

    def mark_message_as_spam(self, redis_id):
        with self.__driver.session() as session:
            session.run("MATCH (u1:user)-[r:messages]->(u2:user) "
                        "WHERE $redis_id IN r.all AND NOT $redis_id IN r.spam "
                        "SET r.spam = r.spam + $redis_id", redis_id=redis_id)

    def get_users_with_tagged_messages(self, tags):
        return self.__record_to_list(self.__get_users_with_tagged_messages_from_db(tags), 'name')

    def get_unrelated_users_with_tagged_messages(self, tags):
        return self.__pair_record_to_list(self.__get_unrelated_users_with_tagged_messages(tags), 'name')

    def __get_unrelated_users_with_tagged_messages(self, tags):
        with self.__driver.session() as session:
            tags = tags.split(", ")
            for tag in tags:
                if not Tags.has_member(tag):
                    raise ValueError(f"Tag: {tag} doesnt exist")

            query = "MATCH ((u1:user)-[r1:messages]-()), ((u2:user)-[r2:messages]-()) WHERE "
            query += " AND ".join([f" \'{tag}\' IN r1.tags" for tag in tags]) + " AND "
            query += " AND ".join([f" \'{tag}\' IN r2.tags" for tag in tags])
            query += " AND NOT EXISTS((u1)-[:messages]-(u2)) RETURN u1, u2"

            result = session.run(query)
            return list(result)

    def __get_users_with_tagged_messages_from_db(self, tags):
        with self.__driver.session() as session:
            tags = tags.split(", ")
            for tag in tags:
                if not Tags.has_member(tag):
                    raise ValueError(f"Tag: {tag} doesnt exist")

            query = "MATCH (u:user)-[r:messages]-() WHERE"
            query += " AND ".join([f" \'{tag}\' IN r.tags" for tag in tags])
            query += " RETURN u"
            result = session.run(query)
            return list(result)

    def shortest_way_between_users(self, username1, username2):
        users = self.get_users()
        if username1 not in users or username2 not in users:
            raise ValueError('Invalid users names')
        with self.__driver.session() as session:
            shortest_path = session.run("MATCH p = shortestPath((u1:user)-[*..10]-(u2:user)) "
                                        "WHERE u1.name = $username1 AND u2.name = $username2 "
                                        "RETURN p", username1=username1, username2=username2)
            if shortest_path.peek() is None:
                raise Exception(f"Way between {username1} and {username2} doesnt exist")
            for record in shortest_path:
                nodes = record[0].nodes
                path = []
                for node in nodes:
                    path.append(node._properties['name'])
                return path

    def get_users_with_n_long_relations(self, n):
        with self.__driver.session() as session:
            res = session.run(f"MATCH p = (u1:user)-[*{n}]-(u2:user) "
                              f"WHERE u1 <> u2 "
                              f"RETURN u1, u2")
            return self.__pair_record_to_list(res, 'name')

    def get_users_with_have_only_spam_conversation(self):
        with self.__driver.session() as session:
            res = session.run("MATCH p = (u1:user)-[]-(u2:user)"
                              "WHERE u1 <> u2 AND all(x in relationships(p) WHERE x.all = x.spam)"
                              "RETURN u1, u2")
            return self.__pair_record_to_list(res, 'name')

    def __pair_record_to_list(self, res, pull_out_value):
        my_list = list(res)
        my_list = list(dict.fromkeys(my_list))
        new_list = []
        for el in my_list:
            list_el = list(el)
            if list_el not in new_list and list_el[::-1] not in new_list:
                new_list.append(el)

        return [[el[0]._properties[pull_out_value], el[1]._properties[pull_out_value]] for el in new_list]

    def get_users(self):
        with self.__driver.session() as session:
            res = session.run("MATCH (u:user) RETURN u")
            return self.__record_to_list(res, 'name')

    def __record_to_list(self, res, pull_out_value):
        my_list = list(dict.fromkeys(res))
        return [el[0]._properties[pull_out_value] for el in my_list]
