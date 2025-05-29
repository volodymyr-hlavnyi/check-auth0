from models import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sub = db.Column(db.String(64), unique=True, nullable=False)  # Auth0 user_id
    name = db.Column(db.String(256), nullable=False)  # Full name
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    email = db.Column(db.String(128), unique=True)
    picture = db.Column(db.String(256))
    registered_at = db.Column(db.DateTime, nullable=False)
    last_updated_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"
