from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_from_directory, jsonify
from flask_session import Session
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
import re
from pprint import pprint
import urllib.parse as urlparse
from django.utils.deprecation import MiddlewareMixin
import urllib
import json
import urllib.parse as urlparse
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


@app.route("/")
def index():
    """The index of the website"""
    # If user logged in, show groupfeed
    if request.method == "POST":
        return render_template("groupfeed.html", user_id=session["user_id"])

    # If user new, render the startscreen
    if request.method == "GET":
        return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if information is right and valid
        if not request.form.get("email"):
            flash("Please fill in your email adress!")
            return render_template("register.html")

        if not request.form.get("username"):
            flash("Please fill in your username!")
            return render_template("register.html")

        if request.form.get("password") != request.form.get("confirmation"):
            flash("Password and confirmation password were not the same!")
            return render_template("register.html")

        if request.form.get("password") == "":
            flash("Please fill in your password!")
            return render_template("register.html")

        elif not request.form.get("password"):
            flash("Please fill in your password!")
            return render_template("register.html")

        elif not request.form.get("confirmation"):
            flash("Please fill in your password!")
            return render_template("register.html")

        # Check if username exists
        username = request.form.get("username")
        if len(select_users_with_name(username)) > 0:
            flash("username already exists")
            return render_template("register.html")

        # register
        geregistreerd = db.execute("INSERT INTO users (email, username, hash) VALUES(:email, :username, :password)", email=request.form.get(
            "email"), username=request.form.get("username"), password=pwd_context.hash(request.form.get("password")))
        # if not possible, fill in form again
        if not geregistreerd:
            flash("The registration could not happen")
            return render_template("register.html")

        # Remember user
        session["user_id"] = geregistreerd

        # Confirm registration
        return redirect(url_for("groupfeed"))

    # When no POST, render register again
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
            return render_template("makegroup.html")

        # Get profile picture
        file = request.files['file']

        # Check if picture is uploaded
        if file == "":
            flash("Upload photo")
            return render_template("makegroup.html")

        if not allowed_file(file.filename):
            flash("This is not a picture")
            return render_template("makegroup.html")

        # Upload profile picture
        filename = namegroup + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Upload info group into database groups
        db.execute("INSERT INTO groups (name_group, profile_picture) VALUES(:groupname, :profile_picture)",
                   groupname=namegroup, profile_picture=filename)

        # Make session for the group
        session["group_id"] = ses_group(namegroup)

        # Put users into database user_groups
        db.execute("INSERT INTO user_groups (user_id, group_id) VALUES(:user_id, :group_id)",
                   user_id=session["user_id"], group_id=session["group_id"])

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
            return render_template("addgroupmember.html")

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
            return render_template("addgroupmember.html")

        # Add member to the group
        db.execute("INSERT INTO user_groups (user_id, group_id) VALUES(:user_id, :group_id)",
                   user_id=id_user, group_id=session["group_id"])

        # Get other members and put it in a list
        members = get_members()
        temporary = []
        temp = []
        for line in range(len(members)):
            member = members[line]["user_id"]
            temp.append(member)
        for row in temp:
            mem = get_username_by_id(row)
            mem = mem[0]["username"]
            temporary.append([mem])

        # Reload page with updated list of members
        return render_template("addgroupmember.html", list_members=temporary)
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

        # Link to redirect
        urlBase = request.url_root
        link = urlBase + 'groupview?value='
        link += groupname

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
        db.execute("INSERT INTO user_groups (user_id, group_id) VALUES(:user_id, :group_id)",
                   user_id=id_user, group_id=session["group_id"])

        # Redirect link
        return redirect(link)
    else:
        # Get name of the group and reload page
        url = request.url
        parsed = urlparse.urlparse(url)
        name = urlparse.parse_qs(parsed.query)['value']
        groupname = name[0]
        return render_template("add_member.html", name=groupname)


@app.route("/eventview", methods=["GET", "POST"])
@login_required
def eventview():
    event_id1 = get_event_id()

    # Check if user has an event yet
    if len(event_id1) <= 0:
        return redirect(url_for("noevent"))

    # Get all the info and upload it to html page
    temporary = []
    temp = []
    for event in range(len(event_id1)):
        event_id = event_id1[event]["event_id"]
        temp.append(event_id)

    for number in temp:
        event_id = get_event_info(number)
        event_id1 = event_id[0]["event_name"]
        profilepic = event_id[0]["event_picture"]
        profilepicture = os.path.join(app.config["UPLOAD_FOLDER"], profilepic)
        temporary.append([event_id1, profilepicture])

    for rows in temporary:
        print(rows[0], rows[1])

    return render_template("eventview.html", list_event_id=temporary)


@app.route("/makeevent", methods=["GET", "POST"])
@login_required
def makeevent():
    if request.method == "POST":
        # Check if the field is not empty
        name_event = request.form.get("makeevent")
        if not request.form.get("makeevent"):
            return "insert eventname"

        if len(get_event_name(name_event)) > 0:
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
        filename = name_event + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db.execute("INSERT INTO event_account (event_picture, event_name) VALUES(:event_picture, :event_name)",
                   event_picture=filename, event_name=name_event)

        rows = get_event_nameid(name_event)
        session["event"] = rows[0]["event_id"]

        db.execute("INSERT INTO user_events (user_id, event_id) VALUES(:user_id, :event_id)",
                   user_id=session["user_id"], event_id=session["event"])
        return redirect(url_for("eventview"))
    else:
        return render_template("makeevent.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # Forget any user_id
    session.clear()

    # Als POST kan
    if request.method == "POST":

        # Confirm username
        if not request.form.get("username"):
            flash("Must provide username!")
            return render_template("login.html")

        # Confirm password
        elif not request.form.get("password"):
            flash("must provide password!")
            return render_template("login.html")

        # username database
        username = request.form.get("username")
        rows = select_users_with_name(username)

        # Check if username unique and valid
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            flash("invalid username and/or password!")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page

        return redirect(url_for("groupfeed"))

    # Else if user reached route via GET (as by clicking a link or via redirect)
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
            username = user[0]["username"]
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
            groupname = name_pic_group_by_group_id(number)
            groupnamel = groupname[0]["name_group"]
            profilepic = groupname[0]["profile_picture"]
            profilepicture = os.path.join(app.config['UPLOAD_FOLDER'], profilepic)

            # Add info to list and reload page
            temporary.append([groupnamel, profilepicture])
        return render_template("groupfeed.html", list_group=temporary)


@app.route("/aboutus", methods=["GET", "POST"])
def aboutus():
    # Go to about us html
    return render_template("aboutus.html")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    # Go to settings html
    return render_template("settings.html")


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "POST":
        # Tests if password is correct and valid
        password = request.form.get("newpassword")
        if len(password) < 8:
            flash("Make sure your password is at least 8 letters")
            return render_template("password.html")

        if re.search('[0-9]', password) is None:
            flash("Make sure your password has a number in it")
            return render_template("password.html")

        if re.search('[A-Z]', password) is None:
            flash("Make sure your password has a capital letter in it")
            return render_template("password.html")

        if request.form.get("newpassword") != request.form.get("newconfirmation"):
            flash("Password and confirmation password were not the same!")
            return render_template("password.html")

        if request.form.get("newpassword") == "":
            flash("Please fill in your password!")
            return render_template("password.html")

        if request.form.get("newconfirmation") == "":
            flash("Please fill in your password!")
            return render_template("password.html")

        elif not request.form.get("newpassword"):
            flash("Please fill in your password!")
            return render_template("password.html")

        elif not request.form.get("newconfirmation"):
            flash("Please fill in your password!")
            return render_template("password.html")

        # Update password
        wwupdate = db.execute("UPDATE users SET hash = :password WHERE id = :ide",
                              ide=session["user_id"], password=pwd_context.hash(request.form.get("newpassword")))

        # If not possible, try again
        if not wwupdate:
            flash("The password change could not happen")
            return render_template("password.html")

        # Remember user
        session["user_id"] = wwupdate

        # If everything succeeded, return to settings
        return redirect(url_for("settings"))

    if request.method == "GET":
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
        filename = nummer + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db.execute("UPDATE users SET profilepicture = :profilepicture WHERE id = :gebruiksersnaam",
                   profilepicture=filename, gebruikersnaam=session["user_id"])
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
    # Get photo from server
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

        temporary.append([username, profilepicture, comments, profilepic, like, temp, tim])

    # Get other members and put it in a list
    members = get_members()
    print(members)
    list_temporary = []
    list_temp = []
    for line in range(len(members)):
        member = members[line]["user_id"]
        list_temp.append(member)
    for row in list_temp:
        mem = get_memb(row)
        mem = mem[0]["username"]
        list_temporary.append([mem])
    print(list_temporary)
    # return to html page with required information
    return render_template("groupview.html", list_picture=temporary, group=name[0], list_members=list_temporary)


@app.route("/upload_photo", methods=["GET", "POST"])
@login_required
def upload_photo():
    if request.method == "POST":
        # Get groupname from helpers
        group = get_nam_group()

        # Get comment from html page
        comments = request.form.get("comment")

        # Check if user wrote a comment
        if comments == "":
            flash("You need to write a comment")
            return render_template("upload_photo.html")

        # Check if uploaded file is an actual picture
        file = request.files['file']
        if not allowed_file(file.filename):
            flash("This is not a picture")
            return render_template("upload_photo.html")

        # Add picture to the server with special name
        filename = str(session["user_id"]) + "_" + str(session["group_id"]) + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Add picture with comment to database
        db.execute("INSERT INTO picture_group (user_id, group_id, picture, like, comment) VALUES(:user_id, :group_id, :picture, :like, :comment)",
                   user_id=session["user_id"], picture=filename, group_id=session["group_id"], like=0, comment=comments)

        # Get link to redirect to groupview
        # Link to redirect
        urlBase = request.url_root
        link = urlBase + 'groupview?value='
        link += group
        return redirect(link)
    else:
        # Reload page
        return render_template("upload_photo.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    # Search for events and show results
    check = 0
    zoekopdracht = request.form.get("search")
    zoeken = search_results(zoekopdracht)
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
        eventlink = get_nam_event()

        caption = request.form.get("caption")

        # Check if uploaded file is an picture
        file = request.files['file']
        if not allowed_file(file.filename):
            return "This is not a picture"

        filename = str(session["user_id"]) + "_" + str(session["event_id"]) + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db.execute("INSERT INTO event_feed (images, likes, dislikes, comments, caption, user_id, event_id) VALUES(:images, :likes, :dislikes, :comments, :caption, :user_id, :event_id)",
                   images=filename, likes=0, dislikes=0, comments="hi does this work?", caption=caption, user_id=session["user_id"], event_id=session["event_id"])

        # Link to redirect
        urlBase = request.url_root
        link = urlBase + 'eventfeed?value='
        link += eventlink
        return redirect(link)
    else:
        return render_template("eventphoto.html")


@app.route("/get_event/", methods=['POST'])
def get_event():
    # get event id
    eventform = request.form.get("eventname")
    event = get_event_id_by_name(eventform)
    event_idd = event[0]["event_id"]
    return event_idd


@app.route('/eventfeed/')
def eventfeed():
    # Get info from url
    url = request.url
    parsed = urlparse.urlparse(url)
    eventform = urlparse.parse_qs(parsed.query)['value']
    if session.get("user_id") is None:
        flash("Login or make an account to use more functions")

    event_idd = get_event_id_by_name(eventform)
    event_idd = event_idd[0]["event_id"]
    session["event_id"] = event_idd
    temporary = []
    event = get_eventfeed_info(event_idd)

    # Add data from database in a list to upload to html page
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

    return render_template("eventfeed.html", list_picture=temporary, event=eventform[0], urls=url)


@app.route('/leave_group/')
@login_required
def leave_group():
    # Delete group
    db.execute("DELETE FROM user_groups WHERE user_id = :user_id AND group_id = :group_id",
               user_id=session["user_id"], group_id=session["group_id"])

    # Check if group is empty if true delete the group from database
    check = check_users()
    if check == []:
        db.execute("DELETE FROM groups WHERE group_id = :group_id", group_id=session["group_id"])

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
    urlBase = request.url_root
    link = urlBase + 'groupview?value='
    link += view[0]

    # Insert like into database
    db.execute("INSERT INTO like_group (user_id, picture_user, groupname) VALUES(:user_id, :picture_user, :groupname)",
               user_id=session["user_id"], picture_user=name, groupname=view)

    # Get info about like
    check = like_check(name, view)

    # Check if user already liked the picture
    check_id = check[0]["id"]
    if len(check) != 1:
        db.execute("DELETE FROM like_group WHERE user_id=:user_id AND picture_user=:picture_user AND groupname=:groupname AND id=:id_check",
                   id_check=check_id, user_id=session["user_id"], picture_user=name, groupname=view)
        flash("You have already liked this picture")
        return redirect(link)
    else:
        # Update likes
        likes = get_like(name)
        db.execute("UPDATE picture_group SET like =:like WHERE picture=:picture_user AND group_id=:groupname",
                   like=likes + 1, picture_user=name, groupname=session["group_id"])

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
    urlBase = request.url_root
    link = urlBase + 'groupview?value='
    link += view[0]

    # Insert dislike into database
    db.execute("INSERT INTO like_group (user_id, picture_user, groupname) VALUES(:user_id, :picture_user, :groupname)",
               user_id=session["user_id"], picture_user=name, groupname=view)

    # Get info about like
    check = like_check(name, view)

    # Check if user already liked the photo
    check_id = check[0]["id"]
    if len(check) != 1:
        db.execute("DELETE FROM like_group WHERE user_id=:user_id AND picture_user=:picture_user AND groupname=:groupname AND id=:id_check",
                   id_check=check_id, user_id=session["user_id"], picture_user=name, groupname=view)
        flash("You have already liked this picture")
        return redirect(link)
    else:
        # Update dislikes
        likes = get_like(name)
        db.execute("UPDATE picture_group SET like =:like WHERE user_id=:user_id AND picture=:picture_user AND group_id=:groupname",
                   like=likes - 1, user_id=session["user_id"], picture_user=name, groupname=session["group_id"])

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

    # Link to redirect
    urlBase = request.url_root
    link_back = urlBase + 'groupview?value='
    link_back += view[0]

    # Check if an authorized person deletes the picture
    user = bin_check(name)
    if session["user_id"] != user:
        flash("Only the person who posted the picture can delete the picture")
        return redirect(link_back)

    # Delete picture
    db.execute("DELETE FROM picture_group WHERE user_id=:user_id AND picture=:picture_user AND group_id=:groupname",
               user_id=session["user_id"], picture_user=name, groupname=session["group_id"])

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
    db.execute("DELETE FROM event_feed WHERE user_id=:user_id AND images=:image_user AND event_id=:eventname",
               user_id=session["user_id"], image_user=name, eventname=session["event_id"])

    # Redirect link
    urlBase = request.url_root
    link_back = urlBase + 'eventfeed?value='
    link_back += view[0]
    return redirect(link_back)


@app.route("/username", methods=["GET", "POST"])
@login_required
def username():
    if request.method == "POST":
        # Check if the username filled in is correct
        if request.form.get("newusername") != request.form.get("newusernameconfirmation"):
            flash("Username and confirmation username were not the same!")
            return redirect(url_for("settings"))

        if request.form.get("newusername") == "":
            flash("Please fill in your username!")
            return redirect(url_for("settings"))

        if request.form.get("newusernameconfirmation") == "":
            flash("Please fill in your username!")
            return redirect(url_for("settings"))

        elif not request.form.get("newusername"):
            flash("Please fill in your username!")
            return redirect(url_for("settings"))

        elif not request.form.get("newusernameconfirmation"):
            flash("Please fill in your username!")
            return redirect(url_for("settings"))

        usupdate = db.execute("UPDATE users SET username = :username WHERE id = :ide",
                              ide=session["user_id"], username=request.form.get("newusername"))

        if not usupdate:
            flash("The username change could not happen")
            return redirect(url_for("settings"))

        # gebruiker onthouden
        session["user_id"] = usupdate

        # als alles doorstaan en voltooid is, bevestig registratie
        return redirect(url_for("settings"))

    return render_template("username.html")


@app.route('/event_like_photo/')
@login_required
def event_like_photo():
    # Get info from url query
    url = request.url
    parsed = urlparse.urlparse(url)
    name = urlparse.parse_qs(parsed.query)['value']
    view = urlparse.parse_qs(parsed.query)['q']

    # Link to redirect
    urlBase = request.url_root
    link = urlBase + 'eventfeed?value='
    link += view[0]

    # Insert like into database
    db.execute("INSERT INTO like_event (user_id, picture_user, eventname) VALUES(:user_id, :picture_user, :eventname)",
               user_id=session["user_id"], picture_user=name, eventname=view)

    # Get info about like
    check = event_like_check(name, view)

    # Check if user already liked the picture
    check_id = check[0]["id"]
    if len(check) != 1:
        db.execute("DELETE FROM like_event WHERE user_id=:user_id AND picture_user=:picture_user AND eventname=:eventname AND id=:id_check",
                   id_check=check_id, user_id=session["user_id"], picture_user=name, eventname=view)
        flash("You have already liked this picture")
        return redirect(link)
    else:
        # Update likes
        likes = event_get_like(name)
        db.execute("UPDATE event_feed SET likes =:like WHERE user_id=:user_id AND images=:picture_user AND event_id=:eventname",
                   like=likes + 1, user_id=session["user_id"], picture_user=name, eventname=session["event_id"])

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
    urlBase = request.url_root
    link = urlBase + 'eventfeed?value='
    link += view[0]

    # Insert dislike into database
    db.execute("INSERT INTO like_event (user_id, picture_user, eventname) VALUES(:user_id, :picture_user, :eventname)",
               user_id=session["user_id"], picture_user=name, eventname=view)

    # Get info about like
    check = event_like_check(name, view)

    # Check if user already liked the photo
    check_id = check[0]["id"]
    if len(check) != 1:
        db.execute("DELETE FROM like_event WHERE user_id=:user_id AND picture_user=:picture_user AND eventname=:eventname AND id=:id_check",
                   id_check=check_id, user_id=session["user_id"], picture_user=name, eventname=view)
        flash("You have already liked this picture")
        return redirect(link)
    else:
        # Update dislikes
        likes = get_like(name)
        db.execute("UPDATE event_feed SET likes =:like WHERE user_id=:user_id AND images=:picture_user AND event_id=:eventname",
                   like=likes - 1, user_id=session["user_id"], picture_user=name, eventname=session["event_id"])

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
    db.execute("INSERT INTO comment_group (user_id, group_id, picture, comment) VALUES(:user_id, :group_id, :picture, :comment)",
               user_id=session["user_id"], group_id=session["group_id"], picture=pica, comment=comm)

    # Get groupname to redirect
    groupnamel = get_nam_group()

    # Link to redirect
    urlBase = request.url_root
    link = urlBase + 'groupview?value='
    link += groupnamel
    return redirect(link)


@app.route("/noevent")
@login_required
def noevent():
    # Go to no event html
    return render_template("noevent.html")


@app.route("/nogroup")
@login_required
def nogroup():
    # Go to no group html
    return render_template("nogroup.html")


@app.route("/add_gif")
@login_required
def add_gif():
    # Get info from url
    url = request.url
    parsed = urlparse.urlparse(url)
    comm = urlparse.parse_qs(parsed.query)['value']
    pica = urlparse.parse_qs(parsed.query)['q']

    # Add data into database
    db.execute("INSERT INTO comment_group (user_id, group_id, picture, comment) VALUES(:user_id, :group_id, :picture, :comment)",
               user_id=session["user_id"], group_id=session["group_id"], picture=pica, comment=comm)

    # Get groupname to redirect
    groupnamel = get_nam_group()

    # Link to redirect
    urlBase = request.url_root
    link = urlBase + 'groupview?value='
    link += groupnamel
    return redirect(link)


@app.route('/eventcomment/')
@login_required
def eventcomment():
    # Get groupname to redirect
    eventnamel = get_nam_event()

    # Link to redirect
    urlBase = request.url_root
    link = urlBase + 'eventfeed?value='
    link += eventnamel

    # Get info from url query
    url = request.url
    parsed = urlparse.urlparse(url)
    comm = urlparse.parse_qs(parsed.query)['comments']
    pica = urlparse.parse_qs(parsed.query)['pic']

    # Insert comment into database
    db.execute("INSERT INTO comment_event (user_id, event_id, picture, comment) VALUES(:user_id, :event_id, :picture, :comment)",
               user_id=session["user_id"], event_id=session["event_id"], picture=pica, comment=comm)

    eventnamel = get_nam_event()

    # Link to redirect
    urlBase = request.url_root
    link = urlBase + 'eventfeed?value='
    link += eventnamel
    return redirect(link)


@app.route("/event_add_gif")
@login_required
def event_add_gif():
    url = request.url
    parsed = urlparse.urlparse(url)
    comm = urlparse.parse_qs(parsed.query)['value']
    pica = urlparse.parse_qs(parsed.query)['q']

    db.execute("INSERT INTO comment_event (user_id, event_id, picture, comment) VALUES(:user_id, :event_id, :picture, :comment)",
               user_id=session["user_id"], event_id=session["event_id"], picture=pica, comment=comm)

    # Get groupname to redirect
    eventnamel = get_nam_event()

    # Link to redirect
    urlBase = request.url_root
    link = urlBase + 'eventfeed?value='
    link += eventnamel
    return redirect(link)
