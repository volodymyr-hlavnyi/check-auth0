"""Python Flask WebApp Auth0 integration example
"""
import datetime
import json
import logging
import secrets
import os

from datetime import datetime

from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for
from flask_migrate import Migrate

from logging import basicConfig, INFO

from models import db
from models.user import User

# Configure logging
basicConfig(
    level=INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

BASEDIR = os.path.abspath(os.path.dirname(__file__))
relative_path = os.path.join(BASEDIR, "db", env.get("DATABASE_NAME", "auth0_users.db"))
DATABASE_URL = f"sqlite:///{relative_path}"

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

migrate = Migrate(app, db)

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


# Controllers API
@app.route("/")
def home():
    return render_template(
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    nonce = session.pop("nonce", None)
    userinfo = oauth.auth0.parse_id_token(token, nonce=nonce)

    u = db.session.query(User).filter_by(sub=userinfo["sub"]).first()
    if not u:
        u = User(sub=userinfo["sub"])
        u.registered_at = datetime.now()
        db.session.add(u)

    u.name = userinfo.get("name")
    u.first_name = userinfo.get("given_name")
    u.last_name = userinfo.get("family_name")
    u.email = userinfo.get("email")
    u.picture = userinfo.get("picture")
    u.last_updated_at = datetime.now()

    db.session.commit()

    logging.info(f"User {u.email} logged in successfully at {u.last_updated_at}, first at {u.registered_at}.")

    return redirect("/")


@app.route("/login")
def login():
    nonce = secrets.token_urlsafe(16)
    session["nonce"] = nonce
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True),
        nonce=nonce,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        logging.info("Database tables created successfully.")
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))
