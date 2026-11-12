
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date

from catalog import get_all_books, add_book, get_all_borrowers, add_borrower
from transactions import issue_book, get_all_loans, return_book, get_overdue_loans
from analytics import get_report_data

app = Flask(__name__)
app.secret_key = "library-project-secret-key"


@app.route("/")
def index():
    books = get_all_books()
    borrowers = get_all_borrowers()
    loans = get_all_loans()
    overdue = get_overdue_loans()

    active_count = sum(
        1 for loan in loans
        if loan["status"] in ("Active", "Overdue")
    )

    return render_template(
        "index.html",
        total_titles=len(books),
        total_copies=sum(book["copies_available"] for book in books),
        borrower_count=len(borrowers),
        active_count=active_count,
        overdue_count=len(overdue),
        recent_loans=loans[:5]
    )


@app.route("/books", methods=["GET", "POST"])
def books_page():
    if request.method == "POST":
        try:
            isbn = request.form.get("isbn", "").strip()
            title = request.form.get("title", "").strip()
            author = request.form.get("author", "").strip()
            category = request.form.get("category", "").strip()
            copies = int(request.form.get("copies", "0"))

            if not title or not author or not category:
                raise ValueError("Please fill in the title, author, and category.")

            if copies < 0:
                raise ValueError("Copies cannot be negative.")

            add_book(isbn, title, author, category, copies)
            flash("Book added successfully!", "success")

        except ValueError as error:
            flash(str(error), "error")
        except Exception as error:
            flash(f"Could not add the book: {error}", "error")

        return redirect(url_for("books_page"))

    search = request.args.get("search", "").strip()
    book_list = get_all_books(search)

    return render_template("books.html", books=book_list, search=search)


@app.route("/borrowers", methods=["GET", "POST"])
def borrowers_page():
    if request.method == "POST":
        try:
            name = request.form.get("borrower_name", "").strip()
            roll_no = request.form.get("roll_no", "").strip()

            if not name or not roll_no:
                raise ValueError("Please enter both the borrower's name and roll number.")

            add_borrower(name, roll_no)
            flash("Borrower added successfully!", "success")

        except Exception as error:
            flash(f"Could not add borrower: {error}", "error")

        return redirect(url_for("borrowers_page"))

    borrower_list = get_all_borrowers()
    return render_template("borrowers.html", borrowers=borrower_list)


@app.route("/loans", methods=["GET", "POST"])
def loans_page():
    if request.method == "POST":
        try:
            book_id = int(request.form.get("book_id", "0"))
            borrower_id = int(request.form.get("borrower_id", "0"))

            due_date_text = request.form.get("due_date", "").strip()

            if due_date_text:
                due_date = date.fromisoformat(due_date_text)
            else:
                due_date = None

            issue_book(book_id, borrower_id, due_date)
            flash("Book issued successfully!", "success")

        except Exception as error:
            flash(f"Could not issue book: {error}", "error")

        return redirect(url_for("loans_page"))

    book_list = get_all_books()
    borrower_list = get_all_borrowers()
    loan_list = get_all_loans()

    return render_template(
        "loans.html",
        books=book_list,
        borrowers=borrower_list,
        loans=loan_list
    )


@app.route("/return/<int:loan_id>", methods=["POST"])
def return_loan(loan_id):
    try:
        return_book(loan_id)
        flash("Book returned successfully!", "success")
    except Exception as error:
        flash(f"Could not return book: {error}", "error")

    return redirect(url_for("loans_page"))


@app.route("/reports")
def reports_page():
    report = get_report_data()
    overdue = get_overdue_loans()

    return render_template(
        "reports.html",
        report=report,
        overdue=overdue
    )


if __name__ == "__main__":
    app.run(debug=True)
