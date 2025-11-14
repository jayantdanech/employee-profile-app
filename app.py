from flask import Flask, request, render_template, jsonify, redirect, url_for
import boto3, pymysql, uuid, os
from datetime import datetime

app = Flask(__name__)

# Environment variables (set in EC2 or ASG launch template)
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
UPLOADS_BUCKET = os.environ.get("UPLOADS_BUCKET")
DDB_TABLE = os.environ.get("DDB_TABLE")

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def get_db_conn():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        db='employee_db',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    location = request.form['location']
    age = request.form['age']
    technology = request.form['technology']
    salary = request.form['salary']
    photo = request.files['photo']

    s3_key = None
    image_id = str(uuid.uuid4())

    if photo:
        s3_key = f"employees/{image_id}_{photo.filename}"
        s3.upload_fileobj(photo, UPLOADS_BUCKET, s3_key)

        # Save metadata in DynamoDB
        table = dynamodb.Table(DDB_TABLE)
        table.put_item(Item={
            "image_id": image_id,
            "s3_key": s3_key,
            "uploaded_on": datetime.utcnow().isoformat()
        })

    # Insert into RDS
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO employees (name, location, age, technology, salary, photo_s3_key)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, location, age, technology, salary, s3_key))
    conn.commit()
    conn.close()

    return redirect(url_for('home'))

@app.route('/employee')
def employee_page():
    return render_template("employee.html")

@app.route('/get_employee', methods=['POST'])
def get_employee():
    emp_id = request.form['emp_id']
    conn = get_db_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM employees WHERE id=%s", (emp_id,))
        result = cur.fetchone()
    conn.close()

    return jsonify(result if result else {"error": "Employee not found"})

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
