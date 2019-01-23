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
# import giphy_client
# from giphy_client.rest import ApiException
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
    if request.method == "POST":
        return "hoi"
    else:
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
        name_group = request.form.get("name_group")

        name = db.execute("SELECT name_group FROM groups WHERE name_group=:name", name=name_group)
        if len(name) > 0:
            name = name[0]["name_group"]
        else:
            name = ""

        if name == name_group:
            return apology("Name of the group already exist")

        file = request.files['file']
        if not allowed_file(file.filename):
            return apology("This is not a picture")

        filename =  name_group + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db.execute("INSERT INTO groups (name_group, profile_picture) VALUES(:groupname, :profile_picture)", groupname=name_group, profile_picture=filename)

        rows = db.execute("SELECT group_id FROM groups WHERE name_group=:group", group=name_group)
        session["group_id"] = rows[0]["group_id"]

        db.execute("INSERT INTO user_groups (user_id, group_id) VALUES(:user_id, :group_id)", user_id=session["user_id"], group_id=session["group_id"])

        return render_template("addgroupmember.html")
    else:
        return render_template("makegroup.html")


@app.route("/addmember", methods=["GET", "POST"])
@login_required
def addmember():
    if request.method == "POST":
        add_members = request.form.get("add_members")
        groupname = request.form.get("groupname")

        user = find_user(add_members)
        if user == []:
            return "Username doesn't exist"

        id_user = db.execute("SELECT id FROM users WHERE username=:username", username=add_members)
        id_user = id_user[0]["id"]

        users = db.execute("SELECT user_id FROM user_groups WHERE user_id=:user_id AND group_id=:group_id", user_id=id_user, group_id=session["group_id"])

        if len(users) > 0:
            users = users[0]["user_id"]
        else:
            users = ""

        if users == id_user:
            return apology("This user is already part of the group")

        db.execute("INSERT INTO user_groups (user_id, group_id) VALUES(:user_id, :group_id)", user_id=id_user, group_id=session["group_id"])

        members = db.execute("SELECT user_id FROM user_groups WHERE group_id=:group_id", group_id=session["group_id"])

        temporary = []
        temp = []
        for line in range(len(members)):
            member = members[line]["user_id"]
            temp.append(member)

        for row in temp:
            mem = db.execute("SELECT username FROM users WHERE id=:id_mem", id_mem=row)
            mem = mem[0]["username"]
            temporary.append([mem])


        return render_template("addgroupmember.html", list_members = temporary)
    else:
        return render_template("addgroupmember.html")



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/eventview", methods=["GET", "POST"])
@login_required
def eventview():
    event_id1 = db.execute("SELECT event_id FROM user_events WHERE user_id=:user_id", user_id=session["user_id"])

    temporaryview = []
    temp = []
    for event in range(len(event_id1)):
        event_id = event_id1[event]["event_id"]
        temp.append(event_id)

    for number in temp:
        event_id = db.execute("SELECT event_name, event_picture FROM event_account WHERE event_id=:id_event", id_event=number)
        event_id1 = event_id[0]["event_name"]
        profilepic = event_id[0]["event_picture"]
        profilepicture = os.path.join(app.config["UPLOAD_FOLDER"], profilepic)
        temporaryview.append([event_id1, profilepicture])

    for rows in temporaryview:
        print(rows[0], rows[1])


    return render_template("eventview.html", list_event_id = temporaryview)

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
        groupl = db.execute("SELECT group_id FROM user_groups WHERE user_id = :user_id", user_id=session["user_id"])

        temporary = []
        temp = []

        for num in range(len(groupl)):
            group = groupl[num]["group_id"]
            groupname = db.execute("SELECT name_group FROM groups WHERE group_id=:group_id", group_id=group)
            temp.append([group, groupname])

        group = db.execute("SELECT user_id, picture, comment FROM picture_group WHERE group_id=:id_group", id_group=group_id)

        for number in range(len(group)):
            user_id = group[number]["user_id"]
            user = db.execute("SELECT username FROM users WHERE id=:id_user", id_user=user_id)
            username= user[0]["username"]
            profilepic = group[number]["picture"]
            comments = group[number]["comment"]
            profilepicture = os.path.join(app.config['UPLOAD_FOLDER'], profilepic)

            temporary.append([username, profilepicture, comments])

        return render_template("groupview.html", list_picture=temporary, name_group=request.form.get("group"), group=temp)
    else:

        groupl = db.execute("SELECT group_id FROM user_groups WHERE user_id=:id_user", id_user=session["user_id"])

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

            temporary.append([groupnamel, profilepicture])
        return render_template("groupfeed.html", list_group = temporary)


@app.route("/aboutus", methods=["GET", "POST"])
def aboutus():
    return render_template("aboutus.html")


@app.route("/settings", methods=["GET", "POST"])
def settings():
    return render_template("settings.html")

@app.route("/password", methods=["GET", "POST"])
def password():
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
    # if request.method == "POST":
    url = request.url
    parsed = urlparse.urlparse(url)
    name = urlparse.parse_qs(parsed.query)['value']
    group_idd = db.execute("SELECT group_id FROM groups WHERE name_group=:group", group=name)
    group_idd = group_idd[0]["group_id"]
    session["group_id"] = group_idd
    temporary = []


    group = db.execute("SELECT user_id, picture, comment FROM picture_group WHERE group_id=:id_group", id_group=group_idd)

    for number in range(len(group)):
        user_id = group[number]["user_id"]
        user = db.execute("SELECT username FROM users WHERE id=:id_user", id_user=user_id)
        username= user[0]["username"]
        profilepic = group[number]["picture"]
        comments = group[number]["comment"]
        profilepicture = os.path.join(app.config['UPLOAD_FOLDER'], profilepic)

        temporary.append([username, profilepicture, comments])

    return render_template("groupview.html", list_picture=temporary, group=name[0])
    # else:
    #     return render_template("groupview.html")

@app.route("/upload_photo", methods=["GET", "POST"])
@login_required
def upload_photo():
    if request.method=="POST":

        group_name = db.execute("SELECT name_group FROM groups WHERE group_id=:group", group=session["group_id"])
        group = group_name[0]["name_group"]

        comments = request.form.get("comment")

        file = request.files['file']
        if not allowed_file(file.filename):
            return "This is not a picture"

        filename =  str(session["user_id"]) + "_" + str(session["group_id"]) + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        db.execute("INSERT INTO picture_group (user_id, group_id, picture, like, comment) VALUES(:user_id, :group_id, :picture, :like, :comment)",
                   user_id=session["user_id"], picture=filename, group_id=session["group_id"], like=0, comment=comments)


        return render_template("upload_photo.html", groupname=group)
    else:

        return render_template("upload_photo.html")



@app.route("/search", methods=["GET", "POST"])
def search():
    check = 0
    zoekopdracht=request.form.get("search")
    zoeken = db.execute("SELECT * FROM events WHERE eventname LIKE :zoekopdracht ORDER BY eventname ASC", zoekopdracht=str(zoekopdracht)+"%")
    resultaten = []

    for row in zoeken:
        resultaten.append(row['eventname'])

    if request.form.get("search") == "":
        return render_template("search.html", zoekopdracht=zoekopdracht, resultaten=resultaten, check=0)
    if not request.form.get("search"):
        return render_template("search.html", zoekopdracht=zoekopdracht, resultaten=resultaten, check=0)


    return render_template("search.html", zoekopdracht=zoekopdracht, resultaten=resultaten, check=1)





@app.route("/eventphoto", methods=["GET, POST"])
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

        db.execute("INSERT INTO event_feed (images, caption, user_id, event_id) VALUES(:images, :caption, :user_id, :event_id)",
                   images=filename, caption = caption, user_id = session.get("user_id"), event_id = session.get("event_id"))

        return render_template("eventphoto.html", eventname=event)
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
@login_required
def eventfeed():
    url = request.url
    parsed = urlparse.urlparse(url)
    name = urlparse.parse_qs(parsed.query)['value']
    event_idd = db.execute("SELECT event_id FROM event_account WHERE name_event=:event", event=name)
    event_idd = event_idd[0]["event_id"]
    session["event_id"] = event_idd
    temporary = []


    event = db.execute("SELECT user_id, images, caption FROM event_feed WHERE event_id=:id_event", id_event=event_idd)

    for number in range(len(event)):
        user_id = event[number]["user_id"]
        user = db.execute("SELECT username FROM users WHERE id=:id_user", id_user=user_id)
        username= user[0]["username"]
        profilepicevent = event[number]["images"]
        captions = event[number]["caption"]
        profilepicture = os.path.join(app.config['UPLOAD_FOLDER'], profilepicevent)

    temporary.append([username, profilepicture, captions])
    if request.form.get("comment") != None:
        #gif = request.get_json(url)
        #data = json.loads(urllib.urlopen(gif).read())
        #print (json.dumps(data, sort_keys=True, indent=4))
        return "hoi"
    like_count = db.execute("SELECT likes FROM event_feed WHERE likes=:like", like = 0)
    if request.form.get("like") == True:
        db.execute("UPDATE event_feed SET likes =: likes WHERE id =: image_id", likes = like_count + 1, image_id = session["image_id"])

    dislike_count = db.execute("SELECT dislikes FROM event_feed WHERE dislikes=:dislike", dislike= 0)
    if request.form.get("dislike") == True:
        db.execute("UPDATE event_feed SET dislikes =: dislikes WHERE id =: image_id", dislikes = dislike_count + 1, image_id = session["image_id"])

    image_names = os.listdir('./images')
    print(image_names)
    return render_template("eventfeed.html", list_picture=temporary, event=name[0])




@app.route('/leave_group/')
@login_required
def leave_group():

    db.execute("DELETE FROM user_groups WHERE user_id = :user_id AND group_id = :group_id", user_id=session["user_id"], group_id = session["group_id"])


    group_name = db.execute("SELECT name_group FROM groups WHERE group_id=:group", group=session["group_id"])
    group = group_name[0]["name_group"]
    return render_template("leave_group.html", groupname=group)
