import os
import logging
from urllib.parse import quote_plus

from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, validators
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from sqlalchemy import text
from dotenv import load_dotenv

# load_dotenv()  # IMPORTANT: uncomment if using .env file for environment variables
env = lambda key: os.getenv(key)

db_username = quote_plus(env('DB_USERNAME'))
db_password = quote_plus(env('DB_PASSWORD'))
db_host = quote_plus(env('DB_HOST'))
db_port = quote_plus(env('DB_PORT'))
db_name = quote_plus(env('DB_NAME'))
database_connection_string = f"mysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

app = Flask(__name__)
app.secret_key = env("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = database_connection_string
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['LOG_LEVEL'] = logging.INFO
app.config['LOG_FORMAT'] = '%(asctime)s - %(levelname)s - %(message)s'

logging.basicConfig(level=app.config['LOG_LEVEL'], format=app.config['LOG_FORMAT'])

db = SQLAlchemy(app)

limiter = Limiter(
    app,
    storage_uri=env("memory://")
)


class EmailModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userEmail = db.Column(db.String(200), unique=True, nullable=False)


class EmailForm(FlaskForm):
    userEmail = StringField("Email", [validators.DataRequired(), validators.Email()])


@app.route("/", methods=("GET", "POST"))
@limiter.limit("15 per minute")
def index():
    form = EmailForm()
    message = None

    if form.validate_on_submit():
        email = form.userEmail.data
        existing_email = EmailModel.query.filter_by(userEmail=email).first()

        if not existing_email:
            new_email = EmailModel(userEmail=email)
            db.session.add(new_email)
            db.session.commit()
            message = f"Thank you for providing your email. I'll be sure to inform you when the website is ready!"
        else:
            form.userEmail.errors.append("This email has already been submitted")

    # Quick check to see that the database is working
    try:
        db.session.execute(text("SELECT 1")).fetchall()
    except Exception as e:
        logging.error(f"Error executing query: {e}")

    return render_template("index.html", form=form, message=message)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
