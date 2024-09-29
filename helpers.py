from functools import wraps
from flask import flash, redirect, session, url_for

# Uploading files
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def flash_and_redirect(msg: str, func: str, **kwargs):
    flash(msg)
    return redirect(url_for(func, **kwargs))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def log_user_in(user_id: int, username: str):
    session.permanent = True  # For making a session permanent - so that it exists even after the browser is closed
    session["user_id"] = user_id
    session["username"] = username