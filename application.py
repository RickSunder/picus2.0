from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_from_directory
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
import unicodedata
import os
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask import send_from_directory
from helpers import *

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
            return "jammer neef"
        if not request.form.get("username"):
            return "jammer neef"
        if request.form.get("password") != request.form.get("confirmation"):
            return "jammer neef"
        if request.form.get("password") == "":
            return "jammer neef"
        elif not request.form.get("password"):
            return "jammer neef"
        elif not request.form.get("confirmation"):
            return "jammer neef"

        geregistreerd = db.execute("INSERT INTO users (email, username, hash) VALUES(:email, :username, :password)", email=request.form.get("email"), username=request.form.get("username"), password=pwd_context.hash(request.form.get("password")))

        if not geregistreerd:
            return apology("Helaas")

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
            return "Name of the group already exist"

        file = request.files['file']
        if not allowed_file(file.filename):
            return "This is not a picture"

        filename =  name_group + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # return "file uploaded"

        # print("joe")
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
            return "This user is already part of the group"

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
def eventview():
    if request.method == "POST":
        return "hoi"
    else:
        return render_template("eventview.html")

@app.route("/makeevent", methods=["GET", "POST"])
@login_required
def makeevent():
    if request.method == "POST":

        if not request.form.get("makeevent"):
            return "insert eventname"


        if len(db.execute("SELECT * FROM events WHERE eventname=:event", event=request.form.get("makeevent"))) > 0:
            return "eventname already exists"

        rows = db.execute("SELECT event_id FROM user_events WHERE event_id=:event_id", event_id=session["event_id"])
        #db.execute("INSERT INTO events (eventname, event_id, username) VALUES(:eventname, :event_id, :username)", eventname=request.form.get("makeevent"), event_id=iets , username=session.get("username")))

        #session["user_id"] = rows[0]["id"]
        # check if the post request has the file part
        file = request.files['file']
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        session["event_id"] = rows[0]["event_id"]

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
        filename =  nmakee + "_" + file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        db.execute("INSERT INTO user_events (eventpicture) VALUES(:eventpicture)", eventpicture=filename)
        db.execute("INSERT INTO events (eventname, username) VALUES(:eventname, :username)", eventname=request.form.get("makeevent"), username=session["user_id"])
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
            return "must provide username"

        # wachtwoord verzekeren
        elif not request.form.get("password"):
            return "must provide password"

        # username database
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # kijken of username uniek is en wachtwoord klopt
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return "invalid username and/or password"

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
    # if request.method == "POST":
    groupl = db.execute("SELECT group_id FROM user_groups WHERE user_id=:user_id", user_id=session["user_id"])

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
        # profilepic = open(app.config['UPLOAD_FOLDER'] +"/" + profilepic, 'wb')
        temporary.append([groupnamel, profilepicture])

    for rows in temporary:
        print(rows[0], rows[1])


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