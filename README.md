# Finance-Tracker
Personal Finance Tracker Website Project

I built this website as a final project for the CS50 Course by Harvard, and it is my first-ever personal project. My idea was that I could use this website to aid my financial management when I start university overseas next year. The functionality that I have added so far includes:

1. Adding and Deleting expenses.
2. Managing budgets.
3. Visualizing these budgets in a Spending vs Budget bar graph for each month.
4. Notification when a budget is exceeded for that month.

## Setup Instructions

### Clone the Repository
Clone this repository to your local machine.

### Set Up a Virtual Environment
Create and activate a virtual environment in the project directory:

```bash
python3 -m venv venv
```
```bash
source venv/bin/activate
``` # For Unix or MacOS

```bash
venv\Scripts\activate  # For Windows
```
### Install Dependencies
Install the required dependencies:
```bash
pip install -r requirements.txt
```
### Create a .env File
Generate a hashed password using python password.py, then create a .env file in the same directory as app.py and add: 
HASHED_PASSWORD=your_hashed_password_here

### Initialize the Database
Create the finance_tracker.db database and set up tables:
```bash
sqlite3 finance_tracker.db < schema.sql
```

### Run the Application
Start the Flask application with:
```bash
flask run
```
   
