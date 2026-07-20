CREATE DATABASE IF NOT EXISTS attendance_system;
USE attendance_system;

CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(100) UNIQUE,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(255),
    class VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(100),
    photo LONGBLOB NULL
);

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('Admin','Teacher','Student') NOT NULL,
    student_id INT NULL
);

CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    status VARCHAR(50) DEFAULT 'Present',
    source VARCHAR(100) DEFAULT 'FaceRecognition',
    device_type ENUM('Laptop','Mobile','TeacherDashboard','FaceRecognition','Manual') DEFAULT 'Laptop'
);

CREATE TABLE IF NOT EXISTS face_data (
    face_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL UNIQUE,
    encoding LONGBLOB NOT NULL
);

INSERT IGNORE INTO users (username, password, role, student_id)
VALUES ('admin', 'admin123', 'Admin', NULL);
