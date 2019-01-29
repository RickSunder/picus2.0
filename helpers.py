import csv
import urllib.request
from cs50 import SQL
from flask import redirect, render_template, request, session
from functools import wraps

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///PicUs.db")

# Photo upload
UPLOAD_FOLDER = '/home/ubuntu/workspace/picus2.0/upload'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
DOWNLOAD_FOLDER = '/picus2.0/upload'

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

# Used in makegroup(), groupview()
def ses_group(name_group):
    rows = db.execute("SELECT group_id FROM groups WHERE name_group=:group", group=name_group)
    ses = rows[0]["group_id"]
    return ses

# Used in addmember(), add_member()
def userse(add_mem):
    id_user = db.execute("SELECT id FROM users WHERE username=:username", username=add_mem)
    id_us = id_user[0]["id"]
    return id_us

# Used in addmember(), add_member()
def add_user(id_users):
    users = db.execute("SELECT user_id FROM user_groups WHERE user_id=:user_id AND group_id=:group_id", user_id=id_users, group_id=session["group_id"])
    return users

# Used in addmember()
def get_members():
    members = db.execute("SELECT user_id FROM user_groups WHERE group_id=:group_id", group_id=session["group_id"])
    return members

def apology(excuus):
    return render_template("apology.html", excuus=excuus)

# Used for uploading photo's
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Used in groupfeed()
def get_group():
    groupl = db.execute("SELECT group_id FROM user_groups WHERE user_id = :user_id", user_id=session["user_id"])
    return groupl

 # Used in groupfeed()
def groupnam(group):
    groupname = db.execute("SELECT name_group FROM groups WHERE group_id=:group_id", group_id=group)
    return groupname

# Used in groupfeed()
def info_group(groupl):
    group = db.execute("SELECT user_id, picture, comment FROM picture_group WHERE group_id=:id_group", id_group=groupl)
    return group

# Used in groupfeed()
def usernam(user_id):
    user = db.execute("SELECT username FROM users WHERE id=:id_user", id_user=user_id)
    return user

# Used in groupview()
def pics(group_idd):
     group = db.execute("SELECT user_id, picture, comment, like, time FROM picture_group WHERE group_id=:id_group ORDER BY time desc", id_group=group_idd)
     return group

# Used in groupview()
def nam(user_id):
    user = db.execute("SELECT username FROM users WHERE id=:id_user", id_user=user_id)
    username= user[0]["username"]
    return username

# Used in groupview()
def comm_group(profilepic):
    comment_group = db.execute("SELECT comment, user_id FROM comment_group WHERE picture=:picture AND group_id=:group_id ORDER BY id desc", picture = profilepic, group_id = session["group_id"])
    return comment_group

# Used in upload_photo()
def get_nam_group():
    group_name = db.execute("SELECT name_group FROM groups WHERE group_id=:group", group=session["group_id"])
    group = group_name[0]["name_group"]
    return group

# Used in leave_group()
def check_users():
    check = db.execute("SELECT user_id FROM user_groups WHERE group_id=:group", group = session["group_id"])
    return check

# Used in like_photo(), dislike_photo()
def like_check(name, view):
        check = db.execute("SELECT id FROM like_group WHERE user_id=:user_id AND picture_user=:picture_user AND groupname=:groupname", user_id=session["user_id"], picture_user=name, groupname=view)
        return check

# Used in like_photo(), dislike_photo()
def get_like(namel):
    like_pic = db.execute("SELECT like FROM picture_group WHERE user_id=:user_id AND picture=:picture_user AND group_id=:groupname", user_id=session["user_id"], picture_user=namel, groupname=session["group_id"])
    likes = like_pic[0]["like"]
    return likes

    # Used in like_photo(), dislike_photo()
def event_like_check(name, view):
        check = db.execute("SELECT id FROM like_event WHERE user_id=:user_id AND picture_user=:picture_user AND eventname=:eventname", user_id=session["user_id"], picture_user=name, eventname=view)
        return check

# Used in like_photo(), dislike_photo()
def event_get_like(namel):
    like_pic = db.execute("SELECT like FROM event_feed WHERE user_id=:user_id AND images=:picture_user AND event_id=:eventname", user_id=session["user_id"], picture_user=namel, eventname=session["event_id"])
    likes = like_pic[0]["like"]
    return likes

def event_check_users():
    event_check = db.execute("SELECT user_id FROM user_events WHERE event_id=:event", event = session["event_id"])
    return event_check

# Used in bin()
def bin_check(name):
    pic = db.execute("SELECT user_id FROM picture_group WHERE picture=:picture AND group_id=:group", picture = name, group=session["group_id"])
    user = pic[0]["user_id"]
    return user

# Used in bin()
def event_bin_check(name):
    pic = db.execute("SELECT user_id FROM event_feed WHERE images=:picture AND event_id=:event", picture = name, event=session["event_id"])
    user = pic[0]["user_id"]
    return user

# Used in groupview()
def comm_event(profilepicevent):
    comment_event = db.execute("SELECT comment, user_id FROM comment_event WHERE picture=:picture AND event_id=:event_id ORDER BY id desc", picture = profilepicevent, event_id = session["event_id"])
    return comment_event

def get_nam_event():
    eventname = db.execute("SELECT event_name FROM event_account WHERE event_id=:event", event=session["event_id"])
    event = eventname[0]["event_name"]
    return event