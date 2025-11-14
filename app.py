from flask import Flask, request, render_template, jsonify, redirect, url_for
import pymysql, uuid, os
from datetime import datetime

# --------------------------------------------
# Local Dev Mode — No AWS
# --------------------------------------------
LOCAL_DEV = True
print("### LOCAL DEV MODE ENABLED — AWS SERVICES DISABLED ###")

app = Flask(__name__)

# --------------------------------------------
# Environment Variables (Defaults for Local)
# --------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "mysql")
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASS = os.environ.get("DB_PASS", "mypass")
DB_NAME = "employee_db"

def get_db_conn():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

# --------------------------------------------
# PAGE 1 — Main Page (Employee Input)
# --------------------------------------------
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

    image_id = str(uuid.uuid4())
    file_name = f"{image_id}_{photo.filename}"

    # Skip AWS (Dev Mode)
    print("LOCAL DEV: Uploaded file simulated:", file_name)

    # Insert into MySQL
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


# --------------------------------------------
# PAGE 2 — About Us Page (Simulating S3)
# --------------------------------------------
@app.route("/about")
def about():
    return render_template("about.html")


# --------------------------------------------
# PAGE 3 — Employee Information Lookup
# --------------------------------------------
@app.route("/employee")
def employee_lookup_page():
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
        return jsonify({"error": f"DB Error: {e}"})

    return jsonify(result if result else {"error": "Employee Not Found"})


@app.route("/health")
def health():
    return "OK", 200


# --------------------------------------------
# START FLASK SERVER
# --------------------------------------------
if __name__ == "__main__":
    print("Starting Flask server on 0.0.0.0:5000 ...")
    app.run(host="0.0.0.0", port=5000)
