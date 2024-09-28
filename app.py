from database import execute, execute_retrieve
from datetime import timedelta
from flask import Flask, render_template, redirect, request, session, url_for
from helpers import log_user_in, login_required
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
# Permanent Session
app.secret_key = "stfu"
app.permanent_session_lifetime = timedelta(minutes=69)
# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


@app.route("/")
@login_required
def index():
    return render_template("index.html", username=session.get("username"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Retrieve form data
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate form data
        if not username:
            print("Please enter a username")
            return redirect(url_for("login"))
        
        if not password:
            print("Please enter a password")
            return redirect(url_for("login"))
        
        # Get user data from the database
        rows = execute_retrieve("SELECT id, hash FROM user WHERE username = :username", {"username" : username})
                        
        # Check if user doesn't exist from db OR password doesn't match [fused for security]
        if not rows or not check_password_hash(rows[0]["hash"], password):
            print("Enter correct username / password!")
            return redirect(url_for("login"))
        
        log_user_in(rows[0]["id"], username)
        return redirect(url_for("index"))
    else:
        # If user is already logged-in
        if "user_id" in session:
            return redirect(url_for("index"))
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
        # Retrieve form data
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        # Validate form data
        if not username:
            print("Please enter a username.")
            return redirect(url_for("register"))
        
        if not password:
            print("Please enter a password.")
            return redirect(url_for("register"))
        
        if not confirmation:
            print("Please re-enter password.")
            return redirect(url_for("register"))
        
        # Check if username already exists
        rows = execute_retrieve("SELECT id FROM user WHERE username = :username", {"username":username})
        
        if rows:
            print("Username already taken!")
            return redirect(url_for("register"))
        
        # Check password and confirmation not matching
        if password != confirmation:
            print("Passwords don't match!")
            return redirect(url_for("register"))
        
        # Insert data into table
        execute("INSERT INTO user (username, hash) VALUES (:username, :hash)", 
                {"username":username, "hash":generate_password_hash(password)})

        # Log-in the user
        rows = execute_retrieve("SELECT id FROM user WHERE username = :username", {"username":username})
        log_user_in(rows[0]["id"], username)
        return redirect(url_for("index"))
    else:
        return render_template("register.html")
    

@app.route("/profile/<username>")
@login_required
def profile(username):
    # TODO : implement profile page
    
    return f"Welcome to your profile {username}"