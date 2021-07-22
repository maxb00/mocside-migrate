# migrate.py
# Converts coding rooms json data into mocside MySQL inserts.

import json
import mysql.connector
from mysql.connector import Error
from datetime import datetime

FILENAME = "CSC2290_questions.json"  # TODO: Make arg.

# from https://realpython.com/python-sql-libraries/#mysql
def create_connection(host_name, user_name, user_password):
    # creates connection with MySQL database
    connection = None

    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection

# from same src as above
def execute_query(connection, query):
    cursor = connection.cursor()

    try:
        cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

def execute_many(connection, query, values):
    cursor = connection.cursor()

    try:
        cursor.executemany(query, values)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")


def main():
    connection = create_connection("localhost", "root", "")
    with open(FILENAME) as f:
        data = json.load(f)

    # first, we need to create the course.
    now = datetime.now()
    now_format = now.strftime("$d/%m/%Y %H:%M:S")
    course_name = FILENAME.split('_')[0]
    course_create_query = """
    INSERT INTO
      `courses` (`name`, `description`, `owner_id`, `created_at`, `updated_at`)
    VALUES (%s, %s, %d, %s, %s)
    """
    vals = [(course_name, "Imported from Coding Rooms",
             1237419, now_format, now_format)]
    execute_many(connection, course_create_query, vals)
    # then, we need to load in all of it's problems.
    labs = []
    problems = []
    test_cases = []
    for problem in data:
        # it looks like every problem in the import file is single file code.
        pass

if __name__ == '__main__':
    main()
