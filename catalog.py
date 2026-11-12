
from db import get_connection


def get_all_books(search=""):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if search:
        word = "%" + search + "%"
        cursor.execute("""
            SELECT * FROM books
            WHERE title LIKE %s OR author LIKE %s
            OR category LIKE %s OR isbn LIKE %s
            ORDER BY title
        """, (word, word, word, word))
    else:
        cursor.execute("SELECT * FROM books ORDER BY title")

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def add_book(isbn, title, author, category, copies):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO books
        (isbn, title, author, category, copies_available)
        VALUES (%s, %s, %s, %s, %s)
    """, (isbn or None, title, author, category, copies))

    conn.commit()
    cursor.close()
    conn.close()


def get_all_borrowers():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM borrowers ORDER BY borrower_name")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows


def add_borrower(name, roll_no):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO borrowers (borrower_name, roll_no)
        VALUES (%s, %s)
    """, (name, roll_no))

    conn.commit()
    cursor.close()
    conn.close()
