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






def apology(excuus):
    return render_template("apology.html", excuus=excuus)
