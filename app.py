import os
import sqlite3
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE_PATH=os.environ.get(
            "DATABASE_PATH", str(BASE_DIR / "database" / "expenses.db")
        ),
    )
    if test_config:
        app.config.update(test_config)

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    def init_db():
        database_path = Path(app.config["DATABASE_PATH"])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        get_db().execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL
            )
            """
        )
        get_db().commit()

    @app.teardown_appcontext
    def close_db(_error=None):
        database = g.pop("db", None)
        if database is not None:
            database.close()

    with app.app_context():
        init_db()

    @app.get("/")
    def index():
        expenses = get_db().execute(
            "SELECT id, name, amount, category, date FROM expenses "
            "ORDER BY date DESC, id DESC"
        ).fetchall()
        category_totals = get_db().execute(
            "SELECT category, SUM(amount) AS total FROM expenses "
            "GROUP BY category ORDER BY total DESC, category ASC"
        ).fetchall()
        total = sum((expense["amount"] for expense in expenses), 0)
        return render_template(
            "index.html",
            expenses=expenses,
            category_totals=category_totals,
            total=total,
        )

    @app.route("/expenses/add", methods=["GET", "POST"])
    def add_expense():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            amount_text = request.form.get("amount", "").strip()
            category = request.form.get("category", "").strip()
            date_text = request.form.get("date", "").strip()

            if not name or len(name) > 100:
                flash("Enter an expense name (up to 100 characters).", "error")
            elif not category or len(category) > 50:
                flash("Enter a category (up to 50 characters).", "error")
            else:
                try:
                    amount = Decimal(amount_text)
                    if (
                        not amount.is_finite()
                        or amount <= 0
                        or amount != amount.quantize(Decimal("0.01"))
                    ):
                        raise InvalidOperation
                    expense_date = datetime.strptime(date_text, "%Y-%m-%d").date()
                    if expense_date.isoformat() != date_text:
                        raise ValueError
                except (InvalidOperation, ValueError):
                    flash(
                        "Enter a positive amount with up to two decimal places "
                        "and a valid date.",
                        "error",
                    )
                else:
                    get_db().execute(
                        "INSERT INTO expenses (name, amount, category, date) "
                        "VALUES (?, ?, ?, ?)",
                        (name, float(amount), category, expense_date.isoformat()),
                    )
                    get_db().commit()
                    flash("Expense added.", "success")
                    return redirect(url_for("index"))

        return render_template("add_expense.html")

    @app.post("/expenses/<int:expense_id>/delete")
    def delete_expense(expense_id):
        cursor = get_db().execute(
            "DELETE FROM expenses WHERE id = ?", (expense_id,)
        )
        get_db().commit()
        if cursor.rowcount == 0:
            abort(404)
        flash("Expense deleted.", "success")
        return redirect(url_for("index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
