CREATE TABLE expenses (
    id INTEGER PRIMARY KEY,
    date TEXT,
    category TEXT,
    amount REAL,
    description TEXT
);
CREATE TABLE income (
    id INTEGER PRIMARY KEY,
    date TEXT,
    source TEXT,
    amount REAL,
    description TEXT
);
CREATE TABLE budgets (
    category TEXT PRIMARY KEY,
    amount REAL
);