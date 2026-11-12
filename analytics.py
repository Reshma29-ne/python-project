
import os
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from db import get_connection

CHART_FOLDER = os.path.join("static", "charts")
os.makedirs(CHART_FOLDER, exist_ok=True)


def get_report_data():
    conn = get_connection()

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT book_id, title, category, copies_available
            FROM books
        """)
        books = cursor.fetchall()

        cursor.execute("""
            SELECT book_id, issue_date, return_date
            FROM loans
        """)
        loans = cursor.fetchall()

        cursor.close()

    finally:
        conn.close()

    books_df = pd.DataFrame(books)
    loans_df = pd.DataFrame(loans)

    if loans_df.empty:
        popular = pd.DataFrame(
            columns=["title", "total_borrowed"]
        )
        monthly = pd.DataFrame(
            columns=["month", "total_borrowed"]
        )
        average_loans = 0
        maximum_loans = 0

    else:
        popular = (
            loans_df.groupby("book_id")
            .size()
            .reset_index(name="total_borrowed")
            .merge(
                books_df[["book_id", "title"]],
                on="book_id",
                how="left"
            )
            [["title", "total_borrowed"]]
            .sort_values(
                "total_borrowed",
                ascending=False
            )
        )

        loans_df["month"] = pd.to_datetime(
            loans_df["issue_date"]
        ).dt.to_period("M").astype(str)

        monthly = (
            loans_df.groupby("month")
            .size()
            .reset_index(name="total_borrowed")
            .sort_values("month")
        )

        counts = loans_df.groupby("book_id").size().to_numpy()

        average_loans = float(np.mean(counts))
        maximum_loans = int(np.max(counts))

    if books_df.empty:
        category = pd.DataFrame(
            columns=[
                "category",
                "number_of_books",
                "available_copies"
            ]
        )
    else:
        category = (
            books_df.groupby("category")
            .agg(
                number_of_books=("book_id", "count"),
                available_copies=("copies_available", "sum")
            )
            .reset_index()
        )

    # Monthly borrowing chart
    plt.figure(figsize=(8, 4))

    if monthly.empty:
        plt.text(
            0.5, 0.5,
            "No borrowing records yet",
            ha="center",
            va="center"
        )
        plt.xticks([])
        plt.yticks([])
    else:
        plt.plot(
            monthly["month"],
            monthly["total_borrowed"],
            marker="o"
        )
        plt.xticks(rotation=45, ha="right")

    plt.title("Monthly Library Borrowing")
    plt.xlabel("Month")
    plt.ylabel("Books Issued")
    plt.tight_layout()
    plt.savefig(
        os.path.join(CHART_FOLDER, "monthly_trends.png")
    )
    plt.close()

    # Most borrowed books chart
    top_books = popular.head(5).sort_values("total_borrowed")

    plt.figure(figsize=(8, 4))

    if top_books.empty:
        plt.text(
            0.5, 0.5,
            "No borrowing records yet",
            ha="center",
            va="center"
        )
        plt.xticks([])
        plt.yticks([])
    else:
        plt.barh(
            top_books["title"],
            top_books["total_borrowed"]
        )

    plt.title("Most Borrowed Books")
    plt.xlabel("Number of Issues")
    plt.tight_layout()
    plt.savefig(
        os.path.join(CHART_FOLDER, "popular_books.png")
    )
    plt.close()
    
    # Category distribution pie chart
    plt.figure(figsize=(7, 5))

    if category.empty or category["number_of_books"].sum() == 0:
        plt.text(
            0.5, 0.5,
            "No category data available",
            ha="center",
            va="center"
        )
        plt.axis("off")
    else:
        plt.pie(
            category["number_of_books"],
            labels=category["category"],
            autopct="%1.1f%%",
            startangle=90
        )

    plt.title("Library Books by Category")
    plt.tight_layout()
    plt.savefig(
        os.path.join(CHART_FOLDER, "category_distribution.png")
    )
    plt.close()


    return {
        "popular": popular.to_dict("records"),
        "monthly": monthly.to_dict("records"),
        "category": category.to_dict("records"),
        "average_loans": round(average_loans, 2),
        "maximum_loans": maximum_loans
    }
