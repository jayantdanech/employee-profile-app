from flask import Flask, request, render_template, jsonify, redirect, url_for
import pymysql, uuid, os
from datetime import datetime

# --------------------------------------------
# Local Dev Mode
# --------------------------------------------
LOCAL_DEV = True   # Set to False when deploying to AWS
print("### LOCAL DEV MODE ENABLED — AWS SERVICES DISABLED ###")

app = Flask(__name__)

# --------------------------------------------
# Environment variables (use defaults for local)
# --------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "mysql")      # MySQL container name
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASS = os.environ.get("DB_PASS", "mypass")
DB_NAME = "employee_db"

UPLOADS_BUCKET = os.environ.get("UPLOADS_BUCKET", "dummybucket")
DDB_TABLE = os.environ.get("DDB_TABLE", "dummytable")

# --------------------------------------------
# Database Connection Helper
# --------------------------------------------
def get_db_conn():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

# --------------------------------------------
# Routes
# --------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    location = request.form["location"]
    age = request.form["age"]
    technology = request.form["technology"]
    salary = request.form["salary"]
    photo = request.files["photo"]

    # Generate UUID for filename
    image_id = str(uuid.uuid4())
    s3_key = f"employees/{image_id}_{photo.filename}"

    # --------------------------------------------
    # SKIP AWS for Local Dev
    # --------------------------------------------
    if LOCAL_DEV:
        print(f"LOCAL DEV: Skipping S3 upload for: {s3_key}")
        print(f"LOCAL DEV: Skipping DynamoDB write for image_id {image_id}")
    else:
        # Add real AWS upload here for production
        pass

    # --------------------------------------------
    # Insert into MySQL DB
    # --------------------------------------------
    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO employees (name, location, age, technology, salary, photo_s3_key) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (name, location, age, technology, salary, s3_key)
            )
        conn.commit()
        conn.close()
        print("DB Insert OK")
    except Exception as e:
        print("ERROR inserting into DB:", e)

    return redirect(url_for("index"))


@app.route("/employee")
def employee_page():
    return render_template("employee.html")


@app.route("/get_employee", methods=["POST"])
def get_employee():
    emp_id = request.form["emp_id"]

    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM employees WHERE id=%s", (emp_id,))
            result = cur.fetchone()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"DB error: {e}"})

    return jsonify(result if result else {"error": "Employee not found"})


@app.route("/health")
def health():
    return "OK", 200


# --------------------------------------------
# START FLASK SERVER
# --------------------------------------------
if __name__ == "__main__":
    print("Starting Flask server on 0.0.0.0:5000 ...")
    app.run(host="0.0.0.0", port=5000)
