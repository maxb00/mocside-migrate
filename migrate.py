# migrate.py
# Converts coding rooms json data into mocside MySQL inserts.
# TODO: Get assignment description from data -> prompt_md ! Complete
# TODO: Add course to relevant lists (Professor roster, user roster?)
# TODO: Fix blank test cases on problem 2
# TODO: Auth from file. ! Complete

import json
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from functools import cache  # @cache decorator will save redoing queries.
import argparse
import pdb

parser = argparse.ArgumentParser(
    description='Designate file location and user ID.')
parser.add_argument('-i', '--fscid', metavar='fscid', type=int,
                    nargs=1, help='Set owner fsc_id', default=1237419)
parser.add_argument('-p', '--path', metavar='path', type=str, nargs=1,
                    help='The file path of course to be imported', required=True)
args = parser.parse_args()

USER_ID = args['fscid']
# FILENAME = "CSC2290_questions-truncated.json"  # TODO: Make arg. ! Complete
FILENAME = args['path']
now = datetime.now()
now_format = now.strftime("%Y-%m-%d %H:%M:%S")
with open("auth.json", encoding='utf8') as f:
    auth = json.load(f)

# create assignment from data
def create_assignment(connection, assignment_name, lab_id, data):
    lang, starter, model, desc = data
    starter = connection._cmysql.escape_string(starter)
    model = connection._cmysql.escape_string(model)
    desc = connection._cmysql.escape_string(desc)
    if lang == 'java':
        query = f"""
        INSERT INTO
          `assignments` (`name`, `description`, `java_starter`, `java_model`, `lab_id`, `published`, `created_at`, `updated_at`)
        VALUES ('{assignment_name}', '{desc.decode('utf-8')}', '{starter.decode('utf-8')}', '{model.decode('utf-8')}', {lab_id}, 1, '{now_format}', '{now_format}');
        """
        execute_query(connection, query)
    else:
        query = f"""
        INSERT INTO
          `assignments` (`name`, `description`, `python_starter`, `python_model`, `lab_id`, `published`, `created_at`, `updated_at`)
        VALUES ('{assignment_name}', '{desc.decode('utf-8')}', '{starter}', '[]', {lab_id}, 1, '{now_format}', '{now_format}');
        """
        execute_query(connection, query)

    problem_id = find_problem_id(connection, assignment_name, lab_id)
    return problem_id


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

# create a new lab
def create_lab(connection, course_id, lab_name):
    query = f"""
    INSERT INTO
      `labs` (`name`, `description`, `course_id`, `created_at`, `updated_at`)
    VALUES ('{lab_name}', 'Imported from Coding Rooms', {course_id}, '{now_format}', '{now_format}');
    """
    execute_query(connection, query)
    lab_id = find_lab_id(connection, course_id, lab_name)
    return lab_id


# create test case from payload
def create_test_case(connection, problem_id, data):
    title, points, input, out, feedback, compare = data
    query = f"""
    INSERT INTO
      `test_cases` (`title`, `assignment_id`, `input`, `output`, `points`, `compare_method`, `feedback`, `created_at`, `updated_at`)
    VALUES ('{title}', {problem_id}, '{input.decode('utf-8')}', '{out.decode('utf-8')}', {points}, '{compare}', '{feedback.decode('utf-8')}', '{now_format}', '{now_format}');
    """
    execute_query(connection, query)


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
      `name` = '{data[0][0]}'
      AND `created_at` = '{data[0][1]}'
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
    FROM assignments
    WHERE
      `name` = '{name}'
      AND `lab_id` = {lab_id}
    LIMIT 1;
    """
    result = execute_read_query(connection, query)
    return result[0][0]


def parse_problem_data(problem):
    # things we need:
    # java_starter OR python_starter and model, lang
    data = json.loads(problem['single_file_code_data'])
    desc = problem['prompt_md']
    lang = data['common']['template']['primaryCodeLanguage']
    starter = data['common']['template']['defaultFileContents']
    model = data['grading']['modelSolution']['defaultFileContents']
    return [(lang, starter, model, desc), data]


# function to update prof course list so they see the imported course
def updateProf(connection, course_id):
    # get prof object from USER_ID
    query = f"""
    SELECT courses
    FROM professors
    WHERE `fsc_id` = {USER_ID}
    LIMIT 1;
    """
    execute_read_query(connection, query)
    pdb.set_trace()
    # add course to list
    # update prof object
    return 0

# main function
def main():
    connection = create_connection(auth["host"], auth["uname"], auth["pass"])
    execute_query(connection, 'use mocside;')
    with open(FILENAME, encoding="utf8") as f:
        data = json.load(f)

    # first, we need to create the course.
    course_name = FILENAME.split('_')[0]
    course_create_query = f"""
    INSERT INTO
      `courses` (`name`, `description`, `owner_id`, `created_at`, `updated_at`)
    VALUES ('{course_name}', 'Imported from Coding Rooms', {USER_ID}, '{now_format}', '{now_format}');
    """
    print('Creating course ' + course_name + '...   ', end='')
    execute_query(connection, course_create_query)

    # after we insert, we need to find the course ID of the course we just made.
    course_id = find_course_id(connection, [(course_name, now_format)])
    print('Complete. ID: ' + str(course_id))
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
            print("Creating Lab " + lab_name + '...   ', end='')
            lab_id = create_lab(connection, course_id, lab_name)
            print("Complete. ID: " + str(lab_id))
        else:
            # hopefully, cache will speed this up.
            lab_id = find_lab_id(connection, course_id, lab_name)

        problem_name = split_name[1]
        print("Creating problem " + problem_name + '...   ', end='')
        problem_data, parsed_data = parse_problem_data(problem)
        # now that we have our data, make assignment
        problem_id = create_assignment(
            connection, problem_name, lab_id, problem_data)
        print("Complete. ID: " + str(problem_id))

        # now that we've made an assignment, we must make it's test cases.
        for tc in parsed_data['grading']['testCases']:
            # I am going to assume the only type supported and used is stdout
            tc_title = tc['title']
            print("Creating test case " + tc_title + '...   ', end='')
            tc_points = int(tc['points'])
            tc_in = connection._cmysql.escape_string(tc['stdin'])
            tc_out = connection._cmysql.escape_string(tc['stdout'])
            tc_feedback = connection._cmysql.escape_string(
                tc['feedbackOnFailure'])
            tc_compare = tc['stdoutCompareMethod']
            # we have to parse stdoutCompareMethod further
            # not having python 3.10 here is a BUMMER -> TODO: implement match (3.10)
            if tc_compare == 'equals_flexible':
                tc_compare = 'flexible'
            elif tc_compare == 'equals':
                tc_compare = 'exact'
            # else, leave it and deal after, I guess. Regex is in form.
            # we are ready for an insert
            payload = (tc_title, tc_points, tc_in,
                       tc_out, tc_feedback, tc_compare)
            create_test_case(connection, problem_id, payload)
            print('Complete.')


if __name__ == '__main__':
    connection = create_connection(auth["host"], auth["uname"], auth["pass"])
    updateProf(connection, 2321)
