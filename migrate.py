# migrate.py
# Converts coding rooms json data into mocside MySQL inserts.

import json
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import functools # @cache decorator will save redoing queries.

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
@cache
def execute_query(connection, query):
    cursor = connection.cursor()

    try:
        cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# my own wrapper
@cache
def execute_many(connection, query, values):
    cursor = connection.cursor()

    try:
        cursor.executemany(query, values)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# from realpython src
@cache
def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
    except Error as e:
        print(f"The error '{e}' occurred")

    return result

# this function finds the new, unique course ID created by this script
def find_course_id(connection, data):
    query = f"""
    SELECT id
    FROM courses
    WHERE
      `name` = '{data[0]}'
      AND `created_at` = '{data[1]}'
    LIMIT 1;
    """
    result = execute_read_query(connection, query)
    # "... returns a list of tuples". Since I'm getting just 1 id,
    # I assume this will return like [(2280)]. I just want the int.
    return result[0][0]

# finds lab ID with given course_id and name
@cache
def find_lab_id(connection, course_id, lab_name):
    query = f"""
    SELECT id
    FROM labs
    WHERE
      `name` = '{lab_name}'
      AND `course_id` = '{course_id}'
    LIMIT 1;
    """
    result = execute_read_query(connection, query)
    return result[0][0]

# find assignment ID with given name and lab_id
@cache
def find_problem_id(connection, name, lab_id):
    query = f"""
    SELECT id
    FROM assingments
    WHERE
      `name` = '{name}'
      AND `lab_id` = {lab_id}
    LIMIT 1;
    """
    result = execute_read_query(connection, query)
    return result[0][0]

# create a new lab
def create_lab(connection, course_id, lab_name):
    query = f"""
    INSERT INTO
      `labs` (`name`, `description`, `course_id`)
    VALUES ({lab_name}, 'Imported from Coding Rooms', {course_id});
    """
    execute_query(connection, query)
    lab_id = find_lab_id(connection, course_id, lab_id)
    return lab_id

def parse_problem_data(data):
    # things we need:
    # java_starter OR python_starter and model, lang
    data = json.loads(data)
    lang = data['common']['template']['primaryCodeLanguage']
    starter = data['common']['template']['defaultFileContents']
    model = data['grading']['modelSolution']['defaultFileContents']
    return [(lang, starter, model), data]

def create_assignment(connection, assingment_name, lab_id, data):
    lang, starter, model = data
    if lang = 'java':
        query = f"""
        INSERT INTO
          `assignments` (`name`, `description`, `java_starter`, `java_model`, `lab_id`, `published`)
        VALUES ('{assingment_name}', 'Imported from Coding Rooms', '{starter}', '{model}', {lab_id}, 1)
        """
        execute_query(connection, query)
        problem_id = find_problem_id(connection, assingment_name, lab_id)
        return problem_id

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
    VALUES (%s, %s, %d, %s, %s);
    """
    vals = [(course_name, "Imported from Coding Rooms",
             1237419, now_format, now_format)]
    execute_many(connection, course_create_query, vals)

    # after we insert, we need to find the course ID of the course we just made.
    course_id = find_course_id(connection, [(course_name, now_format)])
    # then, we need to load in all of it's problems.
    labs = []
    for problem in data:
        # it looks like every problem in the import file is single file code.
        # first, lets determine the lab and problem name.
        # "title": "Lab04_Problem18: Number Counts"
        split_name = problem['title'].split('_')
        lab_name = split_name[0]
        if lab_name not in labs:
            # first time seeing this lab! let's create.
            labs.append(lab_name)
            lab_id = create_lab(connection, course_id, lab_name)
        else:
            # hopefully, cache will speed this up.
            lab_id = find_lab_id(connection, course_id, lab_name)

        problem_name = split_name[1]
        problem_data, parsed_data = parse_problem_data(problem['single_file_code_data'])
        # now that we have our data, make assignment
        problem_id = create_assignment(connection, problem_name, lab_id, problem_data)

        # now that we've made an assingment, we must make it's test cases.

if __name__ == '__main__':
    main()
