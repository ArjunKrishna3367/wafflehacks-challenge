# initially following tutorial from
# https://towardsdatascience.com/sending-data-from-a-flask-app-to-postgresql-database-889304964bf2

#incorporating some elements from previous project for databases course

import os
import random
import string

from flask import Flask, request, render_template, g, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
import datetime


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir, static_url_path='')
print(tmpl_dir)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#for testing on local database
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://arjun:waffle@localhost/flask_db'

# details for db hosted on heroku
# apparently these details might change, not sure when
host = "ec2-3-219-229-143.compute-1.amazonaws.com"
port = 5432
database = "dfeh4rkfk17g87"
user = "vputohlcpjkdle"
password = "4271bc45e4782721e0cb54935d49559da5998e6bce0a51589237d6b376daaab8"

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{user}:{password}@{host}/{database}"

connection = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

db = SQLAlchemy(app)


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = connection.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/event_list')
def event_list():
    cursor = g.conn.execute('SELECT * '
                            'FROM events '
                            'ORDER BY date')
    events = []
    for result in cursor:
        events.append(result)
    cursor.close()

    context = dict(data=events)
    return render_template("event_list.html", **context)


@app.route("/event_form")
def event_form():
    return render_template("event_add_form.html")

@app.route("/add_event", methods=['POST'])
def add_event():
    name = request.form["name"]
    location = request.form["location"]
    date = datetime.datetime.strptime(request.form["date"], '%Y-%m-%d').date()
    eid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    g.conn.execute('INSERT INTO Events(eid, name, location, date) VALUES (%s, %s, %s, %s)', eid, name, location, date)

    return render_template("event_add_form.html")

@app.route('/edit_event/<eid>', methods=['GET'])
def edit_event(eid):
    cursor = g.conn.execute('SELECT * '
                   'FROM Events '
                   'WHERE eid = %s', eid)
    context = dict(event = cursor.fetchone())
    return render_template("event_edit_form.html", **context)

@app.route('/event_update/<eid>', methods=['POST'])
def event_update(eid):
    name = request.form["name"]
    location = request.form["location"]
    date = datetime.datetime.strptime(request.form["date"], '%Y-%m-%d').date()
    g.conn.execute('UPDATE Events '
                   'SET name = %s, location = %s, date = %s '
                   'WHERE eid = %s', name, location, date, eid)
    return redirect('/event_list')

@app.route('/delete_event/<eid>', methods=['POST'])
def delete_event(eid):
    g.conn.execute('DELETE FROM Events '
                   'WHERE eid = %s', eid)
    return redirect('/event_list')



@app.route('/participant_list', methods=['GET'])
def participant_list():
    cursor = g.conn.execute('SELECT * '
                            'FROM People '
                            'ORDER BY last')
    people = []
    for result in cursor:
        people.append(result)
    cursor.close()

    context = dict(data=people)
    return render_template("participants.html", **context)

@app.route("/person_form", methods=['GET'])
def person_form():
    return render_template("person_add_form.html")

@app.route("/add_person", methods=['POST'])
def add_person():
    first = request.form["first"]
    last = request.form["last"]
    school = request.form["school"]
    pid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    g.conn.execute('INSERT INTO People(pid, first, last, school) VALUES (%s, %s, %s, %s)', pid, first, last, school)

    return render_template("person_add_form.html")

@app.route('/edit_person/<pid>', methods=['GET'])
def edit_person(pid):
    cursor = g.conn.execute('SELECT * '
                   'FROM People '
                   'WHERE pid = %s', pid)
    context = dict(person = cursor.fetchone())
    return render_template("person_edit_form.html", **context)

@app.route('/person_update/<pid>', methods=['POST'])
def person_update(pid):
    first = request.form["first"]
    last = request.form["last"]
    school = request.form["school"]
    g.conn.execute('UPDATE People '
                   'SET first = %s, last = %s, school = %s '
                   'WHERE pid = %s', first, last, school, pid)
    return redirect('/participant_list')

@app.route('/delete_person/<pid>', methods=['POST'])
def delete_person(pid):
    g.conn.execute('DELETE FROM People '
                   'WHERE pid = %s', pid)
    return redirect('/participant_list')

@app.route('/event_attendance/<eid>', methods=['GET'])
def event_attendance(eid):
    cursor = g.conn.execute('SELECT * FROM People P '
                            'WHERE P.pid IN '
                            '(SELECT P.pid FROM People P '
                            'RIGHT JOIN Attends A '
                            'ON P.pid = A.pid AND A.eid = %s' 
                            'WHERE P.pid IS NOT NULL) '
                            'ORDER BY P.last', eid)

    attendees = []
    for result in cursor:
        attendees.append(result)

    print(attendees)

    cursor = g.conn.execute('SELECT * FROM People P '
                            'WHERE P.pid NOT IN '
                            '(SELECT P.pid FROM People P '
                            'RIGHT JOIN Attends A '
                            'ON P.pid = A.pid AND A.eid = %s '
                            'WHERE P.pid IS NOT NULL) '
                            'ORDER BY P.last', eid)

    nonattendees = []
    for result in cursor:
        nonattendees.append(result)

    print(nonattendees)

    cursor = g.conn.execute('SELECT * '
                            'FROM Events '
                            'WHERE eid = %s', eid)

    event_info = cursor.fetchone()

    cursor.close()

    context = dict(attendees=attendees, nonattendees=nonattendees, event=event_info)
    return render_template("attendance.html", **context)

@app.route('/mark_present/<eid>/<pid>', methods=['GET'])
def mark_present(eid, pid):
    g.conn.execute('INSERT INTO Attends(eid, pid) VALUES (%s, %s)', eid, pid)
    print(eid, pid)
    return redirect('/event_attendance/' + eid)

@app.route('/mark_absent/<eid>/<pid>', methods=['GET'])
def mark_absent(eid, pid):
    g.conn.execute('DELETE FROM Attends WHERE eid = %s AND pid = %s', eid, pid)
    print(eid, pid)
    return redirect('/event_attendance/' + eid)



if __name__ == '__main__':
    db.create_all()
    app.run()