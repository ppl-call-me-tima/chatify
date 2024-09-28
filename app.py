from flask import Flask, render_template, redirect, request, session, url_for
from database import execute, execute_retrieve
from datetime import timedelta
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
# Permanent Session
app.secret_key = "stfu"
app.permanent_session_lifetime = timedelta(minutes=69)
# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


@app.route("/")
def index():
    # If user is logged-in
    if "user_id" in session:
        return render_template("index.html", user_id=session["user_id"])
    else:
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # For making a session permanent - so that it exists even after a browser is closed
        session.permanent = True
        
        username = request.form.get("username")
        password = request.form.get("password")

        # Validation of the input fields
        if not username:
            print("Please enter a username")
            return redirect(url_for("login"))
        
        if not password:
            print("Please enter a password")
            return redirect(url_for("login"))
        
        # Gets user data from the database
        rows = execute_retrieve("SELECT id, hash FROM user WHERE username = :username", {"username" : username})
                        
        # Checks if the user exists from database OR password doesn't match [fused for security]
        if not rows or not check_password_hash(rows[0]["hash"], password):
            print("Enter correct username / password!")
            return redirect(url_for("login"))
        
        # Logs the user in, using its ID instead of username
        session["user_id"] = rows[0]["id"]
        return redirect(url_for("index"))
    else:
        # If user is already logged-in
        if "user_id" in session:
            return redirect(url_for("index"))
        else:
            return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        pass
    else:
        return render_template("register.html")