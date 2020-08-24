import cs50
import os
import re
import time
import datetime
from cs50 import SQL
from flask import Flask, session,render_template, request, redirect, url_for
from flask_sessions import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)
db = SQL("sqlite:///db.db")
alert_text = ""

# Function to ensure that users are logged in to view the website
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        # Redirects users to the login page when trying to access a login-only page while not logged in
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Dealing with the main route
@app.route("/")
@login_required
def index():
    session["commentopen"] = None

    plans = db.execute("SELECT * FROM plans WHERE user_id = :user_id ORDER BY date ASC LIMIT 5", user_id = session["user_id"])
    projects = db.execute("SELECT * FROM projects WHERE user_id = :user_id ORDER BY importance DESC LIMIT 5", user_id = session["user_id"])

    # Sends user to index.html, if logged in
    alert_text = ""
    return render_template("index.html", plans = plans, projects = projects)

# Dealing with appointments / plans
@app.route("/plans", methods =  ["GET", "POST"])
@login_required
def plans():
    session["commentopen"] = None
    alert_text = ""
    # Make query to get all plans add button next to all plans to remove
    
    plans = db.execute("SELECT * FROM plans WHERE user_id = :user_id ORDER BY date ASC", user_id = session["user_id"])
    print(plans)
    if request.method == "GET":
        return render_template("plans.html", plans = plans)
    else:
        details = request.form.get("details")
        date = request.form.get("date")

        db.execute("INSERT INTO plans (user_id, details, date) VALUES (:user_id, :details, :date)",
                                        user_id = session["user_id"], details = details, date = date)
        alert_text = "Successfully Added"
        # return render_template("plans.html", plans = plans, alert_text = alert_text)
        # If you can figure out how to add alerts well, remove the line below
        return redirect("/plans")

#Dealing with projects
@app.route("/projects", methods = ["GET", "POST"])
@login_required
def projects():
    session["commentopen"] = None
    if request.method == "GET":
        projects = db.execute("SELECT * FROM projects WHERE user_id = :user_id ORDER BY importance DESC", user_id = session["user_id"])
        print(projects)
        return render_template("projects.html", projects = projects)
    else:
        name = request.form.get("name")
        importance = request.form.get("importance")
        print(name)
        print(importance)
        db.execute("INSERT INTO projects (user_id, visible_ids, name, importance) VALUES (:user_id, :visible_ids, :name, :importance)",
                    user_id = session["user_id"], visible_ids = None, name = name, importance = importance)
        return redirect("/projects")

# Dealing with viewing projects
@app.route("/viewproject", methods = ["GET", "POST"])
@login_required
def viewproject():
    if request.method == "POST":
        id = request.form.get("id")
        details = db.execute("SELECT * FROM projects WHERE id = :id", id = id)
        shared = db.execute("SELECT * FROM shared WHERE user_id = :user_id", user_id = session["user_id"])
        comments = db.execute("SELECT * FROM comments WHERE project_id = :project_id ORDER BY datetime ASC", project_id = id)
        comments = getCommentUsers(comments)
        if len(shared) == 1:
            shared = shared[0]["project_ids"].split(",")

        # Checking for if user is the creator
        if session["user_id"] == details[0]["user_id"]:
            shared_users = getUsers(id)
            items = db.execute ("SELECT * FROM project_items WHERE project_id = :project_id ORDER BY status ASC", project_id = id)
            return render_template("viewproject.html", project = details[0], items = items, owner = True, shared_users = shared_users, comments = comments)
        
        # Checking if user was shared the project
        elif id in shared:
            items = db.execute ("SELECT * FROM project_items WHERE project_id = :project_id ORDER BY status ASC", project_id = id)
            return render_template("viewproject.html", project = details[0], items = items, owner = False, shared_users = [], comments = comments)
        
        # Denying access
        else:
            return "You do not have permission to view this page"

# Dealing with adding project items
@app.route("/addpitem", methods = ["POST"])
@login_required
def addproject():
    text = request.form.get("details")
    id = request.form.get("id")
    db.execute("INSERT INTO project_items (project_id, text, status) VALUES (:project_id, :text, :status)",
                project_id = id, text = text, status = 0)
    return redirect(f"/viewproject?id={id}", code = 307)

# Editing project item status
@app.route("/editstatus", methods = ["POST"])
@login_required
def editstatus():
    id = request.form.get("iid")
    project_id = request.form.get("id")
    status = request.form.get("status")
    db.execute("UPDATE project_items SET status = :status WHERE id = :id", status = status, id = id)    
    return redirect(f"/viewproject?{project_id}", code = 307)

# Deleting project items
@app.route("/deleteitem", methods = ["POST"])
@login_required
def deleteitem():
    id = request.form.get("iid")
    project_id = request.form.get("id")
    db.execute("DELETE FROM project_items WHERE id = :id", id = id)
    return redirect(f"/viewproject?{project_id}", code = 307)

# Sharing projects
@app.route("/share", methods = ["POST"])
@login_required
def share():
    username = request.form.get("username")
    project_id = request.form.get("id")
    guest_id = db.execute("SELECT * FROM users WHERE username = :username", username = username)
    visible_ids = db.execute("SELECT * FROM projects WHERE id = :id", id = project_id)[0]["visible_ids"]

    if guest_id:
        guest_id = guest_id[0]["id"]
        if not visible_ids:
            visible_ids = guest_id
            db.execute("UPDATE projects SET visible_ids = :visible_ids WHERE id = :id", 
                        visible_ids = visible_ids, id = project_id)
        else:
            visible_ids = visible_ids.split(',')
            print(f"split {guest_id}")
            if str(guest_id) not in visible_ids:
                visible_ids.append(str(guest_id))
                visible_ids = ','.join(visible_ids)
                db.execute("UPDATE projects SET visible_ids = :visible_ids WHERE id = :id", 
                            visible_ids = visible_ids, id = project_id)

        project_ids = db.execute("SELECT * FROM shared WHERE user_id = :user_id", user_id = guest_id)
        if len(project_ids) != 1:

            # If the user has not been shared a project before
            project_ids = project_id
            db.execute("INSERT INTO shared (user_id, project_ids) VALUES (:user_id, :project_ids)",
                        user_id = guest_id, project_ids = project_ids)
            return redirect(f"/viewproject?{project_id}", code = 307)
        else:

            # If the user has already been shared projects
            project_ids = project_ids[0]["project_ids"].split(",")
            if project_id in project_ids:

                # Redundancy checking
                return redirect(f"/viewproject?{project_id}", code = 307)
            project_ids.append(f"{project_id}")
            project_ids = ','.join(project_ids)

        db.execute("UPDATE shared SET project_ids = :project_ids WHERE user_id = :user_id", project_ids = project_ids, user_id = guest_id)
        return redirect(f"/viewproject?{project_id}", code = 307)
    else:
        print("could not find user")
        return redirect(f"/viewproject?{project_id}", code = 307)

# Viewing shared projects
@app.route("/shared", methods = ["GET", "POST"])
@login_required
def shared():
    shared = db.execute("SELECT * FROM shared WHERE user_id = :user_id", user_id = session["user_id"])

    if len(shared) == 1:

        # Getting shared project ids
        shared = shared[0]["project_ids"].split(",")
        print(shared)
        shared_projects = []
        for id in shared:
            for char in id:
                if char not in [range(10)]:
                    id.replace(char, '')
            print(id)
            # Getting shared project details 
            single = db.execute("SELECT * FROM projects WHERE id = :id", id = id)
            if len(single) == 1:
                single = single[0]
                single["owner"] = db.execute("SELECT * FROM users WHERE id = :id", id = single["user_id"])[0]["username"]
                shared_projects.append(single)
                print(shared_projects)
    else:
        shared_projects = []

    if request.method == "GET":
        return render_template("shared.html", projects = shared_projects)

# Deleting shared users
@app.route("/deleteuser", methods = ["POST"])
@login_required
def deleteuser():
    username = request.form.get("username")
    project_id = request.form.get("id")
    guest_id = db.execute("SELECT * FROM users WHERE username = :username", username = username)[0]["id"]

    # Removing project id from guest id's shared table
    shared = db.execute("SELECT * FROM shared WHERE user_id = :user_id", user_id = guest_id)[0]["project_ids"].split(",")

    shared.remove(project_id)

    print(f"shared list now {shared}")

    shared = ",".join(shared)

    db.execute("UPDATE shared SET project_ids = :project_ids WHERE user_id = :user_id",
                project_ids = shared, user_id = guest_id)

    # Removing guest id from project's visible id list
    visible_ids = db.execute("SELECT * FROM projects WHERE id = :id", id = project_id)[0]["visible_ids"].split(",")
    
    print(visible_ids)

    visible_ids.remove(str(guest_id))

    visible_ids = ",".join(visible_ids)

    db.execute("UPDATE projects SET visible_ids = :visible_ids WHERE id = :id",
                visible_ids = visible_ids, id = project_id)

    return redirect(f"/viewproject?{project_id}", code = 307) 

# Deleting plans
@app.route("/deleteplan", methods = ["POST"])
@login_required
def deleteplan():
    # Delete with sql query
    id = request.form.get("id")
    db.execute("DELETE FROM plans WHERE id = :id", id = id)
    return redirect("/plans")

# Sending comments
@app.route("/sendcomment", methods = ["POST"])
@login_required
def sendcomment():
    comment = request.form.get("comment")
    project_id = request.form.get("id")
    dt = datetime.datetime.now()
    
    db.execute("INSERT INTO comments (user_id, project_id, text, datetime) VALUES (:user_id, :project_id, :text, :datetime)",
    user_id = session["user_id"], project_id = project_id, text = comment, datetime = dt.strftime('%Y-%m-%d %H:%M:%S') )

    session["commentopen"] = True
    return redirect(f"/viewproject?{project_id}", code = 307) 

# Closing the chat box
@app.route("/closecomment", methods = ["POST"])
@login_required
def closecomment():
    session["commentopen"] = None
    return ('', 204)

# Dealing with registration
@app.route("/register", methods = ["POST", "GET"])
def register():
    alert_text = ""

    # If get, view the page, if post, check and update appropriately
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        
        # Checking for valid inputs
        if not password == request.form.get("confirm-password"):
            return "Password did not match, please try again"
        if not email == request.form.get("confirm-email"):
            return "Emails did not match, please try again"
        if not username:
            return "Please provide a username"
        if not password:
            return "Please provide a password"
        if not email:
            return "Please provide an email"
        if "@" not in email:
            return "Please provide a valid email"
        
        # Checking for redundant accounts
        rows = db.execute("SELECT * FROM users WHERE username = :username", username = username)
        if len(rows) == 0:
            emailrows = db.execute("SELECT * FROM users WHERE email = :email", email = email)
            if len(emailrows) == 0:

                # If there are no overlapping emails or username, proceed
                hash = generate_password_hash(password)
                db.execute ("INSERT INTO users (username, hash, email) VALUES (:username, :hash, :email)",
                            username = username, hash = hash, email = email)
                return redirect ("/")
            else:
                return "An account with that email already exists"
        else:
            return "An account with that username already exists"

# Dealing with logins
@app.route("/login", methods = ["GET", "POST"])
def login():
    alert_text = ""
    
    # Clearing previous session data
    session.clear()

    if request.method == "GET":
        return render_template("login.html")
    else:

        # Checking for valid inputs
        if not request.form.get("username"):
            return "Please enter a username"
        if not request.form.get("password"):
            return "Please enter a password"

        # Checking for a match in the database
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                            username = request.form.get("username"))
        
        # Checking if the match exists and that the hashes are the same
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return "Invalid username and/or password"

        # Give the user a session id
        session["user_id"] = rows[0]["id"]
        session["commentopen"] = None
        session["theme"] = "white"
        print(session["commentopen"])

        return redirect("/")

# Dealing with password changes
@app.route("/changepassword", methods = ["GET", "POST"])
def changepassword():
    session["commentopen"] = None
    
    alert_text = ""

    if request.method == "GET":
        return render_template("changepassword.html")
    else:

        # Get values from the change password form
        current_pass = request.form.get("password")
        new_pass = request.form.get("new-password")
        email = request.form.get("email")

        # Get current values for the hash and email from db
        current_hash = db.execute("SELECT * FROM users WHERE id = :id", id = session["user_id"])[0]["hash"]
        current_email = db.execute("SELECT * FROM users WHERE id = :id", id = session["user_id"])[0]["email"]

        # Checking for valid inputs
        if not new_pass == request.form.get("confirm-new-password"):
            return "Passwords do not match please try again"
        if not check_password_hash(current_hash,current_pass):
            return "Password Invalid"
        if not email == current_email:
            return "Email Invalid"
        else:

            # Hash new password, update the table, and return to index with an alert
            hash = generate_password_hash(new_pass)
            db.execute("UPDATE users SET hash = :hash WHERE id = :id", hash = hash, id = session["user_id"])
            alert_text = "Password Changed Successfully"
            return render_template("index.html", alert_text = alert_text)

# Changing themes
@app.route("/changecolor", methods = ["POST"])
def changecolor():
    if session["theme"] == "dark":
        session["theme"] = "white"
    else:
        session["theme"] = "dark"
    return ('', 204)

def getUsers(id):
    # Takes the project id and returns a list a list of usernames that have access
    visible_ids = db.execute("SELECT * FROM projects WHERE id = :id", id = id)[0]["visible_ids"]
    id_list = []
    u_list = []
    if visible_ids:
        visible_ids = visible_ids.split(",")
        for i in visible_ids:
            id_list.append(int(i))
        for elem in id_list:
            if elem == "" or elem == None:
                id_list.remove(elem)
            else:
                j = db.execute("SELECT * FROM users WHERE id = :id", id = elem)[0]["username"]
                u_list.append(j)
    
    return u_list

def getCommentUsers(comments):
    modifiedList = []
    for comment in comments:
        user_id = comment["user_id"]
        username = db.execute("SELECT * FROM users WHERE id = :id", id = user_id)[0]["username"]
        comment["username"] = username
        modifiedList.append(comment)
    return modifiedList