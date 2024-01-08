# Finance-Tracker
Personal Finance Tracker Website Project
I built this website as a final project for the CS50 Course by harvard and is my first ever personal project>
My idea was that I could use this website to aid my finnancial management When I start university overseas next year.
The functionality that I have added so far include.

1. Adding and Deleting expenses.
2. Managing budgets.
3. Visualising these budgets in a Spending vs Budget bar graph for each month.
4. Notification when a buget is exceeded for that month.

IF YOU WANT TO RECREATE THIS PROGRAM:
1. Setup a virtual environment and install all the dependencies
2. Generate a password Hash
To Generate A Password Hash run the following command:

```bash```
python password.py

3. Create a .env file in the same route as the app.py and in that file add: HASHED_PASSWORD = (Your hashed password here)
4. Create a file called finance-tracker.db
5. Run the following command:
   sqlite3 finance_tracker.db
6. Copy paste the entire contents of the schema.sql to the terminal after (Terminal should say sqlite3 before you enter the CREATE TABLE commands)
   
   
