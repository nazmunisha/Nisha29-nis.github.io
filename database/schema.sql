Table: attendance
Columns:
attendance_id int AI PK 
student_id int 
date date 
time time 
status enum('Present','Absent','Late') 
source varchar(20) 
device_type varchar(50)

Table: daily_attendance_stats
Columns:
stat_date date PK 
total_students int 
present_count int 
absent_count int 
late_count int 
generated_at timestamp

Table: device_logs
Columns:
log_id int AI PK 
user_id int 
device_type enum('Laptop','Mobile') 
ip_address varchar(45) 
login_time timestamp

Table: face_data
Columns:
face_id int AI PK 
student_id int 
encoding longblob 
created_at timestamp

Table: students
Columns:
student_id int AI PK 
roll_no varchar(20) 
name varchar(100) 
department varchar(50) 
class varchar(50) 
email varchar(100) 
phone varchar(20) 
created_at timestamp

Table: teachers
Columns:
teacher_id int AI PK 
name varchar(100) 
email varchar(100) 
phone varchar(20) 
department varchar(50) 
created_at timestamp

Table: users
Columns:
user_id int AI PK 
username varchar(50) 
password varchar(255) 
role enum('Admin','Teacher','Student') 
created_at timestamp 
student_id int 
teacher_id int