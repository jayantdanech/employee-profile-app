CREATE TABLE employees (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128),
  location VARCHAR(100),
  age INT,
  technology VARCHAR(100),
  salary DECIMAL(10,2),
  photo_s3_key VARCHAR(500)
);
