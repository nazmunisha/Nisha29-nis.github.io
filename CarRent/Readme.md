                        CAR RENTAL SYSTEM


ABSTRACT

This report presents the development of a Car Rental System created using Python and SQLite. The system replaces manual paperwork with a basic digital solution that allows customers to book cars and administrators to manage vehicles and rental requests. The project focuses on essential features, without any advanced or innovative enhancements. The report covers the system design, architecture, development tools, testing, diagrams, and documentation used throughout the project.


TABLE OF CONTENTS
1.Introduction
2.Background
3.System Design
     1 Use Case Overview 
     2 Class Diagram Explanation
     3 System Architecture
     4.  System Development 
 1 Development Tools 
 2 Technologies Used 
 3.File Structure
 4.Testing 
 
4.Unit Testing 
5.Test Case Table
6.Confluence Tool Usage
7.References


INTRODUCTION
The Car Rental System was developed to help a rental company move from manual paperwork to a simple digital solution. The system allows customers to register, log in, view available cars, and make bookings. Administrators can add cars, delete cars, and approve or reject rental requests. The project uses Python and SQLite. The system runs entirely in the terminal and focuses only on the required features.

BACKGROUND
Many small rental companies still rely on handwritten forms and manual logs. This can lead to errors, delays, and lost records. A simple digital system can help organise bookings, store car details, and manage customers more efficiently. This project aims to create a basic version of such a system using simple programming techniques. 

SYSTEM DESIGN
1.Use Case Overview:
The system has two main actors.
(A)Customer
(B)Admin

Customer
•Register
•Login
•View available cars
•Book a car

Admin
•Login
•Add cars
•Delete cars
•Approve or reject bookings

Use Case Diagram

The system interacts with two different types of users, each performing their own set of actions.

Customer Role
A customer can create an account, log in, browse the list of cars currently available, and submit a booking request for a vehicle they want to rent.

Admin Role
The administrator is responsible for managing the system. This includes logging in, adding new cars to the database, removing cars that are no longer available, and reviewing customer booking requests to either approve or decline them.

Class Diagram
•User
•Car
•Rental

User Class
This class represents anyone who interacts with the system. It keeps information such as the user’s ID, login credentials, email address, and whether the person is an admin or a customer.

Car Class
This class stores all details related to each vehicle in the system. It includes the car’s unique ID, brand, model, manufacturing year, mileage, and the rental rate used to calculate the cost.

Rental Class
This class records every booking made by customers. It contains the rental ID, the customer who made the booking, the car being rented, the rental period, the number of days, the calculated fee, and the current approval status.

System Architecture
The Car Rental System is a application built using Python for the program logic and SQLite for data storage. The system separates responsibilities between two user types: customers who make bookings and administrators who manage the fleet and approve rental requests.  

The system supports two roles:
•Admin
•Customer

Customer Capabilities
*Create an account and log in.
*View the list of cars that are currently available.
*Submit a booking request
*Automatically receive a calculated rental cost based on the number of days.

Admin Capabilities
*Log in with admin credentials.
*Add new vehicles to the system.
*Review all stored car records.
*Remove cars when needed.
*Approve or decline customer booking requests  

Folder Structure

•main.py – controls the program flow
•database.py – handles database setup
•login.py – manages login and registration
•admin_functions.py – admin features
•customer_functions.py – customer features
•menus.py – displays menus
This structure makes the system easier to maintain and update.

A step-by-step guidance to configure

1.Ensure Python 3 is installed on your computer.
2.Open the project folder where the files are stored.
3.Start the application by running.
python main.py
4.The main menu will appear, allowing you to register, log in, or exit the program.
You will see:
1.Register
2.Login
3.Exit

Development Tools
•Python 3 – main programming language
•SQLite – lightweight database
•VS Code / PyCharm – code editor
•Terminal / Command Prompt – to run the program
•Modularity and Encapsulation

I organised the whole program into separate .py files, each handlining part of the system. This makes the code easier to understand, fix, and update.

Examples from the project:
database.py → handles database setup

•Naming Conventions
 I used clear and meaningful names for variables, functions, and files.This makes the code easy to read and understand.

Examples:
add_car()
delete_car()

•Indentation and Formatting
The entire program uses consistent indentation and clean formatting.This makes the code readable and avoids Python errors.

Example:
python
def add_car():
conn = get_connection()
cur = conn.cursor()

•Commenting and Documentation
I added simple comments in the code to explain what each section does.This helps anyone reading the code understand the purpose of each part.

Examples:
Create tables
python
Customer books a car
def book_car(user):
These comments are short and clear.


•Technologies Used
     
Python Used for program logic, menus, and functions.

SQLite Used to store:
•users
•cars
•rentals

TESTING
Unit Testing
Unit testing checks if individual functions work correctly.

Example:
Login Function
Input: correct username and password Expected Output: user data returned

REFERENCES
1.Python Official Documentation – https://docs.python.org
2.SQLite Documentation – https://sqlite.org/docs.html
3.W3Schools Python Tutorial – https://www.w3schools.com/python
4.Stack Overflow – general coding questions
5.Class notes and lecture materials

Managing Software Maintenance
 Maintaining the system involves keeping the code organised and ensuring future updates do not break existing features. The project uses a modular structure, where each file handles a specific responsibility. This makes it easier to update one part of the system without affecting the rest.

 Version Control
 Tracking changes over time helps identify what was modified and when. This makes it easier to fix issues or revert to earlier versions if needed.


Modular File Structure
The program is split into separate .py files:
•database.py – database setup
•login.py – login and registration
•admin_functions.py – admin features
•customer_functions.py – customer features
•menus.py – menu screens
•main.py – runs the program.
This makes it easier to fix one part without affecting the others.

Backward Compatibility
When new features are added, the existing database structure is kept intact so that older data continues to work without requiring major changes.






    

                




  


 
                 

 
                           
 


                          







