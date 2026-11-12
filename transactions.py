
from datetime import date, timedelta
from db import get_connection

LOAN_DAYS = 14


def issue_book(book_id, borrower_id, due_date=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()

        cursor.execute(
            "SELECT copies_available FROM books WHERE book_id = %s FOR UPDATE",
            (book_id,)
        )
        book = cursor.fetchone()

        if not book:
            raise ValueError("Book not found.")

        if book["copies_available"] < 1:
            raise ValueError("No copies of this book are available.")

        cursor.execute(
            "SELECT borrower_id FROM borrowers WHERE borrower_id = %s",
            (borrower_id,)
        )
        if not cursor.fetchone():
            raise ValueError("Borrower not found.")

        issue_date = date.today()
        if due_date is None:
            due_date = issue_date + timedelta(days=LOAN_DAYS)

        if due_date < issue_date:
            raise ValueError("Due date cannot be before issue date.")

        cursor.execute("""
            INSERT INTO loans
            (book_id, borrower_id, issue_date, due_date)
            VALUES (%s, %s, %s, %s)
        """, (book_id, borrower_id, issue_date, due_date))

        cursor.execute("""
            UPDATE books
            SET copies_available = copies_available - 1
            WHERE book_id = %s
        """, (book_id,))

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_all_loans():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT l.loan_id, b.title, br.borrower_name, br.roll_no,
               l.issue_date, l.due_date, l.return_date,
               CASE
                   WHEN l.return_date IS NOT NULL THEN 'Returned'
                   WHEN l.due_date < CURDATE() THEN 'Overdue'
                   ELSE 'Active'
               END AS status
        FROM loans l
        JOIN books b ON l.book_id = b.book_id
        JOIN borrowers br ON l.borrower_id = br.borrower_id
        ORDER BY l.loan_id DESC
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def return_book(loan_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        conn.start_transaction()

        cursor.execute("""
            SELECT book_id, issue_date, return_date
            FROM loans WHERE loan_id = %s FOR UPDATE
        """, (loan_id,))
        loan = cursor.fetchone()

        if not loan:
            raise ValueError("Loan not found.")

        if loan["return_date"] is not None:
            raise ValueError("This book has already been returned.")

        cursor.execute("""
            UPDATE loans SET return_date = %s
            WHERE loan_id = %s
        """, (date.today(), loan_id))

        cursor.execute("""
            UPDATE books
            SET copies_available = copies_available + 1
            WHERE book_id = %s
        """, (loan["book_id"],))

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def get_overdue_loans():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.title, br.borrower_name, br.roll_no,
               l.issue_date, l.due_date,
               DATEDIFF(CURDATE(), l.due_date) AS days_overdue
        FROM loans l
        JOIN books b ON l.book_id = b.book_id
        JOIN borrowers br ON l.borrower_id = br.borrower_id
        WHERE l.return_date IS NULL
          AND l.due_date < CURDATE()
        ORDER BY l.due_date
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows
