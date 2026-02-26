import sqlite3


def init_db():
    conn = sqlite3.connect("jarvis.db")
    cursor = conn.cursor()

    # Create sys_command table
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS sys_command (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        path TEXT)"""
    )

    # Create web_command table
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS web_command (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        url TEXT)"""
    )

    # Create contacts table
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS contacts (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        mobile_no TEXT)"""
    )

    # Add some default web commands
    web_commands = [
        ("google", "https://www.google.com"),
        ("youtube", "https://www.youtube.com"),
        ("facebook", "https://www.facebook.com"),
        ("instagram", "https://www.instagram.com"),
    ]
    cursor.executemany(
        "INSERT INTO web_command (name, url) VALUES (?, ?)", web_commands
    )

    # Add some default system commands (Windows paths)
    sys_commands = [
        ("notepad", "notepad.exe"),
        ("calculator", "calc.exe"),
        ("edge", "msedge.exe"),
    ]
    cursor.executemany(
        "INSERT INTO sys_command (name, path) VALUES (?, ?)", sys_commands
    )

    # Add a dummy contact
    contacts = [
        ("Self", "1234567890"),
    ]
    cursor.executemany("INSERT INTO contacts (name, mobile_no) VALUES (?, ?)", contacts)

    conn.commit()
    conn.close()
    print("Database initialized successfully with default data.")


if __name__ == "__main__":
    init_db()
