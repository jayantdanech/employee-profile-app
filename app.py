from flask import Flask, request, render_template, jsonify, redirect, url_for
import boto3, pymysql, uuid, os
from datetime import datetime

app = Flask(__name__)

# Switch to True when testing locally
LOCAL_DEV = True

# Environment variables (used only in AWS mode)
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASS = os.environ.get("DB_PASS", "mypass")
UPLOADS_BUCKET = os.environ.get("UPLOADS_BUCKET", "dummybucket")
DDB_TABLE = os.environ.get("DDB_TABLE", "dummytable")

# Initialize AWS clients only if NOT in local mode
if not LOCAL_DEV:
    s3 = boto3.client("s3")
    dynamodb = boto3.resource("dynamodb")
else:
    s3 = None
    dynamodb = None
    print("### LOCAL DEV MODE ENABLED — AWS SERVICES DISABLED ###")

def get_db_conn():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        db="employee_db",
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    location = request.form["location"]
    age = request.form["age"]
    technology = request.form["technology"]
    salary = request.form["salary"]
    photo = request.files["photo"]

    image_id = str(uuid.uuid4())
    s3_key = f"employees/{image_id}_{photo.filename}"

    # Upload to AWS S3
    if not LOCAL_DEV:
        s3.upload_fileobj(photo, UPLOADS_BUCKET, s3_key)
    else:
        print("LOCAL DEV: Skipping S3 upload:", s3_key)

    # Store meta
