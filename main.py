import sqlite3
import database
from dotenv import load_dotenv

load_dotenv()


def ask_action_from_user() -> int:
    options = """
1. The number of different "auditd" rules/commands in the database.
2. The command that appears most frequently.
3. The user who executes the most commands.
4. The least common command.
5. The folder path that has the most activity.
6. Update database.
7. Exit.
"""
    print(options)
    action = input("Select action: \n")
    while len(action) > 1 or not "0" < action < "8":
        print(options)
        print("You must select number from the list!")
        action = input("Select action: \n")
        print("action: ", action)
    action = int(action)
    return action


def execute_action(action: int, db: sqlite3.Connection) -> None:
    if action == 1:
        print("The number of log rules that created records in the database is: ", database.number_of_rules(db))
    elif action == 2:
        print("The command that appears most frequently is: ", database.command_most_frequently(db))
    elif action == 3:
        print("The user who executes the most commands is: ", database.user_most_frequently(db))
    elif action == 4:
        print("The least common command is: ", database.command_least_frequently(db))
    elif action == 5:
        print("The folder path that has the most activity is: ", database.path_most_frequently(db))
    elif action == 6:
        print(update_database(db))


def update_database(db: sqlite3.Connection) -> None:
    updating = input("""
Updating the database blogs created since the last update may take time.
Would you like to do it now? (y/n)""")
    if updating in ('y', 'yes', 'Yes', 'Y'):
        print("Updating database, please wait.")
        database.save_logs_to_database(db)
    else:
        print("Not updating. \nYou can query the existing information")


def main():
    db = database.connect_to_database()
    # TODO Write a separate message for each problem. (permissions, memory space, etc.)
    if db is None:
        print("Can't connect or create the database, please check the problem and try again.")
        return

    # check Auditd is run and rules are exist
    # TODO  rules.check_auditd_and_rules()
    # TODO add_rules.apply_audit_rules("audit_rules.txt")

    update_database(db)

    #  TODO If give an action on command line, do only this.
    action = ""

    while action != 7:
        action = ask_action_from_user()
        execute_action(action, db)
    db.close()


if __name__ == '__main__':
    main()
