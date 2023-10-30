import sqlite3
import re
import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


def get_table_list() -> list[str]:
    """
    Returns a list of the required tables in the database.
    """
    return ["rules", "logs", "users", "database_logs"]


def create_table(table: str) -> str:
    """
    Creates SQL query strings for creating tables in the database.

    :param table: Name of the table to be created
    :return: SQL query string for creating the specified table
    """
    if table == "rules":
        table_to_create = "rules(rule_id, rule_name, rule_description, create_time, change_time, active)"
    elif table == "logs":
        table_to_create = ("logs(log_id, rule_id, user_id, time_event, path, original_log, "
                           "create_time NOT NULL DEFAULT(datetime(CURRENT_TIMESTAMP)), change_time, active)")
    elif table == "users":
        table_to_create = "users(user_id, user_name, create_time, change_time, active)"
    elif table == "database_logs":
        table_to_create = "database_logs(log_id, command_name, records_effected, create_time, change_time, active)"
    else:
        print("Error: The table is defined")
        return ''
    return f"CREATE TABLE {table_to_create}"


def check_all_tables_exist(cur_db: sqlite3.Cursor) -> None:
    """
    Checks if all required tables exist in the database, creates them if they don't.

    :param cur_db: Database cursor object
    """
    try:
        res = cur_db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_exist = [row[0] for row in res.fetchall()]
        for table in get_table_list():
            if table not in tables_exist:
                print({f"Create table: {table}"})
                cur_db.execute(create_table(table))
        print("tables", tables_exist, "are exist.")
    except sqlite3 as sql_error:
        print("Error: Unable to create table or connect to database.", sql_error)
    except sqlite3.Error as sql_error:  # Updated to catch sqlite3.Error
        print("Error: Unable to create table or connect to database.", sql_error)


def connect_to_database() -> sqlite3.Connection | None:
    """
    Establishes a connection to the SQLite database.

    :return: Database connection object or None if connection failed
    """
    try:
        data_base = sqlite3.connect(os.getenv('DATABASE_PATH'))
        cur_db = data_base.cursor()
        print("check if all tables exist.")
        check_all_tables_exist(cur_db)
        try:
            data_base.commit()
        except sqlite3.Error as commit_error:
            print("Error during commit operation:", commit_error)

        return data_base

    except sqlite3.Error as sql_error:
        print("Error: Unable to create or connect to database.", sql_error)
        raise sql_error


def get_event_id(record: str) -> str | None:
    """
    Extracts the event ID from a log record.

    Args:
        record (str): A log record.

    Returns:
        str | None: The event ID if found, otherwise None.
    """
    event_key = re.compile(r'msg=audit\(([0-9]*\.[0-9]+:[0-9]+)+\):.*')  # Regular expression for matching event_id
    match = event_key.search(record)
    if match:
        return match[1]
    return None


def get_rule_name(record: str) -> str | None:
    """
    Extracts the rule name from a log record.

    Args:
        record (str): A log record.

    Returns:
        str | None: The rule name if found, otherwise None.
    """
    rule_key = re.compile(r'.*key="([^"]*).*')  # Regular expression for matching rule_name
    role_name = rule_key.search(record)
    return role_name[1] if role_name else None


def get_record_with_key(record: str) -> str | None:
    """
    Extracts the record with the rule key from a log record.

    Args:
        record (str): A log record.

    Returns:
        str | None: The record with the rule key if found, otherwise None.
    """
    # Regular expression for matching rule_key
    rule_key = re.compile(r'msg=audit\(([0-9]*\.[0-9]+)'  # timestmp
                          r':([0-9]+)+\):'                       # log number  
                          r'.*auid=([0-9]+).*'                   # user id
                          r'key="([^"]*)'                        # key name
                          r'"', re.IGNORECASE)
    return rule_key.search(record)


def get_user_id(record: str) -> str | None:
    """
    Extracts the user ID from a log record.

    Args:
        record (str): A log record.

    Returns:
        str | None: The user ID if found, otherwise None.
    """
    user_id_key = re.compile(r'uid=([0-9]+).*')  # Regular expression for matching user_id
    match = user_id_key.search(record)

    return match[1] if match else None


def get_time_readable(record: str) -> str | None:
    """
    Converts the timestamp from a log record to a human-readable format.

    Args:
        record (str): A log record.

    Returns:
        str | None: The timestamp in a human-readable format if found, otherwise None.
    """
    time_key = re.compile(r'msg=audit\(([0-9]*\.[0-9]+)')  # Regular expression for matching time
    match = time_key.search(record)
    return datetime.datetime.utcfromtimestamp(float(match[1])) if match else None


def get_path(record: str) -> str | None:
    """
    Extracts the file path from a log record.

    Args:
        record (str): A log record.

    Returns:
        str | None: The file path if found, otherwise None.
    """
    path_key = re.compile(r'.*type=PATH msg=audit.*name="(.*)" inode')  # Regular expression for matching path
    match = path_key.search(record)

    return match[1] if match else None


def save_new_event(event_logs: str, cur_db: sqlite3.Cursor) -> None:
    """
     Saves a new event log to the logs table in the database.

     Args:
         event_logs (str): The event log to be saved.
         cur_db (sqlite3.Cursor): The database cursor used to execute queries.

     Returns:
         None
     """
    insert = """INSERT INTO logs(log_id, rule_id, user_id, time_event, path, original_log)
                        VALUES(?, ?, ?, ?, ?, ?) """
    values = (get_event_id(event_logs),
              get_rule_name(event_logs),
              get_user_id(event_logs),
              get_time_readable(event_logs),
              get_path(event_logs),
              event_logs)
    try:
        cur_db.execute(insert, values)
    # TODO improve Exception by reason
    except sqlite3 as sql_error:
        print("Error: Unable to connect to database.", sql_error)
        print("Can't save: \n", event_logs)


def event_in_database(database: sqlite3.Connection, event_id: str) -> bool | None:
    """
    Checks if an event with a given ID already exists in the logs table.

    Args:
        database (sqlite3.Connection): The SQLite database connection.
        event_id (str): The ID of the event to check.

    Returns:
        bool | None: True if the event exists, False otherwise. None if there was an error executing the query.
    """
    try:
        database_cursor = database.cursor()
        database_cursor.execute(f"SELECT log_id FROM logs WHERE log_id = ?  ", (event_id,))
        find = database_cursor.fetchone()
        return True if find else False

    except sqlite3 as sql_error:
        print("Error: Unable to create table or connect to database.", sql_error)
        return None


def update_event_in_database(database: sqlite3.Connection, event_id: str) -> int:
    """
    Updates an existing event log in the database.

    Args:
        database (sqlite3.Connection): The SQLite database connection.
        event_id (str): The ID of the event to update.

    Returns:
        int: The number of records updated. (Currently, this function always returns 0 as it is not implemented yet)
    """
    # TODO: Implement the function body
    return 0


def get_last_time_create_record(cur_db: sqlite3.Cursor) -> str | None:
    """
    Retrieves the latest creation time of any record in the logs table.

    Args:
        cur_db (sqlite3.Cursor): A database cursor to execute SQL queries.

    Returns:
        str | None: The latest creation time as a string if found, otherwise None.
    """
    #  todo when the table database logs redy change the query
    try:
        cur_db.execute("SELECT MAX(create_time) FROM logs")
        last_time = cur_db.fetchall()[0][0]

        return last_time if last_time else ''
    except sqlite3 as sql_error:
        print("Error: Unable to  connect to database.", sql_error)
        return None


def number_of_rules(db: sqlite3.Connection) -> str | None:
    """
    Counts the distinct rule IDs in the logs table.

    Args:
        db (sqlite3.Connection): A connection object to the SQLite database.

    Returns:
        str | None: The number of distinct rule IDs as a string if found, otherwise None.
    """
    try:
        cur_db = db.cursor()
        cur_db.execute("SELECT COUNT (DISTINCT rule_id) FROM logs")
        return cur_db.fetchone()[0]
    except sqlite3 as sql_error:
        print("Error: Unable to connect to database.", sql_error)
        return None


def command_most_frequently(db: sqlite3.Connection) -> str:
    """
    Finds the rule ID that appears most frequently in the logs table.

    Args:
        db (sqlite3.Connection): A connection object to the SQLite database.

    Returns:
        str: The most frequently appearing rule ID.
    """
    try:
        cur_db = db.cursor()
        cur_db.execute("SELECT `rule_id` FROM `logs` GROUP BY `rule_id` ORDER BY COUNT(*) DESC LIMIT 1")
        return cur_db.fetchone()[0]
    except sqlite3 as sql_error:
        print("Error: Unable to  connect to database.", sql_error)
        return "Can't find the command most frequently"


def user_most_frequently(db: sqlite3.Connection) -> str:
    """
    Finds the user ID that appears most frequently in the logs table.

    Args:
        db (sqlite3.Connection): A connection object to the SQLite database.

    Returns:
        str: The most frequently appearing user ID.
    """
    cur_db = db.cursor()
    cur_db.execute("SELECT `user_id` FROM `logs` GROUP BY `user_id` ORDER BY COUNT(*) DESC LIMIT 1")
    return cur_db.fetchone()[0]


def path_most_frequently(db: sqlite3.Connection) -> str:
    """
    Finds the file path that appears most frequently in the logs table.

    Args:
        db (sqlite3.Connection): A connection object to the SQLite database.

    Returns:
        str: The most frequently appearing file path.
    """
    cur_db = db.cursor()
    cur_db.execute("SELECT `path` FROM `logs` WHERE `path` IS NOT NULL GROUP BY `path` ORDER BY COUNT(*) DESC LIMIT 2")
    return cur_db.fetchone()[0]


def get_number_of_new_record(db: sqlite3.Connection) -> str:
    """
    Counts the number of new records in the logs table based on the latest creation time.

    Args:
        db (sqlite3.Connection): A connection object to the SQLite database.

    Returns:
        str: The number of new records.
    """
    cur_db = db.cursor()
    # todo change the table from logs to database_logs
    cur_db.execute("SELECT COUNT (*) FROM logs WHERE create_time = (SELECT MAX(create_time) FROM logs)")
    return cur_db.fetchone()[0]


def command_least_frequently(db: sqlite3.Connection) -> str:
    """
    Finds the rule ID that appears least frequently in the logs table.

    Args:
        db (sqlite3.Connection): A connection object to the SQLite database.

    Returns:
        str: The least frequently appearing rule ID.
    """
    cur_db = db.cursor()
    cur_db.execute(
        "SELECT `rule_id` FROM `logs` WHERE rule_id IS NOT NULL GROUP BY `rule_id` ORDER BY COUNT(*) ASC LIMIT 1")
    return cur_db.fetchone()[0]


def save_logs_file_to_database(database: sqlite3.Connection, log_file_path: str) -> None:
    """
    Reads logs from a file and saves them to the database.

    Args:
        database (sqlite3.Connection): The SQLite database connection.
        log_file_path (str): The path to the log file.

    Returns:
        None
    """
    print("save logs from:", log_file_path)
    database_cursor = database.cursor()
    with open(log_file_path, 'r') as log_file:
        event_id, event_logs = '', ''
        new_records, update_records = 0, 0

        for line in log_file:
            if event_id != get_event_id(line):  # new event
                if get_record_with_key(line):  # save event
                    if event_in_database(database, event_id):
                        update_records += update_event_in_database(database, event_id)
                    else:
                        save_new_event(event_logs, database_cursor)
                        new_records += 1
                # update with new event data
                event_logs = line
                event_id = get_event_id(line)
            else:
                event_logs = event_logs + line
    database.commit()

    print(new_records, f"log records have been successfully added to the database")
    print(update_records, f"log records have been successfully updated")


def print_records(database: sqlite3.Connection, num_records: int) -> None:
    """
    Prints a specified number of records from the 'logs' table in the database.

    Args:
        database (sqlite3.Connection): A connection object to the SQLite database.
        num_records (int): The number of records to print from the 'logs' table.

    Returns:
        None
    """
    database_cursor = database.cursor()
    database_cursor.execute("SELECT * FROM logs")
    data = database_cursor.fetchall()
    for i, record in enumerate(data):
        print(record)
        if i > num_records:
            return
    print("\n\n")


def time_file_change(file_path: str) -> str:
    """
    Returns the last modification time of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: A string representing the last modification time of the file in 'YYYY-MM-DD HH:MM:SS' format.
    """
    try:
        epoch_time = os.path.getmtime(file_path)
        file_change = datetime.datetime.utcfromtimestamp(epoch_time).strftime('%Y-%m-%d %H:%M:%S')
        return file_change
    except FileNotFoundError:
        return "File not found"
    except Exception as e:
        return f"An error occurred: {str(e)}"


def save_logs_to_database(data_base: sqlite3.Connection) -> None:
    """
    Reads logs from a directory and saves them to the database if they are newer than the latest logs in the database.

    Args:
        data_base (sqlite3.Connection): The SQLite database connection.

    Returns:
        None
    """
    print("save_logs_to_database.")
    cur_db = data_base.cursor()
    db_last_change = get_last_time_create_record(cur_db)
    if db_last_change is None:
        print("can't save logs to database.")
        return
    log_file_path = os.getenv('LOG_FILE_PATH')

    try:
        lod_dir_path = os.getenv('LOG_DIR_PATH')
        try:
            lod_dir = os.scandir(lod_dir_path)
        except FileNotFoundError as fnf_error:
            print("Error: Directory not found", fnf_error)
            return
        for log_file in lod_dir:
            if not os.path.exists(log_file_path):
                print("Error: Log file does not exist")
                continue
            file_change = time_file_change(log_file_path)
            if db_last_change < file_change:
                save_logs_file_to_database(data_base, lod_dir_path + log_file.name)
    except IOError:
        print("Error: can't open file!\n", IOError)


if __name__ == '__main__':
    print("Try to connect...")
    db1 = connect_to_database()
    print("connect!")
    save_logs_to_database(db1)
    number_of_rules(db1)
    print("good!")
    db1.close()
