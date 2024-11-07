import os.path

from database import execute, execute_retrieve
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, request, session, url_for
from flask_socketio import SocketIO
from helpers import allowed_file, flash_and_redirect, log_user_in, login_required
from markupsafe import escape
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
socketio = SocketIO(app)
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
    # TODO: Implement home page
    
    return render_template("index.html", username=session.get("username"))


@app.route("/friends/myfriends")
@login_required
def myfriends():
    
    # TODO: Move query to helper function
    
    rows = execute_retrieve("""
        SELECT f.id AS friendship_id, f.friend_id, user.username, user.pfp_filename
        FROM
        (
            SELECT friendships.id,
                CASE
                    WHEN low_friend_id = :user_id THEN high_friend_id
                    ELSE low_friend_id
                END AS friend_id
            FROM friendships
            WHERE low_friend_id = :user_id OR high_friend_id = :user_id
        ) AS f
        JOIN user ON user.id = f.friend_id
    """, {"user_id": session.get("user_id")})
    
    return render_template("myfriends.html", rows=rows)


@app.route("/friends/myfriends/remove", methods=["POST"])
@login_required
def remove():
    friendship_id = request.form.get("friendship_id")
    
    # TODO: Validate whether the session user is a part of that friendship-id  #NeverTrustUserInput
    
    execute("DELETE FROM friendships WHERE id = :friendship_id", {"friendship_id": friendship_id})
    
    return flash_and_redirect("Friend Removed!", "myfriends")


@app.route("/friends/friendrequests")
@login_required
def friendrequests():
    
    # TODO: Move query to helper function
    
    rows = execute_retrieve("""
        SELECT friend_requests.id AS req_id, user.id AS user_id, user.username, user.pfp_filename
        FROM friend_requests, user
        WHERE friend_requests.req_to = :to
        AND friend_requests.req_from = user.id;
    """, {"to": session.get("user_id")})
    
    return render_template("friendrequests.html", rows=rows)


@app.route("/friends/friendrequests/reject", methods=["POST"])
@login_required
def rejectfriendrequest():
    if request.method == "POST":
        id = request.form.get("req_id")
        
        # TODO: Validate whether the session user is a part of the request-id  #NeverTrustUserInput
        
        execute("DELETE FROM friend_requests WHERE id = :id", {"id": id})
        return flash_and_redirect("Friend request rejected!", "friendrequests")
    

@app.route("/friends/friendrequests/accept", methods=["POST"])
@login_required
def acceptfriendrequest():
    if request.method == "POST":
        req_id = int(request.form.get("req_id"))
        user_id = int(request.form.get("user_id"))
        
        # TODO: Validate whether that friend-request exists or not  #NeverTrustUserInput
        
        low_friend_id, high_friend_id = sorted([session.get("user_id"), user_id])
        
        execute("INSERT INTO friendships (low_friend_id, high_friend_id) VALUES (:low_friend_id, :high_friend_id)",
                {"low_friend_id": low_friend_id, "high_friend_id": high_friend_id})
        
        execute("DELETE FROM friend_requests WHERE id = :id", {"id": req_id})
        
        return flash_and_redirect("Friend request accepted!", "friendrequests")


@app.route("/friends/sendfriendrequests", methods=["GET", "POST"])
@login_required
def sendfriendrequests():
    if request.method == "POST":
        username = request.form.get("username")
        
        # Validate input
        if not username:
            return flash_and_redirect("Enter username!", "sendfriendrequests")
        
        if username == session.get("username"):
            return flash_and_redirect("Cannot send friend request to yourself!", "sendfriendrequests")
        
        rows = execute_retrieve("SELECT id FROM user WHERE username = :username", 
                                {"username": username})
        
        if not rows:
            return flash_and_redirect("No such user found!", "sendfriendrequests")
        
        to_friend_id = rows[0]["id"]
        
        rows = execute_retrieve("SELECT id FROM friend_requests WHERE req_from = :from AND req_to = :to", 
                                {"from": session.get("user_id"), "to": to_friend_id})
        
        if rows:
            return flash_and_redirect("Friend request already sent!", "sendfriendrequests")
        
        low_friend_id, high_friend_id = sorted([session.get("user_id"), to_friend_id])
        
        rows = execute_retrieve("SELECT id FROM friendships WHERE low_friend_id = :low AND high_friend_id = :high",
                                {"low": low_friend_id, "high": high_friend_id})
        
        if rows:
            return flash_and_redirect("They're already your friend!", "sendfriendrequests")
        
        execute("INSERT INTO friend_requests (req_from, req_to) VALUES (:from, :to)", 
                {"from": session.get("user_id"), "to": to_friend_id})
        
        return flash_and_redirect("Friend request sent!", "sendfriendrequests")
    else:
        return render_template("sendfriendrequests.html")


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
    
    if username == session.get("username"):
        self_profile = True
    else:
        self_profile = False
    
    rows = execute_retrieve("SELECT pfp_filename FROM user WHERE username = :username", 
                            {"username": username})
    
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], rows[0]["pfp_filename"])
    
    # Relative path of template files to static directory
    filepath = "../" + filepath
    
    return render_template("profile.html", filepath=filepath, self_profile=self_profile)


@app.route("/remove_pfp")
@login_required
def remove_pfp():
    # Retrieve filename from db
    rows = execute_retrieve("SELECT pfp_filename FROM user WHERE id = :user_id", 
                                {"user_id": session.get("user_id")})
    
    if rows[0]["pfp_filename"] == "default_pfp.jpeg":
        return flash_and_redirect("PFP already default!", "profile", username=session.get("username"))
    else:
        # Remove file from filesystem
        existing_pfp_filename = rows[0]["pfp_filename"]
        existing_pfp_filepath = os.path.join(app.config["UPLOAD_FOLDER"], existing_pfp_filename)
        os.remove(existing_pfp_filepath)
    
        # Set filename to default_pfp in db
        execute("UPDATE user SET pfp_filename = 'default_pfp.jpeg' WHERE id = :user_id", {
            "user_id": session.get("user_id")})
        
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
                                {"user_id": session.get("user_id")})
        
        if rows[0]["pfp_filename"] and rows[0]["pfp_filename"] != "default_pfp.jpeg":
            existing_pfp_filename = rows[0]["pfp_filename"]
            existing_pfp_filepath = os.path.join(app.config["UPLOAD_FOLDER"], existing_pfp_filename)
            os.remove(existing_pfp_filepath)
        
        # Insert filename into db
        execute("UPDATE user SET pfp_filename = :filename WHERE id = :user_id", 
                {"filename": filename, "user_id": session.get("user_id")})
        
        # Save file to filesystem
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        
        return redirect(url_for("profile", username=session.get("username")))


if __name__ == "__main__":
    socketio.run(app, debug=True)