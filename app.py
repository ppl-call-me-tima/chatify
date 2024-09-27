from flask import Flask, render_template, redirect, request, session, url_for
from datetime import timedelta

app = Flask(__name__)
# Permanent Session
app.secret_key = "stfu"
app.permanent_session_lifetime = timedelta(minutes=69)
# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


@app.route("/")
def index():
    # if user logged-in
    if "user_id" in session:
        return render_template("index.html", user_id=session["user_id"])
    else:
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # for making a session permanent - so that it exists even after a browser is closed
        session.permanent = True
        
        username = request.form.get("username")
        password = request.form.get("password")

        # TODO : validation of the input fields
        
        # TODO : check if the user exists from database
        
        # TODO : log the user in, using its id instead of username

        return redirect(url_for("index"))
    else:
        if "user_id" in session:
            return redirect(url_for("index"))
        else:
            return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        pass
    else:
        return render_template("register.html")