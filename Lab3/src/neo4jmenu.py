from neo4jserver import Neo4jServer
from tags import Tags


def show_way(nodes: list):
    way = ""
    for node in nodes:
        way += f"{node} ->"
    print(way[:-3])


def show_error(err: str):
    print(f"Error: {err}")


def print_list(name_of_list, list):
    print(name_of_list)
    count = 1
    for item in list:
        print(f"{count}: {item}")
        count += 1


def main_menu() -> int:
    menu_items = [
        'Tagged messages(6.1)',
        'N long relations(6.2)',
        'Shortest way(6.3)',
        'Only spam conversation(6.4)',
        'Tagged messages without relations(6.5)',
        'Exit',
    ]
    for i in range(len(menu_items)):
        print(f'{i + 1}. {menu_items[i]}')
    return int(input("What do you want to do?: "))


def main():
    neo4j_server = Neo4jServer()

    while True:
        try:
            choice = main_menu()
        except:
            print('Error occured, please try again')
            continue

        if choice == 1:
            print('Enter comma-separated list of tags:')
            print(f'Available tags: {Tags.get_members_list()}')
            tags = input()

            try:
                result = neo4j_server.get_users_with_tagged_messages(tags)
                print_list('Users: ', result)
            except Exception as e:
                show_error(e)

        elif choice == 2:
            print('Enter N:')

            try:
                n = int(input())
            except:
                print('N should be an integer')
                continue

            result = neo4j_server.get_users_with_n_long_relations(n)
            print_list('Pairs of users: ', result)

        elif choice == 3:
            print('Enter user names as follows: <usr1>, <usr2>')
            usr1, usr2 = input().split(', ')[:2]

            try:
                result = neo4j_server.shortest_way_between_users(usr1, usr2)
                show_way(result)
            except Exception as e:
                show_error(e)

        elif choice == 4:
            result = neo4j_server.get_users_with_have_only_spam_conversation()
            print_list('Pairs of users: ', result)

        elif choice == 5:
            print('Enter comma-separated list of tags:')
            print(f'Available tags: {Tags.get_members_list()}')
            tags = input()

            try:
                result = neo4j_server.get_unrelated_users_with_tagged_messages(tags)
                print_list('Pairs of unrelated users: ', result)
            except Exception as e:
                show_error(e)

        elif choice == 6:
            print("Exiting...")
            break

        else:
            print("Please select correct option [1-3]")


if __name__ == '__main__':
    main()
