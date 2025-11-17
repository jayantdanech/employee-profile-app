from flask import Flask, request, render_template, jsonify, redirect, url_for
import pymysql, uuid, os
from datetime import datetime

# --------------------------------------------
# Detect AWS Mode or Local Mode
# --------------------------------------------
LOCAL_DEV = os.environ.get("LOCAL_DEV", "false").lower() == "true"

if LOCAL_DEV:
    print("### LOCAL DEV MODE ENABLED — AWS SERVICES DISABLED ###")
else:
    print("### AWS MODE ENABLED — RDS / S3 / DYNAMODB ACTIVE ###")
    import boto3

app = Flask(__name__)

# --------------------------------------------
# Environment Variables
# --------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "mysql")
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASS = os.environ.get("DB_PASS", "mypass")
DB_NAME = os.environ.get("DB_NAME", "employee_db")

UPLOADS_BUCKET = os.environ.get("UPLOADS_BUCKET", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


# --------------------------------------------
# MySQL DB Connection
# --------------------------------------------
def get_db_conn():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


# ======================================================
# PAGE 1 — MAIN PAGE (Employee Input)
# ======================================================
@app.route("/")
def main_page():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    location = request.form["location"]
    age = request.form["age"]
    technology = request.form["technology"]
    salary = request.form["salary"]
    photo = request.files["photo"]

    # Generate unique file name
    image_id = str(uuid.uuid4())
    file_name = f"{image_id}_{photo.filename}"

    # -----------------------------------------------------
    # AWS MODE — Upload Photo to S3 + Store metadata DynamoDB
    # -----------------------------------------------------
    if not LOCAL_DEV:

        # Upload image to S3
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.upload_fileobj(photo, UPLOADS_BUCKET, file_name)

        # Metadata → DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = dynamodb.Table("employee_photos")

        table.put_item(Item={
            "image_id": image_id,
            "file_name": file_name,
            "uploaded_at": str(datetime.utcnow())
        })

        print(f"Uploaded file to S3 and metadata to DynamoDB: {file_name}")

    else:
        print("LOCAL DEV: Simulated upload:", file_name)

    # -----------------------------------------------------
    # INSERT EMPLOYEE RECORD INTO RDS
    # -----------------------------------------------------
    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO employees (name, location, age, technology, salary, photo_s3_key)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, location, age, technology, salary, file_name))
        conn.commit()
        conn.close()
        print("DB Insert Successful")

    except Exception as e:
        print("DB Insert Error:", e)

    return redirect(url_for("main_page"))


# ======================================================
# PAGE 2 — ABOUT US PAGE
# From Architecture: Page served from S3 (static hosting)
# App only redirects or shows a button
# ======================================================
@app.route("/about")
def about():
    # This is where your static S3 website URL goes
    about_url = os.environ.get("ABOUT_US_URL", "#")
    return render_template("about.html", s3_about_url=about_url)


# ======================================================
# PAGE 3 — EMPLOYEE LOOKUP (Employee ID)
# ======================================================
@app.route("/employee")
def employee_lookup_page():
    return render_template("employee.html")


@app.route("/get_employee", methods=["POST"])
def get_employee():
    emp_id = request.form.get("emp_id")
    name = request.form.get("name")

    if not emp_id and not name:
        return jsonify({"error": "Please enter Employee ID or Name"})

    try:
        conn = get_db_conn()
        with conn.cursor() as cur:

            # Priority 1 — Find by ID
            if emp_id:
                cur.execute("SELECT * FROM employees WHERE id=%s", (emp_id,))
                result = cur.fetchone()
                if result:
                    conn.close()
                    return jsonify(result)

            # Priority 2 — Find by Name (search all possible matches)
            if name:
                cur.execute("SELECT * FROM employees WHERE name LIKE %s", (f"%{name}%",))
                results = cur.fetchall()
                conn.close()
                return jsonify(results if results else {"error": "No matching employee found"})

        conn.close()
    except Exception as e:
        return jsonify({"error": f"DB Error: {e}"})


# ======================================================
# HEALTH CHECK ENDPOINT
# ======================================================
@app.route("/health")
def health():
    return "OK", 200


# ======================================================
# START FLASK SERVER
# ======================================================
if __name__ == "__main__":
    print("Starting Flask server on 0.0.0.0:5000 ...")
    app.run(host="0.0.0.0", port=5000)
