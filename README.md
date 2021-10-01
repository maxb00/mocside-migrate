# mocside-migrate

A simple script that converts course data from Coding Rooms into MySQL inserts
that properly inteact with the MocsIDE database.

HOW TO USE
If this is a fresh install, build a python venv (at least version 3.9) in the
home directory. Install the dependencies (python -m pip install -r requirements.txt),
and then you can run the migration using the command
  python3.9 migrate.py -i [fsc_id, default 1237419] -p ["/path/to/migration/file"]

If this is an established install, I've probably already made the environment.
Activate it (on Linux) with "source /home/max/mocside-migrate/bin/activate",
and then run the above python command in the home directory of the project.

ARGUMENT EXPLANATION


  -i, --fscid  -> The fsc_id of the desired owner of the imported course.


  -p, --path   -> The filepath of the conversion source. Ex: CSC2290_questions.json


  -t, --length -> Length, in days, to run the imported course for by default.
                  Used for calculating due dates. (Optional)

FUTURE USE
  * Create MocsIDE API hook
  * Allow professors to migrate from course create/profile?

CURRENT ISSUES
  * MocsIDE does not support unit testing. Coding Rooms does. This causes issues
  when importing, because the two (stdout compare and unit testing) don't translate well.
    -> fixed, implemented unit testing
