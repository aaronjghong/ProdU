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

    # Query for user's plans and projects
    plans = db.execute("SELECT * FROM plans WHERE user_id = :user_id ORDER BY date ASC LIMIT 5", user_id = session["user_id"])
    projects = db.execute("SELECT * FROM projects WHERE user_id = :user_id ORDER BY importance DESC LIMIT 5", user_id = session["user_id"])

    # Sends user to index.html, if logged in
    alert_text = ""
    return render_template("index.html", plans = plans, projects = projects)

# Dealing with main plans route and adding plans
@app.route("/plans", methods =  ["GET", "POST"])
@login_required
def plans():
    session["commentopen"] = None
    alert_text = ""
    
    # Make query to get all plans add button next to all plans to remove
    plans = db.execute("SELECT * FROM plans WHERE user_id = :user_id ORDER BY date ASC", user_id = session["user_id"])
    print(plans)
    if request.method == "GET":
        
        # Send user to plans page with their plans
        return render_template("plans.html", plans = plans)
    else:
        
        # Get plan details and date from the form
        details = request.form.get("details")
        date = request.form.get("date")

        # Insert the plan into the database and return to plans page
        db.execute("INSERT INTO plans (user_id, details, date) VALUES (:user_id, :details, :date)",
                                        user_id = session["user_id"], details = details, date = date)
        alert_text = "Successfully Added"
        return redirect("/plans")

# Dealing with main projects route and adding projects
@app.route("/projects", methods = ["GET", "POST"])
@login_required
def projects():
    session["commentopen"] = None
    if request.method == "GET":
        
        # Query for user's projects
        projects = db.execute("SELECT * FROM projects WHERE user_id = :user_id ORDER BY importance DESC", user_id = session["user_id"])
        print(projects)
        
        # Send user to projects page with their projects
        return render_template("projects.html", projects = projects)
    else:

        # Get project name and importance from form
        name = request.form.get("name")
        importance = request.form.get("importance")
        print(name)
        print(importance)

        # Insert project into database and return to projects page
        db.execute("INSERT INTO projects (user_id, visible_ids, name, importance) VALUES (:user_id, :visible_ids, :name, :importance)",
                    user_id = session["user_id"], visible_ids = None, name = name, importance = importance)
        return redirect("/projects")

# Dealing with viewing projects
@app.route("/viewproject", methods = ["GET", "POST"])
@login_required
def viewproject():
    if request.method == "POST":

        # Get the project id from the form
        id = request.form.get("id")

        # Query for the project, the user's shared projects, and the project's comments
        details = db.execute("SELECT * FROM projects WHERE id = :id", id = id)
        shared = db.execute("SELECT * FROM shared WHERE user_id = :user_id", user_id = session["user_id"])
        comments = db.execute("SELECT * FROM comments WHERE project_id = :project_id ORDER BY datetime ASC", project_id = id)
        
        # Modify comments to include the username of the sender as well
        comments = getCommentUsers(comments)

        # If the user has been shared a project, split project_ids into a list
        if len(shared) == 1:
            shared = shared[0]["project_ids"].split(",")

        # Checking for if user is the creator
        if session["user_id"] == details[0]["user_id"]:

            # Get list of shared users (usernames)
            shared_users = getUsers(id)

            # Query for the project's items
            items = db.execute ("SELECT * FROM project_items WHERE project_id = :project_id ORDER BY status ASC", project_id = id)
            
            # Render the viewproject page for the user
            return render_template("viewproject.html", project = details[0], items = items, owner = True, shared_users = shared_users, comments = comments)
        
        # Checking if user was shared the project
        elif id in shared:

            # Query for the project's items
            items = db.execute ("SELECT * FROM project_items WHERE project_id = :project_id ORDER BY status ASC", project_id = id)
            
            # Render the viewproject page for the user
            return render_template("viewproject.html", project = details[0], items = items, owner = False, shared_users = [], comments = comments)
        
        # Denying access
        else:
            return "You do not have permission to view this page"

# Dealing with adding project items
@app.route("/addpitem", methods = ["POST"])
@login_required
def addproject():

    # Get the project item's text and project id from the form
    text = request.form.get("details")
    id = request.form.get("id")

    # Add the item into the database
    db.execute("INSERT INTO project_items (project_id, text, status) VALUES (:project_id, :text, :status)",
                project_id = id, text = text, status = 0)
    
    # Redirect to the same project page
    return redirect(f"/viewproject?id={id}", code = 307)

# Editing project item status
@app.route("/editstatus", methods = ["POST"])
@login_required
def editstatus():

    # Gets the item id, project id, and new status from the form
    id = request.form.get("iid")
    project_id = request.form.get("id")
    status = request.form.get("status")

    # Updates the item status in the database
    db.execute("UPDATE project_items SET status = :status WHERE id = :id", status = status, id = id)    
   
    # Redirects the user to the same project page
    return redirect(f"/viewproject?{project_id}", code = 307)

# Deleting project items
@app.route("/deleteitem", methods = ["POST"])
@login_required
def deleteitem():

    # Gets project item id and project id from the form
    id = request.form.get("iid")
    project_id = request.form.get("id")

    # Deletes the project from the same page
    db.execute("DELETE FROM project_items WHERE id = :id", id = id)

    # Redirects the user to the same project page
    return redirect(f"/viewproject?{project_id}", code = 307)

# Sharing projects
@app.route("/share", methods = ["POST"])
@login_required
def share():

    # Get the guest's username and project id from the form
    username = request.form.get("username")
    project_id = request.form.get("id")

    # Queries for the guest's id and the project's current shared users (visible_ids)
    guest_id = db.execute("SELECT * FROM users WHERE username = :username", username = username)
    visible_ids = db.execute("SELECT * FROM projects WHERE id = :id", id = project_id)[0]["visible_ids"]

    # If the id of the given username is found
    if guest_id:
        guest_id = guest_id[0]["id"]

        # If there are no shared users:
        if not visible_ids:

            # Set the shared users list to the guest's id
            visible_ids = guest_id
            db.execute("UPDATE projects SET visible_ids = :visible_ids WHERE id = :id", 
                        visible_ids = visible_ids, id = project_id)
        
        # If there are shared users,
        else:

            # Split the shared users string into a list
            visible_ids = visible_ids.split(',')
            print(f"split {guest_id}")

            # If the guest id is not in the shared users list
            if str(guest_id) not in visible_ids:

                # Append the guest id to the shared users list, join the list into a string, and update the db
                visible_ids.append(str(guest_id))
                visible_ids = ','.join(visible_ids)
                db.execute("UPDATE projects SET visible_ids = :visible_ids WHERE id = :id", 
                            visible_ids = visible_ids, id = project_id)

        # Query for the guest's shared projects (project_ids)
        project_ids = db.execute("SELECT * FROM shared WHERE user_id = :user_id", user_id = guest_id)
        if len(project_ids) != 1:

            # If the user has not been shared a project before, set the shared projects list to the shared project id and update db
            project_ids = project_id
            db.execute("INSERT INTO shared (user_id, project_ids) VALUES (:user_id, :project_ids)",
                        user_id = guest_id, project_ids = project_ids)
            
            # Redirect the user to the same page
            return redirect(f"/viewproject?{project_id}", code = 307)
        else:

            # If the user has already been shared projects
            project_ids = project_ids[0]["project_ids"].split(",")
            
            # Check for duplicate entries
            if project_id in project_ids:
                
                # If there are duplicates, redirect the user to the same page 
                return redirect(f"/viewproject?{project_id}", code = 307)
            
            # Append the shared project to the shared projects list, and join the list
            project_ids.append(f"{project_id}")
            project_ids = ','.join(project_ids)

        # Update the shared projects in the db
        db.execute("UPDATE shared SET project_ids = :project_ids WHERE user_id = :user_id", project_ids = project_ids, user_id = guest_id)
        
        # Redirect user to the same page
        return redirect(f"/viewproject?{project_id}", code = 307)
    
    # If the id was not found:
    else:

        # Redirect user to the same page
        return redirect(f"/viewproject?{project_id}", code = 307)

# Viewing shared projects
@app.route("/shared", methods = ["GET", "POST"])
@login_required
def shared():

    # Query for the user's shared projects
    shared = db.execute("SELECT * FROM shared WHERE user_id = :user_id", user_id = session["user_id"])

    # If the user was shared projects
    if len(shared) == 1:

        # Split the shared projects string into a list
        shared = shared[0]["project_ids"].split(",")
        print(shared)
        shared_projects = []

        # Iterating over each shared project id
        for id in shared:

            # If there are any non number chracters in the id, remove those characters
            for char in id:
                if char not in [range(10)]:
                    id.replace(char, '')
            print(id)

            # Getting the details of the project at id 
            single = db.execute("SELECT * FROM projects WHERE id = :id", id = id)
            
            # If the project exists:
            if len(single) == 1:
                single = single[0]

                # Get the shared project's owner's username
                single["owner"] = db.execute("SELECT * FROM users WHERE id = :id", id = single["user_id"])[0]["username"]
                shared_projects.append(single)
                print(shared_projects)
    else:
        shared_projects = []

    if request.method == "GET":

        # Send the user to their shared page
        return render_template("shared.html", projects = shared_projects)

# Deleting shared users
@app.route("/deleteuser", methods = ["POST"])
@login_required
def deleteuser():

    # Get the guest's username and the project id from the form
    username = request.form.get("username")
    project_id = request.form.get("id")

    # Query for the guest's id
    guest_id = db.execute("SELECT * FROM users WHERE username = :username", username = username)[0]["id"]

    # Query for the guest's shared projects list
    shared = db.execute("SELECT * FROM shared WHERE user_id = :user_id", user_id = guest_id)[0]["project_ids"].split(",")

    # Removing project id from guest's shared projects
    shared.remove(project_id)

    print(f"shared list now {shared}")

    shared = ",".join(shared)

    # Update the shared projects list in the db
    db.execute("UPDATE shared SET project_ids = :project_ids WHERE user_id = :user_id",
                project_ids = shared, user_id = guest_id)

    # Get the project's shared users list
    visible_ids = db.execute("SELECT * FROM projects WHERE id = :id", id = project_id)[0]["visible_ids"].split(",")
    
    print(visible_ids)

    # Removing guest id from project's visible id list
    visible_ids.remove(str(guest_id))

    visible_ids = ",".join(visible_ids)

    # Update the shared users list in the db
    db.execute("UPDATE projects SET visible_ids = :visible_ids WHERE id = :id",
                visible_ids = visible_ids, id = project_id)

    return redirect(f"/viewproject?{project_id}", code = 307) 

# Deleting plans
@app.route("/deleteplan", methods = ["POST"])
@login_required
def deleteplan():

    # Get the plan id from the form
    id = request.form.get("id")

    # Delete the plan from the db and redirect back to plans
    db.execute("DELETE FROM plans WHERE id = :id", id = id)
    return redirect("/plans")

# Sending comments
@app.route("/sendcomment", methods = ["POST"])
@login_required
def sendcomment():

    # Get the comment, project id, and the current datetime
    comment = request.form.get("comment")
    project_id = request.form.get("id")
    dt = datetime.datetime.now()
    
    # Add the comment into the db
    db.execute("INSERT INTO comments (user_id, project_id, text, datetime) VALUES (:user_id, :project_id, :text, :datetime)",
    user_id = session["user_id"], project_id = project_id, text = comment, datetime = dt.strftime('%Y-%m-%d %H:%M:%S') )

    # Set the comments to be open and redirect the user to the same project page
    session["commentopen"] = True
    return redirect(f"/viewproject?{project_id}", code = 307) 

# Closing the chat box
@app.route("/closecomment", methods = ["POST"])
@login_required
def closecomment():

    # Change the commentopen state
    session["commentopen"] = None
    return ('', 204)

# Dealing with registration
@app.route("/register", methods = ["POST", "GET"])
def register():
    alert_text = ""

    if request.method == "GET":

        # Render the registration page
        return render_template("register.html")
    else:

        # Get the user's username, password, and email from the form
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
        # Query for users with the same username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username = username)
        
        # If there are no username matches:
        if len(rows) == 0:

            # Query for users with the same email
            emailrows = db.execute("SELECT * FROM users WHERE email = :email", email = email)
            
            # If there are no email matches
            if len(emailrows) == 0:

                # Hash the user's password
                hash = generate_password_hash(password)

                # Add the user into the database
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
    session["theme"] = "white"
    session["referrer"] = "/"
    if request.method == "GET":

        # Send the user to the login page
        session["theme"] = "white"
        print(f"{session['theme']} is the theme")
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
        print(session["commentopen"])

        return redirect("/")

# Dealing with password changes
@app.route("/changepassword", methods = ["GET", "POST"])
def changepassword():
    session["commentopen"] = None
    
    alert_text = ""

    if request.method == "GET":

        # Render the changepassword page
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
@app.route("/changecolor", methods = ["GET","POST"])
def changecolor():
    if request.method == "GET":

        # If the user was viewing a project:
        if "viewproject" in session["referrer"]:

            # Return the user back to the projects page
            return redirect("/projects")

        # Return the user back to the page they were on
        return redirect(session["referrer"])

    else:

        # Get the page the user was on
        session["referrer"] = request.referrer

        # Get the theme from the page
        theme = request.form.get("theme")

        # Set the theme to the opposite that it currently is
        if theme == "white":
            theme = "dark"
        else:
            theme = "white"

        # Set the session theme variable to the new theme
        session["theme"] = theme
        print(f"{session['theme']} vs {theme}")
        print(f"REQUEST URL {request.url}")

        # Sends the user back to /changecolor with a GET request
        return redirect(request.url, 302)

# Takes the project id and returns a list a list of usernames that have access to the project
def getUsers(id):

    # Query for the shared users
    visible_ids = db.execute("SELECT * FROM projects WHERE id = :id", id = id)[0]["visible_ids"]
    id_list = []
    u_list = []

    # If there are shared users
    if visible_ids:
        visible_ids = visible_ids.split(",")
        
        # Iterating through the list of ids
        for i in visible_ids:

            # Append the shared id to a list of ids
            id_list.append(int(i))
        
        #^^^ Probably redundant and not needed

        # Iterating through the list of ids
        for elem in id_list:

            # If the id does not exist, remove it
            if elem == "" or elem == None:
                id_list.remove(elem)

            # If the id exists
            else:

                # Query for the username of the id and add it to a list of usernames
                j = db.execute("SELECT * FROM users WHERE id = :id", id = elem)[0]["username"]
                u_list.append(j)
    
    return u_list

# Takes a list of comments and returns a modified list with usernames of the commenters
def getCommentUsers(comments):
    modifiedList = []

    # Go through each comment
    for comment in comments:

        # Get the commenter's id
        user_id = comment["user_id"]

        # Query for the commenter's username
        username = db.execute("SELECT * FROM users WHERE id = :id", id = user_id)[0]["username"]
        
        # Add the commenter's username to the comment dictionary
        comment["username"] = username
        modifiedList.append(comment)
    return modifiedList