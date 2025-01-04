import os.path
import boto3

from database import execute, execute_retrieve
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, redirect, request, session, url_for
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from helpers import *
from markupsafe import escape
from pytz import timezone
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from flask_apscheduler import APScheduler  # render.com inactivity prevention

app = Flask(__name__)
s3 = boto3.client("s3")
socketio = SocketIO(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
scheduler.add_job(id="send_GET", func=send_get, trigger="interval", seconds=600)

# S3 Stuff
aws_bucket_name = os.environ["AWS_BUCKET_NAME"]
app.jinja_env.globals.update(url_for_pfp=url_for_pfp)
# Permanent Session
app.secret_key = os.environ["APP_KEY"].encode("utf-8")
app.permanent_session_lifetime = timedelta(minutes=69)
# Uploading Files
app.config["MAX_CONTENT_LENGTH"] = 64 * 1000 * 1000  # 64MB
#Time Zone
IST = timezone("Asia/Kolkata")


@socketio.on("connect")
def connect():
    # execute("UPDATE user SET is_online = TRUE WHERE id = :id", 
    #         {"id": session.get("user_id")})
    
    print(f"{session.get('username')} established connection to the socket.")


@socketio.on("disconnect")
def disconnect():
    leave_room(session.get("room_code"))


@socketio.on("join_a_room")
def join_a_room(friend_id):
    if (session.get("room_code")):
        leave_room(session.get("room_code"))
    
    low, high = sorted([session.get("user_id"), friend_id])
    
    rows = execute_retrieve("""
        SELECT id AS friendship_id
        FROM friendships
        WHERE (low_friend_id = :low AND high_friend_id = :high);
    """, {"low": low, "high": high})
    
    if len(rows) == 0:
        return
    
    session["room_code"] = rows[0]["friendship_id"]
    join_room(session.get("room_code"))
    
    # Load the previous messages
    rows = execute_retrieve("""
        SELECT 
            sender.username AS msg_from_username, 
            receiver.username AS msg_to_username, 
            m.msg AS msg, 
            m.timestamp AS timestamp
        FROM 
            user sender, 
            user receiver, 
            messages m
        WHERE 
            m.msg_from = sender.id
            AND m.msg_to = receiver.id
            AND ((receiver.id = :user_id AND sender.id = :friend_id) OR (receiver.id = :friend_id AND sender.id = :user_id))
        ORDER BY 
            timestamp ASC;
    """, {"user_id": session.get("user_id"), "friend_id": friend_id})
    
    for row in rows:
        timestamp = row["timestamp"]
        row["timestamp"] = f"{timestamp[8:10]}:{timestamp[10:12]} {timestamp[0:4]}/{timestamp[4:6]}/{timestamp[6:8]}"
    
    emit("load_messages", rows, json=True)
    

@socketio.on("message")
def message(data):  
    rows = execute_retrieve("SELECT id AS friend_id FROM user WHERE username = :username", 
                            {"username": data["msg_to"]})
    
    timestamp = datetime.now(tz=IST).strftime(r"%Y%m%d%H%M%S%f")
    
    execute("""
        INSERT INTO messages (
            msg_from, 
            msg_to, 
            msg, 
            timestamp
        ) VALUES (
            :msg_from, 
            :msg_to, 
            :msg, 
            :timestamp)
    """, {
        "msg_from": session.get("user_id"), 
        "msg_to": rows[0]["friend_id"], 
        "msg": data["message"],
        "timestamp": timestamp
    })
    
    json_data = {
        "msg_from_username": session.get("username"),
        "msg_to_username": data["msg_to"],
        "msg": data["message"],
        "timestamp": f"{timestamp[8:10]}:{timestamp[10:12]} {timestamp[0:4]}/{timestamp[4:6]}/{timestamp[6:8]}"
    }
    
    send(json_data, to=session.get("room_code"))


@app.route("/")
@login_required
def index():   
    rows = execute_retrieve("""
        SELECT 
            f.id AS friendship_id, 
            f.friend_id, 
            user.username, 
            user.pfp_filename
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
    
    return render_template("index.html", rows=rows, index=True)


@app.route("/friends/myfriends")
@login_required
def myfriends():    
    rows = execute_retrieve("""
        SELECT 
            f.id AS friendship_id, 
            f.friend_id, 
            user.username, 
            user.pfp_filename
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
    
    rows = execute_retrieve("SELECT low_friend_id, high_friend_id FROM friendships WHERE id = :id",
                                {"id": friendship_id})
        
    ids = [rows[0]["low_friend_id"], rows[0]["high_friend_id"]]
    
    if session["user_id"] not in ids:
        return flash_and_redirect("Friendship removal not allowed.", "myfriends")
        
    execute("DELETE FROM friendships WHERE id = :friendship_id", {"friendship_id": friendship_id})  
    
    return flash_and_redirect("Friend Removed!", "myfriends")


@app.route("/friends/friendrequests")
@login_required
def friendrequests():    
    rows = execute_retrieve("""
        SELECT 
            friend_requests.id AS req_id, 
            user.username, 
            user.pfp_filename
        FROM 
            friend_requests, 
            user
        WHERE 
            friend_requests.req_to = :to 
            AND friend_requests.req_from = user.id;
    """, {"to": session.get("user_id")})
    
    return render_template("friendrequests.html", rows=rows)


@app.route("/friends/friendrequests/reject", methods=["POST"])
@login_required
def rejectfriendrequest():
    if request.method == "POST":
        req_id = request.form.get("req_id")
        
        rows = execute_retrieve("SELECT req_to FROM friend_requests WHERE id = :id", {"id": req_id})
        
        if rows[0]["req_to"] != session["user_id"]:
            return flash_and_redirect("This rejection is not possible.")
        
        execute("DELETE FROM friend_requests WHERE id = :id", {"id": req_id})
        return flash_and_redirect("Friend request rejected!", "friendrequests")
    

@app.route("/friends/friendrequests/accept", methods=["POST"])
@login_required
def acceptfriendrequest():
    if request.method == "POST":
        req_id = int(request.form.get("req_id"))
        
        rows = execute_retrieve("SELECT req_from, req_to FROM friend_requests WHERE id = :req_id", 
                                {"req_id": req_id})
                
        if rows[0]["req_to"] != session.get("user_id"):
            return flash_and_redirect("This friend request can't be accepted.", "friendrequests")
        
        low_friend_id, high_friend_id = sorted([rows[0]["req_from"], session.get("user_id")])
        
        execute("INSERT INTO friendships (low_friend_id, high_friend_id) VALUES (:low_friend_id, :high_friend_id)",
                {"low_friend_id": low_friend_id, "high_friend_id": high_friend_id})
        
        execute("DELETE FROM friend_requests WHERE id = :id", {"id": req_id})
        
        return flash_and_redirect("Friend request accepted!", "friendrequests")


@app.route("/friends/sendfriendrequests", methods=["GET", "POST"])
@login_required
def sendfriendrequests():
    if request.method == "POST":
        username = request.form.get("username")
        
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
        
        # Check for already present reverse friend request
        rows = execute_retrieve("SELECT id FROM friend_requests WHERE req_from = :from AND req_to = :to",
                                {"from": to_friend_id, "to": session.get("user_id")})
        
        if rows:
            execute("DELETE FROM friend_requests WHERE id = :id",
                    {"id": rows[0]["id"]})
            
            execute("INSERT INTO friendships (low_friend_id, high_friend_id) VALUES (:low_friend_id, :high_friend_id)",
                    {"low_friend_id": low_friend_id, "high_friend_id": high_friend_id})
            
            return flash_and_redirect("They had sent you a request, now you're both friends!", "sendfriendrequests")
        
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

        if not username:
            return flash_and_redirect("Enter name!", "login")
        
        if not password:
            flash("Enter password!")
            return render_template("login.html", username=username)
        
        rows = execute_retrieve("SELECT id, hash FROM user WHERE username = :username", {"username" : username})
                        
        if not rows or not check_password_hash(rows[0]["hash"], password):
            flash("Enter correct username/password!")
            return render_template("login.html", username=username)
        
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
        
        if not username:
            return flash_and_redirect("Enter username!", "register")
        
        if not password:
            flash("Enter password!")
            return render_template("register.html", username=username)
        
        if not confirmation:
            flash("Re-enter password!")
            return render_template("register.html", username=username, password=password)
        
        if password != confirmation:
            flash("Passwords don't match!")
            return render_template("register.html", username=username, password=password, confirmation=confirmation)
                
        rows = execute_retrieve("SELECT id FROM user WHERE username = :username", {"username":username})
        
        if rows:
            return flash_and_redirect("Username already taken!", "register")
                
        execute("INSERT INTO user (username, hash) VALUES (:username, :hash)", 
                {"username":username, "hash":generate_password_hash(password)})

        rows = execute_retrieve("SELECT id FROM user WHERE username = :username", {"username":username})
        log_user_in(rows[0]["id"], username)
        
        return flash_and_redirect("Successfully Registered and Logged-In!", "index")
    else:
        return render_template("register.html")
    

@app.route("/profile/<username>")
@login_required
def profile(username):
    username = str(escape(username))
    
    if username == session.get("username"):
        self_profile = True
    else:
        self_profile = False
    
    rows = execute_retrieve("SELECT username, pfp_filename, name, bio FROM user WHERE username = :username", 
                            {"username": username})
    
    return render_template("profile.html", row=rows[0], self_profile=self_profile)


@app.route("/profile/inline_edit", methods=["POST"])
@login_required
def inline_edit():
    field = request.json.get("field")
    value = request.json.get("value")
    
    execute(f"UPDATE user SET {field} = :value WHERE id = :id",
            {"value": value, "id": session.get("user_id")})
    
    return jsonify({"status": "success"})


@app.route("/remove_pfp")
@login_required
def remove_pfp():
    rows = execute_retrieve("SELECT pfp_filename FROM user WHERE id = :user_id", 
                                {"user_id": session.get("user_id")})
    
    if rows[0]["pfp_filename"] == "default_pfp.jpeg":
        return flash_and_redirect("PFP already default!", "profile", username=session.get("username"))
    else:
        s3.delete_object(Bucket=aws_bucket_name, Key=rows[0]["pfp_filename"])
    
        execute("UPDATE user SET pfp_filename = 'default_pfp.jpeg' WHERE id = :user_id", {
            "user_id": session.get("user_id")})
        
        return redirect(url_for("profile", username=session.get("username")))        


@app.route("/upload_pfp", methods=["POST"])
@login_required
def upload_pfp():
    if request.method == "POST":
        file = request.files.get("upload_pfp")
        
        if not file:
            return flash_and_redirect("Choose a file!", "profile", username=session.get("username"))
        
        if not allowed_file(file.filename):
            return flash_and_redirect("Choose correct file type!", "profile", username=session.get("username"))
            
        if len(file.filename) > 50:
            return flash_and_redirect("File name should be less than 50 characters! GEEZ!", "profile", username=session.get("username"))        
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now(tz=IST).strftime("%Y%m%d_%H%M%S%f")
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        
        rows = execute_retrieve("SELECT pfp_filename FROM user WHERE id = :user_id", 
                                {"user_id": session.get("user_id")})
        
        older_filename = rows[0]["pfp_filename"]
        
        if older_filename != "default_pfp.jpeg":
            s3.delete_object(Bucket=aws_bucket_name, Key=older_filename)
        
        execute("UPDATE user SET pfp_filename = :filename WHERE id = :user_id", 
                {"filename": filename, "user_id": session.get("user_id")})
        
        s3.upload_fileobj(file, aws_bucket_name, filename)
        
        return redirect(url_for("profile", username=session.get("username")))


if __name__ == "__main__":
    socketio.run(app, allow_unsafe_werkzeug=True, host="0.0.0.0")