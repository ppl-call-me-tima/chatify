import os

from database import execute, execute_retrieve
from datetime import datetime, timedelta
from flask import flash, Flask, render_template, redirect, request, session, url_for
from helpers import allowed_file, flash_and_redirect, log_user_in, login_required
from markupsafe import escape
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Permanent Session
app.secret_key = "stfu"
app.permanent_session_lifetime = timedelta(minutes=69)
# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Uploading Files
UPLOAD_FOLDER = "static/uploads"
app.config["MAX_CONTENT_LENGTH"] = 64 * 1000 * 1000  # 64MB
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
@login_required
def index():
    return render_template("index.html", username=session.get("username"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate form data
        if not username:
            return flash_and_redirect("Enter name!", "login")
        
        if not password:
            return flash_and_redirect("Enter password!", "login")
        
        rows = execute_retrieve("SELECT id, hash FROM user WHERE username = :username", {"username" : username})
                        
        # User / password mismatch
        if not rows or not check_password_hash(rows[0]["hash"], password):
            return flash_and_redirect("Enter correct username / password!", "login")
        
        log_user_in(rows[0]["id"], username)
        return redirect(url_for("index"))
    else:
        if "user_id" in session:
            return flash_and_redirect("Already logged-in!", "index")
        else:
            return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":        
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        # Validate form data
        if not username:
            return flash_and_redirect("Enter username!", "register")
        
        if not password:
            return flash_and_redirect("Enter password!", "register")
        
        if not confirmation:
            return flash_and_redirect("Re-enter password!", "register")
        
        if password != confirmation:
            return flash_and_redirect("Passwords don't match!", "register")
                
        # Check if username already exists
        rows = execute_retrieve("SELECT id FROM user WHERE username = :username", {"username":username})
        
        if rows:
            return flash_and_redirect("Username already taken!", "login")
                
        # Insert data into table
        execute("INSERT INTO user (username, hash) VALUES (:username, :hash)", 
                {"username":username, "hash":generate_password_hash(password)})

        # Log-in the user
        rows = execute_retrieve("SELECT id FROM user WHERE username = :username", {"username":username})
        log_user_in(rows[0]["id"], username)
        
        return flash_and_redirect("Successfully Registered and Logged-In!", "index")
    else:
        return render_template("register.html")
    

@app.route("/profile/<username>")
@login_required
def profile(username):
    # TODO : implement profile page
    
    username = str(escape(username))
    
    if username == session["username"]:
        self_profile = True
    else:
        self_profile = False
    
    rows = execute_retrieve("SELECT pfp_filename FROM user WHERE username = :username", 
                            {"username": username})
    
    # user.pfp_filename == NULL
    if not rows[0]["pfp_filename"]:
        filepath = "static/default_pfp.jpeg"
    else:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], rows[0]["pfp_filename"])
    
    # Relative path of template files to static directory
    filepath = "../" + filepath
    
    return render_template("profile.html", filepath=filepath, self_profile=self_profile)


@app.route("/remove_pfp")
@login_required
def remove_pfp():
    # Retrieve filename from db
    rows = execute_retrieve("SELECT pfp_filename FROM user WHERE id = :user_id", 
                                {"user_id": session["user_id"]})
    
    if not rows[0]["pfp_filename"]:
        return flash_and_redirect("PFP already default!", "profile", username=session.get("username"))
    else:
        # Remove file from filesystem
        existing_pfp_filename = rows[0]["pfp_filename"]
        existing_pfp_filepath = os.path.join(app.config["UPLOAD_FOLDER"], existing_pfp_filename)
        os.remove(existing_pfp_filepath)
    
        # Remove filename from db
        execute("UPDATE user SET pfp_filename = NULL WHERE id = :user_id", {
            "user_id": session["user_id"]})
        
        return redirect(url_for("profile", username=session.get("username")))        


@app.route("/upload_pfp", methods=["POST"])
@login_required
def upload_pfp():
    if request.method == "POST":
        file = request.files.get("upload_pfp")
        
        # Validation
        if not file:
            return flash_and_redirect("Choose a file!", "profile", username=session.get("username"))
        
        if not allowed_file(file.filename):
            return flash_and_redirect("Choose correct file type!", "profile", username=session.get("username"))
            
        if len(file.filename) > 50:
            return flash_and_redirect("File name should be less than 50 characters! GEEZ!", "profile", username=session.get("username"))        
        
        # Generate secure filename as filename+timestamp and
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        
        # Remove older file if exists
        rows = execute_retrieve("SELECT pfp_filename FROM user WHERE id = :user_id", 
                                {"user_id": session["user_id"]})
        
        if rows[0]["pfp_filename"]:
            existing_pfp_filename = rows[0]["pfp_filename"]
            existing_pfp_filepath = os.path.join(app.config["UPLOAD_FOLDER"], existing_pfp_filename)
            os.remove(existing_pfp_filepath)
        
        # Insert filename into db
        execute("UPDATE user SET pfp_filename = :filename WHERE id = :user_id", 
                {"filename": filename, "user_id": session["user_id"]})
        
        # Save file to filesystem
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        
        return redirect(url_for("profile", username=session.get("username")))