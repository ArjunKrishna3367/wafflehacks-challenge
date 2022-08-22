# initially following tutorial from
# https://towardsdatascience.com/sending-data-from-a-flask-app-to-postgresql-database-889304964bf2

#incorporating some elements from previous project for databases course

import os
import random
import string

from flask import Flask, request, render_template, g, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
import datetime

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir, static_url_path='')
print(tmpl_dir)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://arjun:waffle@localhost/flask_db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = 'secret string'

db = SQLAlchemy(app)

#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

class Event(db.Model):
    __tablename__ = 'events'
    eid = db.Column(db.String(8), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=True)
    date = db.Column(db.Date, nullable=True)

    def __init__(self, eid, name, location, date):
        self.eid = eid
        self.name = name
        self.location = location
        self.date = date



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
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
def eventlist():
    cursor = g.conn.execute('SELECT * '
                            'FROM events')
    events = []
    for result in cursor:
        events.append(result)
    cursor.close()

    context = dict(data=events)
    return render_template("eventlist.html", **context)


@app.route("/event_form")
def eventform():
    return render_template("eventform.html")

@app.route("/addevent", methods=['POST'])
def addevent():
    name = request.form["name"]
    location = request.form["location"]
    date = datetime.datetime.strptime(request.form["date"], '%Y-%m-%d').date()
    eid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    g.conn.execute('INSERT INTO Events(eid, name, location, date) VALUES (%s, %s, %s, %s)', eid, name, location, date)

    return render_template("eventform.html")

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



if __name__ == '__main__':
    db.create_all()
    app.run()