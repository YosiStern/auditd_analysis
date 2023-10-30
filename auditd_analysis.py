import sqlite3
import database
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()


def get_user_action_choice() -> int:
    """
    Display a menu of actions to the user and get their choice.

    Returns:
        int: The user's chosen action as an integer.
    """
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
    user_input = input("Please select an action (1-7): ")
    while not user_input.isdigit() or int(user_input) not in range(1, 8):
        print(options)
        print("You must select a number from the list!")
        user_input = input("Please select an action (1-7): ")

    action = int(user_input)
    return action


def execute_action(action: int, db: sqlite3.Connection) -> None:
    """
    Execute the action corresponding to the user's choice.

    Args:
        action (int): The user's chosen action.
        db (sqlite3.Connection): The database connection object.
    """

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
    """
    Prompt the user to update the database and perform the update if confirmed.

    Args:
        db (sqlite3.Connection): The database connection object.
    """

    updating = input("""
Updating the database blogs created since the last update may take time.
Would you like to do it now? (y/n)""")
    if updating in ('y', 'yes', 'Yes', 'Y'):
        print("Updating database, please wait.")
        database.save_logs_to_database(db)
    else:
        print("Not updating. \nYou can query the existing information")


def main():
    """
    The main function to run the program.
    """
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
        action = get_user_action_choice()
        execute_action(action, db)
    db.close()


if __name__ == '__main__':
    main()
