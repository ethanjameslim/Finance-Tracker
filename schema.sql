CREATE TABLE expenses (
    id INTEGER PRIMARY KEY,
    date TEXT,
    category TEXT,
    amount REAL,
    description TEXT
);
CREATE TABLE budgets (
    category TEXT PRIMARY KEY,
    amount REAL
);
CREATE TABLE subscriptions (
    sub_id INTEGER PRIMARY KEY,
    name TEXT,
    interval TEXT,
    next_due DATETIME,
    notes TEXT
);