from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_from_directory, jsonify
from flask_session import Session
from flask_login import current_user, LoginManager
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
import unicodedata
import os
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask import send_from_directory
from helpers import *
import time
global request
# import giphy_client
# from giphy_client.rest import ApiException

import re

from pprint import pprint
import urllib.parse as urlparse
from django.utils.deprecation import MiddlewareMixin
import urllib
import json
import urllib.parse as urlparse
#from selenium import webdriver
#from selenium.webdriver.common.keys import Keys

import uuid

# configure application
app = Flask(__name__)

# Photo upload
UPLOAD_FOLDER = '/home/ubuntu/workspace/picus2.0/upload'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
DOWNLOAD_FOLDER = '/picus2.0/upload'

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Session(app)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# configure CS50 Library to use SQLite database
db = SQL("sqlite:///PicUs.db")



#login_manager = LoginManager()
#login_manager.init_app(app)
#login_manager.login_view = 'login'



@app.route("/")
def index():
    """The index of the website"""
    if request.method == "POST":
        return render_template("groupfeed.html", user_id=session["user_id"])
    if request.method == "GET":
        return render_template("index.html")

#GINO
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # checken voor goede invulling
        if not request.form.get("email"):
            return apology("Please fill in your email adress!")
        if not request.form.get("username"):
            return apology("Please fill in your username!")
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Password and confirmation password were not the same!")
        if request.form.get("password") == "":
            return apology("Please fill in your password!")
        elif not request.form.get("password"):
            return apology("Please fill in your password!")
        elif not request.form.get("confirmation"):
            return apology("Please fill in your password!")

        if len(db.execute("SELECT * FROM users WHERE username=:username", username=request.form.get("username"))) > 0:
            return apology("username already exists")

        geregistreerd = db.execute("INSERT INTO users (email, username, hash) VALUES(:email, :username, :password)", email=request.form.get("email"), username=request.form.get("username"), password=pwd_context.hash(request.form.get("password")))

        if not geregistreerd:
            return apology("The registration could not happen")

        # gebruiker onthouden
        session["user_id"] = geregistreerd

        # als alles doorstaan en voltooid is, bevestig registratie
        return redirect(url_for("groupfeed"))

    # opnieuw registerpagina tevoorschijn toveren wanneer geen POST
    else:
        return render_template("register.html")


@app.route("/makegroup", methods=["GET", "POST"])
@login_required
def makegroup():
    """Make new group"""
    if request.method == "POST":
        # Get name of the group from makegroup.html
        namegroup = request.form.get("name_group")

        # Check the name of the group
        name = nam_group(namegroup)
        if len(name) > 0:
            name = name[0]["name_group"]
        else:
            name = ""

        # Check if groupname already exist
        if name == namegroup:
            flash("Name of the group already exist")
            return redirect(url_for("makegroup"))

        # Get profile picture
        file = request.files['file']

        # Check if picture is uploaded
        if file == "":
            flash("Upload photo")
            return redirect(url_for("makegroup"))

        if not allowed_file(file.filename):
            flash("This is not a picture")
            return redirect(url_for("makegroup"))


        # Upload profile picture
        filename =  namegroup + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Upload info group into database groups
        db.execute("INSERT INTO groups (name_group, profile_picture) VALUES(:groupname, :profile_picture)", groupname=namegroup, profile_picture=filename)

        # Make session for the group
        session["group_id"] = ses_group(namegroup)

        # Put users into database user_groups
        db.execute("INSERT INTO user_groups (user_id, group_id) VALUES(:user_id, :group_id)", user_id=session["user_id"], group_id=session["group_id"])

        # Redirect to adding group members
        return redirect(url_for("addmember"))
    else:
        # Reload make group
        return render_template("makegroup.html")


@app.route("/addmember", methods=["GET", "POST"])
@login_required
def addmember():
    if request.method == "POST":
        # Get username and groupname from html
        add_members = request.form.get("add_members")
        groupname = request.form.get("groupname")

        # Check if user exist
        user = find_user(add_members)
        if user == []:
            flash("Username doesn't exist")
            return redirect(url_for("addmember"))

        # Get user id from helpers.py
        id_user = userse(add_members)

        # Get members of the group
        users = add_user(id_user)

        # Check user if it is already part of the group
        if len(users) > 0:
            users = users[0]["user_id"]
        else:
            users = ""

        # Notification if user is already part of the group
        if users == id_user:
            flash("This user is already part of the group")
            return redirect(url_for("addmember"))

        # Add member to the group
        db.execute("INSERT INTO user_groups (user_id, group_id) VALUES(:user_id, :group_id)", user_id=id_user, group_id=session["group_id"])

        # Get other members and put it in a list
        members = get_members()
        temporary = []
        temp = []
        for line in range(len(members)):
            member = members[line]["user_id"]
            temp.append(member)
        for row in temp:
            mem = db.execute("SELECT username FROM users WHERE id=:id_mem", id_mem=row)
            mem = mem[0]["username"]
            temporary.append([mem])

        # Reload page with updated list of members
        return render_template("addgroupmember.html", list_members = temporary)
    else:
        # Reload page
        return render_template("addgroupmember.html")


@app.route("/add_member", methods=["GET", "POST"])
@login_required
def add_member():
    if request.method == "POST":
        # Get information from add_member.html
        add_members = request.form.get("add_members")
        groupname = request.form.get("name")

        # Get link to redirect
        links = "https://ide50-britt1212.legacy.cs50.io:8080/groupview?value="
        links += groupname

        # Check username
        user = find_user(add_members)
        if user == []:
            flash("Username doesn't exist")
            return redirect(url_for("add_member"))

        # Get user id from helpers.py
        id_user = userse(add_members)

        # Get members of the group
        users = add_user(id_user)

        # Check if user is already part of the group
        if len(users) > 0:
            users = users[0]["user_id"]
        else:
            users = ""

        if users == id_user:
            flash("This user is already part of the group")
            return redirect(url_for("add_member"))

        # Add user to database
        db.execute("INSERT INTO user_groups (user_id, group_id) VALUES(:user_id, :group_id)", user_id=id_user, group_id=session["group_id"])

        # Redirect link
        return redirect(links)
    else:
        # Get name of the group and reload page
        url = request.url
        parsed = urlparse.urlparse(url)
        name = urlparse.parse_qs(parsed.query)['value']
        groupname = name[0]
        return render_template("add_member.html", name = groupname)


@app.route("/eventview", methods=["GET", "POST"])
@login_required
def eventview():
    event_id1 = db.execute("SELECT event_id FROM user_events WHERE user_id=:user_id", user_id=session["user_id"])
    if len(event_id1) <= 0:
        return redirect(url_for("noevent"))
    temporary = []
    temp = []
    for event in range(len(event_id1)):
        event_id = event_id1[event]["event_id"]
        temp.append(event_id)

    for number in temp:
        event_id = db.execute("SELECT event_name, event_picture FROM event_account WHERE event_id=:id_event", id_event=number)
        event_id1 = event_id[0]["event_name"]
        profilepic = event_id[0]["event_picture"]
        profilepicture = os.path.join(app.config["UPLOAD_FOLDER"], profilepic)
        temporary.append([event_id1, profilepicture])

    for rows in temporary:
        print(rows[0], rows[1])


    return render_template("eventview.html", list_event_id = temporary)

@app.route("/makeevent", methods=["GET", "POST"])
@login_required
def makeevent():
    if request.method == "POST":

        name_event = request.form.get("makeevent")
        if not request.form.get("makeevent"):
            return "insert eventname"


        if len(db.execute("SELECT * FROM event_account WHERE event_name=:event", event=name_event)) > 0:
            return "eventname already exists"


        # check if the post request has the file part
        file = request.files['file']
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)


        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
        filename =  name_event + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db.execute("INSERT INTO event_account (event_picture, event_name) VALUES(:event_picture, :event_name)", event_picture=filename, event_name = name_event)


        rows = db.execute("SELECT event_id FROM event_account WHERE event_name=:event", event=name_event)
        session["event"] = rows[0]["event_id"]

        db.execute("INSERT INTO user_events (user_id, event_id) VALUES(:user_id, :event_id)", user_id=session["user_id"], event_id=session["event"])
        return redirect(url_for("eventview"))
    else:
        return render_template("makeevent.html")



#GINO
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # Als POST kan
    if request.method == "POST":

        # username verzekeren
        if not request.form.get("username"):
            return apology("Must provide username!")

        # wachtwoord verzekeren
        elif not request.form.get("password"):
            return apology("must provide password!")

        # username database
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))


        # kijken of username uniek is en wachtwoord klopt
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password!")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page

        return redirect(url_for("groupfeed"))
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/groupfeed", methods=["GET", "POST"])
@login_required
def groupfeed():
    if request.method == "POST":
        # Get group id from helpers and check if you have a group
        groupl = get_group()
        if len(groupl) <= 0:
            return redirect(url_for("nogroup"))

        # Get all groups
        temporary = []
        temp = []
        for num in range(len(groupl)):
            groupe = groupl[num]["group_id"]
            groupname = groupnam(groupe)
            temp.append([groupe, groupname])

        # Get information about groups from helpers
        group = info_group(groupe)

        # Get all profilepictures
        for number in range(len(group)):
            user_id = group[number]["user_id"]

            # Get username from helpers
            user = usernam(user_id)

            # Select needed info
            username= user[0]["username"]
            profilepic = group[number]["picture"]
            comments = group[number]["comment"]
            profilepicture = os.path.join(app.config['UPLOAD_FOLDER'], profilepic)

            # Add info into list to return to html page
            temporary.append([username, profilepicture, comments])
        return render_template("groupview.html", list_picture=temporary, name_group=request.form.get("group"), group=temp)
    else:
        # Check if you are part of a group
        groupl = get_group()
        if len(groupl) <= 0:
            return redirect(url_for("nogroup"))

        # Load all groups with profilepic
        temporary = []
        temp = []
        for line in range(len(groupl)):
            group = groupl[line]["group_id"]
            temp.append(group)

        for number in temp:
            groupname = db.execute("SELECT name_group, profile_picture FROM groups WHERE group_id=:id_group", id_group=number)
            groupnamel = groupname[0]["name_group"]
            profilepic = groupname[0]["profile_picture"]
            profilepicture = os.path.join(app.config['UPLOAD_FOLDER'], profilepic)

            # Add info to list and reload page
            temporary.append([groupnamel, profilepicture])
        return render_template("groupfeed.html", list_group = temporary)


@app.route("/aboutus", methods=["GET", "POST"])
def aboutus():
    return render_template("aboutus.html")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    return render_template("settings.html")

@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "POST":

        password = request.form.get("newpassword")
        if len(password) < 8:
            return apology("Make sure your password is at least 8 letters")
        if re.search('[0-9]',password) is None:
            return apology("Make sure your password has a number in it")
        if re.search('[A-Z]',password) is None:
            return apology("Make sure your password has a capital letter in it")

        if request.form.get("newpassword") != request.form.get("newconfirmation"):
            return apology("Password and confirmation password were not the same!")
        if request.form.get("newpassword") == "":
            return apology("Please fill in your password!")
        if request.form.get("newconfirmation") == "":
            return apology("Please fill in your password!")
        elif not request.form.get("newpassword"):
            return apology("Please fill in your password!")
        elif not request.form.get("newconfirmation"):
            return apology("Please fill in your password!")

        wwupdate = db.execute("UPDATE users SET hash = :password WHERE id = :ide", ide=session["user_id"], password=pwd_context.hash(request.form.get("newpassword")))

        if not wwupdate:
            return apology("The password change could not happen")

        # gebruiker onthouden
        session["user_id"] = wwupdate

        # als alles doorstaan en voltooid is, bevestig registratie
        return redirect(url_for("settings"))

    return render_template("password.html")

@app.route("/profilepicture", methods=["GET", "POST"])
def profilepicture():
    if request.method == "POST":

            # check if the post request has the file part
        file = request.files['file']
        if 'file' not in request.files:
            flash('No picture uploaded')
            return render_template("profilepicture.html")


        nummer = str(session["user_id"])

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
        filename =  nummer + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db.execute("UPDATE users SET profilepicture = :profilepicture WHERE id = :gebruiksersnaam", profilepicture=filename, gebruikersnaam=session["user_id"])
        return render_template("settings.html")
    else:
        return render_template("profilepicture.html")

@app.route("/logout")
def logout():
    # vergeet de id
    session.clear()

    # terug bij af
    return redirect(url_for("index"))


@app.route('/home/ubuntu/workspace/picus2.0/upload/<path:path>')
def show(path):
    return send_from_directory('upload', path)


@app.route("/groupview")
@login_required
def groupview():
    # Get information from url query
    url = request.url
    parsed = urlparse.urlparse(url)
    name = urlparse.parse_qs(parsed.query)['value']

    # Get group id from helpers
    group_idd = ses_group(name)
    session["group_id"] = group_idd

    # Get information form helpers
    group = pics(group_idd)

    # Add all info to a list
    temporary = []
    for number in range(len(group)):
        temp = []
        tem = []
        user_id = group[number]["user_id"]

        # Get username from helpers
        username = nam(user_id)

        # Select needed info
        profilepic = group[number]["picture"]
        comments = group[number]["comment"]
        like = group[number]["like"]
        tim = group[number]["time"]
        profilepicture = os.path.join(app.config['UPLOAD_FOLDER'], profilepic)

        # Select comments from a picture and put it in a list
        comment_group = comm_group(profilepic)

        # if len(comment_group) == 0:
        #     temp.append(["", ""])
        # else:
        for num in range(len(comment_group)):
            us = comment_group[num]["user_id"]

            # Get username from helpers
            usern = nam(us)
            com = comment_group[num]["comment"]
            temp.append([usern, com])


        # gif = gif_group(profilepic)
        # for number in range(len(gif)):
        #     us = comment_group[num]["user_id"]

        #     # Get username from helpers
        #     usern = nam(us)
        #     com = comment_group[num]["comment"]
        #     tem.append([usern, com])

        temporary.append([username, profilepicture, comments, profilepic, like, temp, tim])

    members = db.execute("SELECT user_id FROM user_groups WHERE group_id = :goh", goh=session['group_id'])
    ventjes = []

    for person in members:
        pers=db.execute("SELECT username FROM users WHERE id =:sjala", sjala=members[person]['user_id'])
        ventjes.append(pers)

    # return to html page with required information
    return render_template("groupview.html", list_picture=temporary, group=name[0], ventjes=ventjes)


@app.route("/upload_photo", methods=["GET", "POST"])
@login_required
def upload_photo():
    if request.method=="POST":
        # Get groupname from helpers
        group = get_nam_group()

        # Get comment from html page
        comments = request.form.get("comment")

        # Check if user wrote a comment
        if comments == "":
            flash("You need to write a comment")
            return redirect(url_for("upload_photo"))

        # Check if uploaded file is an actual picture
        file = request.files['file']
        if not allowed_file(file.filename):
            flash("This is not a picture")
            return redirect(url_for("upload_photo"))

        # Add picture to the server with special name
        filename =  str(session["user_id"]) + "_" + str(session["group_id"]) + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Add picture with comment to database
        db.execute("INSERT INTO picture_group (user_id, group_id, picture, like, comment) VALUES(:user_id, :group_id, :picture, :like, :comment)",
                   user_id=session["user_id"], picture=filename, group_id=session["group_id"], like=0, comment=comments)

        # Get link to redirect to groupview
        links = "https://ide50-britt1212.legacy.cs50.io:8080/groupview?value="
        links += group
        return redirect(links)
    else:
        # Reload page
        return render_template("upload_photo.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    check = 0
    zoekopdracht=request.form.get("search")
    zoeken = db.execute("SELECT * FROM event_account WHERE event_name LIKE :zoekopdracht ORDER BY event_name ASC", zoekopdracht=str(zoekopdracht)+"%")
    resultaten = []

    for row in zoeken:
        resultaten.append(row['event_name'])

    if request.form.get("search") == "":
        return render_template("search.html", zoekopdracht=zoekopdracht, resultaten=resultaten, check=0)
    if not request.form.get("search"):
        return render_template("search.html", zoekopdracht=zoekopdracht, resultaten=resultaten, check=0)


    return render_template("search.html", zoekopdracht=zoekopdracht, resultaten=resultaten, check=1)





@app.route("/eventphoto", methods=["GET", "POST"])
@login_required
def eventphoto():
    if request.method == 'POST':

        event_name = db.execute("SELECT event_name FROM event_account WHERE event_id=:event", event=session["event_id"])
        event = event_name[0]["event_name"]

        caption = request.form.get("caption")

        file = request.files['file']
        if not allowed_file(file.filename):
            return "This is not a picture"

        filename =  str(session["user_id"]) + "_" + str(session["event_id"]) + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db.execute("INSERT INTO event_feed (images, likes, dislikes, comments, caption, user_id, event_id) VALUES(:images, :likes, :dislikes, :comments, :caption, :user_id, :event_id)"
                   ,images=filename, likes = 0, dislikes = 0, comments = "hi does this work?", caption = caption, user_id = session["user_id"], event_id = session["event_id"])

        return render_template("eventphoto.html", event = event_name[0]["event_name"])
    else:
        return render_template("eventphoto.html")

# @app.route("/get_group/", methods=['POST'])
# def get_group():
#     f=request.form.get("groupname")
#     group = db.execute("SELECT group_id FROM groups WHERE name_group=:name_group", name_group=f)
#     group_idd = group[0]["group_id"]
#     return group_idd

@app.route("/get_event/", methods=['POST'])
def get_event():
    f=request.form.get("eventname")
    event = db.execute("SELECT event_id FROM event_account WHERE event_name=:name_event", name_event=f)
    event_idd = event[0]["event_id"]
    return event_idd

@app.route('/eventfeed/')
def eventfeed():
    url = request.url
    parsed = urlparse.urlparse(url)
    name = urlparse.parse_qs(parsed.query)['value']
    if session.get("user_id") is None:
        flash("Login or make an account to use more functions")
    event_idd = db.execute("SELECT event_id FROM event_account WHERE event_name=:event", event=name)
    event_idd = event_idd[0]["event_id"]
    session["event_id"] = event_idd
    temporary = []

    event = db.execute("SELECT user_id, images, caption, likes, dislikes, comments, time FROM event_feed WHERE event_id=:id_event", id_event=event_idd)

    for number in range(len(event)):
        temp = []
        ex_temp = []
        user_id = event[number]["user_id"]

        username = nam(user_id)
        profilepicevent = event[number]["images"]
        captions = event[number]["caption"]
        comments = event[number]["comments"]
        like = event[number]["likes"]
        dislike = event[number]["dislikes"]
        tim = event[number]["time"]
        profilepicture = os.path.join(app.config['UPLOAD_FOLDER'], profilepicevent)

        comment_event = comm_event(profilepicevent)
        count = 0

        for num in range(len(comment_event)):
            us = comment_event[num]["user_id"]
            # Get username from helpers
            usern = nam(us)
            com = comment_event[num]["comment"]
            temp.append([usern, com])
            if count < 6:
                ex_temp.append([usern, com])
            count += 1
        temporary.append([username, profilepicture, captions, profilepicevent, like, temp, tim, ex_temp])

    return render_template("eventfeed.html", list_picture=temporary, event=name[0], urls=url)


@app.route('/leave_group/')
@login_required
def leave_group():
    # Delete group
    db.execute("DELETE FROM user_groups WHERE user_id = :user_id AND group_id = :group_id", user_id=session["user_id"], group_id = session["group_id"])

    # Check if group is empty if true delete the group from database
    check = check_users()
    if check == []:
         db.execute("DELETE FROM groups WHERE group_id = :group_id", group_id = session["group_id"])

    # redirect to groupfeed
    return redirect(url_for("groupfeed"))


@app.route('/like_photo/')
@login_required
def like_photo():
    # Get info from url query
    url = request.url
    parsed = urlparse.urlparse(url)
    name = urlparse.parse_qs(parsed.query)['value']
    view = urlparse.parse_qs(parsed.query)['q']

    # Link to redirect
    link = "https://ide50-britt1212.legacy.cs50.io:8080/groupview?value="
    link += view[0]

    # Insert like into database
    db.execute("INSERT INTO like_group (user_id, picture_user, groupname) VALUES(:user_id, :picture_user, :groupname)", user_id=session["user_id"], picture_user=name, groupname=view)

    # Get info about like
    check = like_check(name, view)

    # Check if user already liked the picture
    check_id = check[0]["id"]
    if len(check) != 1:
        db.execute("DELETE FROM like_group WHERE user_id=:user_id AND picture_user=:picture_user AND groupname=:groupname AND id=:id_check", id_check = check_id, user_id=session["user_id"], picture_user=name, groupname=view)
        flash("You have already liked this picture")
        return redirect(link)
    else:
        # Update likes
        likes = get_like(name)
        db.execute("UPDATE picture_group SET like =:like WHERE picture=:picture_user AND group_id=:groupname", like = likes + 1, picture_user=name, groupname=session["group_id"])

    # Redirect to adjusted link
    return redirect(link)


@app.route('/dislike_photo/')
@login_required
def dislike_photo():
    # Get info from url query
    url = request.url
    parsed = urlparse.urlparse(url)
    name = urlparse.parse_qs(parsed.query)['value']
    view = urlparse.parse_qs(parsed.query)['q']

    # Link to redirect
    link = "https://ide50-britt1212.legacy.cs50.io:8080/groupview?value="
    link += view[0]

    # Insert dislike into database
    db.execute("INSERT INTO like_group (user_id, picture_user, groupname) VALUES(:user_id, :picture_user, :groupname)", user_id=session["user_id"], picture_user=name, groupname=view)

    # Get info about like
    check = like_check(name, view)

    # Check if user already liked the photo
    check_id = check[0]["id"]
    if len(check) != 1:
        db.execute("DELETE FROM like_group WHERE user_id=:user_id AND picture_user=:picture_user AND groupname=:groupname AND id=:id_check", id_check = check_id, user_id=session["user_id"], picture_user=name, groupname=view)
        flash("You have already liked this picture")
        return redirect(link)
    else:
        # Update dislikes
        likes = get_like(name)
        db.execute("UPDATE picture_group SET like =:like WHERE user_id=:user_id AND picture=:picture_user AND group_id=:groupname", like = likes - 1, user_id=session["user_id"], picture_user=name, groupname=session["group_id"])

    # Redirect to adjusted link
    return redirect(link)


@app.route('/bin/')
@login_required
def bin():
    # Get info from url query
    url = request.url
    parsed = urlparse.urlparse(url)
    name = urlparse.parse_qs(parsed.query)['value']
    view = urlparse.parse_qs(parsed.query)['q']

    # Redirect link
    link_back = "https://ide50-britt1212.legacy.cs50.io:8080/groupview?value="
    link_back += view[0]

    # Check if an authorized person deletes the picture
    user = bin_check(name)
    if session["user_id"] != user:
        flash("Only the person who posted the picture can delete the picture")
        return redirect(link_back)

    # Delete picture
    db.execute("DELETE FROM picture_group WHERE user_id=:user_id AND picture=:picture_user AND group_id=:groupname", user_id=session["user_id"], picture_user=name, groupname=session["group_id"])

    # Redirect to groupview
    return redirect(link_back)

@app.route('/eventbin/')
@login_required
def eventbin():
    # Get info from url query
    url = request.url
    parsed = urlparse.urlparse(url)
    name = urlparse.parse_qs(parsed.query)['value']
    view = urlparse.parse_qs(parsed.query)['q']

    # Delete picture
    db.execute("DELETE FROM event_feed WHERE user_id=:user_id AND images=:image_user AND event_id=:eventname", user_id=session["user_id"], image_user=name, eventname=session["event_id"])

    # Redirect link
    link_back = "https://ide50-a12216321.legacy.cs50.io:8080/eventfeed?value="
    link_back += view[0]
    return redirect(link_back)

@app.route("/username", methods=["GET", "POST"])
@login_required
def username():
    if request.method == "POST":

        if request.form.get("newusername") != request.form.get("newusernameconfirmation"):
            return apology("Username and confirmation username were not the same!")
        if request.form.get("newusername") == "":
            return apology("Please fill in your username!")
        if request.form.get("newusernameconfirmation") == "":
            return apology("Please fill in your username!")
        elif not request.form.get("newusername"):
            return apology("Please fill in your username!")
        elif not request.form.get("newusernameconfirmation"):
            return apology("Please fill in your username!")

        usupdate = db.execute("UPDATE users SET username = :username WHERE id = :ide", ide=session["user_id"], username=request.form.get("newusername"))

        if not usupdate:
            return apology("The username change could not happen")

        # gebruiker onthouden
        session["user_id"] = usupdate

        # als alles doorstaan en voltooid is, bevestig registratie
        return redirect(url_for("settings"))


    return redirect(link)

@app.route('/event_like_photo/')
@login_required
def event_like_photo():
    # Get info from url query
    url = request.url
    parsed = urlparse.urlparse(url)
    name = urlparse.parse_qs(parsed.query)['value']
    view = urlparse.parse_qs(parsed.query)['q']

    # Link to redirect
    link = "https://ide50-a12216321.legacy.cs50.io:8080/eventfeed?value="
    link += view[0]

    # Insert like into database
    db.execute("INSERT INTO like_event (user_id, picture_user, eventname) VALUES(:user_id, :picture_user, :eventname)", user_id=session["user_id"], picture_user=name, eventname=view)

    # Get info about like
    check = event_like_check(name, view)

    # Check if user already liked the picture
    check_id = check[0]["id"]
    if len(check) != 1:
        db.execute("DELETE FROM like_event WHERE user_id=:user_id AND picture_user=:picture_user AND eventname=:eventname AND id=:id_check", id_check = check_id, user_id=session["user_id"], picture_user=name, eventname=view)
        flash("You have already liked this picture")
        return redirect(link)
    else:
        # Update likes
        likes = event_get_like(name)
        db.execute("UPDATE event_feed SET likes =:like WHERE user_id=:user_id AND images=:picture_user AND event_id=:eventname", like = likes + 1, user_id=session["user_id"], picture_user=name, eventname=session["event_id"])

    # Redirect to adjusted link
    return redirect(link)

@app.route('/event_dislike_photo/')
@login_required
def event_dislike_photo():
    # Get info from url query
    url = request.url
    parsed = urlparse.urlparse(url)
    name = urlparse.parse_qs(parsed.query)['value']
    view = urlparse.parse_qs(parsed.query)['q']

    # Link to redirect
    link = "https://ide50-a12216321.legacy.cs50.io:8080/eventfeed?value="
    link += view[0]

    # Insert dislike into database
    db.execute("INSERT INTO like_event (user_id, picture_user, eventname) VALUES(:user_id, :picture_user, :eventname)", user_id=session["user_id"], picture_user=name, eventname=view)

    # Get info about like
    check = event_like_check(name, view)

    # Check if user already liked the photo
    check_id = check[0]["id"]
    if len(check) != 1:
        db.execute("DELETE FROM like_event WHERE user_id=:user_id AND picture_user=:picture_user AND eventpname=:eventname AND id=:id_check", id_check = check_id, user_id=session["user_id"], picture_user=name, eventname=view)
        flash("You have already liked this picture")
        return redirect(link)
    else:
        # Update dislikes
        likes = get_like(name)
        db.execute("UPDATE event_feed SET likes =:like WHERE user_id=:user_id AND images=:picture_user AND event_id=:eventname", like = likes - 1, user_id=session["user_id"], picture_user=name, eventname=session["event_id"])

    # Redirect to adjusted link
    return redirect(link)


@app.route('/comment/')
@login_required
def comment():
    # Get info from url query
    url = request.url
    parsed = urlparse.urlparse(url)
    comm = urlparse.parse_qs(parsed.query)['comments']
    pica = urlparse.parse_qs(parsed.query)['pic']

    # Insert comment into database
    db.execute("INSERT INTO comment_group (user_id, group_id, picture, comment) VALUES(:user_id, :group_id, :picture, :comment)", user_id=session["user_id"], group_id = session["group_id"], picture=pica, comment=comm)

    # Get groupname to redirect
    groupnamel = get_nam_group()
    link = "https://ide50-britt1212.legacy.cs50.io:8080/groupview?value="
    link += groupnamel
    return redirect(link)

@app.route("/noevent")
@login_required
def noevent():
    return render_template("noevent.html")

@app.route("/nogroup")
@login_required
def nogroup():
    return render_template("nogroup.html")


@app.route("/add_gif")
@login_required
def add_gif():
    url = request.url
    parsed = urlparse.urlparse(url)
    comm = urlparse.parse_qs(parsed.query)['value']
    pica = urlparse.parse_qs(parsed.query)['q']

    db.execute("INSERT INTO comment_group (user_id, group_id, picture, comment) VALUES(:user_id, :group_id, :picture, :comment)", user_id=session["user_id"], group_id = session["group_id"], picture=pica, comment=comm)

    # Get groupname to redirect
    groupnamel = get_nam_group()
    link = "https://ide50-britt1212.legacy.cs50.io:8080/groupview?value="
    link += groupnamel
    return redirect(link)

@app.route('/eventcomment/')
@login_required
def eventcomment():
    # Get info from url query
    url = request.url
    parsed = urlparse.urlparse(url)
    comm = urlparse.parse_qs(parsed.query)['comments']
    pica = urlparse.parse_qs(parsed.query)['pic']

    # Insert comment into database
    db.execute("INSERT INTO comment_event (user_id, event_id, picture, comment) VALUES(:user_id, :event_id, :picture, :comment)", user_id=session["user_id"], event_id = session["event_id"], picture=pica, comment=comm)

    # Get groupname to redirect
    eventnamel = get_nam_event()
    link = "https://ide50-a12216321.legacy.cs50.io:8080/eventfeed?value="
    link += eventnamel
    return redirect(link)
