import csv
import urllib.request
from cs50 import SQL
from flask import redirect, render_template, request, session
from functools import wraps

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///PicUs.db")

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


def find_user(u):
    user = db.execute("SELECT * FROM users WHERE username=:username", username=u)
    return user

# Used in makegroup()
def nam_group(namegroup):
    name = db.execute("SELECT name_group FROM groups WHERE name_group=:name", name = namegroup)
    return name

# Used in makegroup()
def ses_group(name_group):
    rows = db.execute("SELECT group_id FROM groups WHERE name_group=:group", group=name_group)
    ses = rows[0]["group_id"]
    return ses

# Used in addmember()
def userse(add_mem):
    id_user = db.execute("SELECT id FROM users WHERE username=:username", username=add_mem)
    id_us = id_user[0]["id"]
    return id_us

# Used in addmember()
def add_user(id_users):
    users = db.execute("SELECT user_id FROM user_groups WHERE user_id=:user_id AND group_id=:group_id", user_id=id_users, group_id=session["group_id"])
    return users

def get_members():
    members = db.execute("SELECT user_id FROM user_groups WHERE group_id=:group_id", group_id=session["group_id"])
    return members

def apology(excuus):
    return render_template("apology.html", excuus=excuus)


