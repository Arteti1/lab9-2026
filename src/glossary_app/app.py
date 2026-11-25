"""
Лабораторна робота № 9. Створення простого веб-додатку на Flask.
Варіант 11: Веб-додаток «Словник термінів».
Студент: Фесюк Максим Ігорович (КН-25-2)
"""
from contextlib import contextmanager
import os
import sqlite3
from typing import Iterator, List, Optional, Tuple
from flask import Flask, abort, flash, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "glossary.db")

INITIAL_TERMS: List[Tuple[str, str, str, str]] = [
    (
        "Алгоритм",
        "Основи програмування",
        "Скінченна послідовність чітко визначених дій, виконання яких приводить до розв'язання поставленої задачі.",
        "Алгоритм бінарного пошуку знаходить елемент у відсортованому масиві за O(log n).",
    ),
    (
        "Інкапсуляція",
        "ООП",
        "Принцип об'єктно-орієнтованого програмування, що поєднує дані та методи роботи з ними в одному класі й приховує внутрішню реалізацію.",
        "Захищені атрибути об'єкта змінюються лише через публічні методи або властивості (@property).",
    ),
    (
        "Маршрутизація (Routing)",
        "Веб-розробка",
        "Механізм зіставлення URL-адреси HTTP-запиту з відповідною функцією-обробником (view) у веб-фреймворку.",
        "@app.route('/edit/<int:term_id>') обробляє перехід на сторінку редагування терміна.",
    ),
    (
        "Зовнішній ключ (Foreign Key)",
        "Бази даних",
        "Поле таблиці реляційної БД, яке посилається на первинний ключ іншої таблиці та забезпечує посилальну цілісність даних.",
        "FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE.",
    ),
    (
        "Шаблонізатор Jinja2",
        "Веб-розробка",
        "Сучасний рушій шаблонів для Python, який дозволяє генерувати динамічні HTML-сторінки з циклами, умовами та наслідуванням макетів.",
        "Вираз {{ term.title }} безпечно виводить назву терміна з автоматичним екрануванням HTML.",
    ),
    (
        "Рекурсія",
        "Основи програмування",
        "Прийом програмування, за якого функція викликає сама себе безпосередньо або опосередковано з обов'язковою базовою умовою виходу.",
        "Обчислення факторіала числа n! = n * (n - 1)! при базовому випадку 0! = 1.",
    ),
]


@contextmanager
def open_db(db_path: str) -> Iterator[sqlite3.Connection]:
    """Контекстний менеджер, який фіксує транзакцію та гарантовано закриває з'єднання SQLite."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db(db_path: str) -> None:
    """Створює таблицю terms у базі даних SQLite та заповнює початковими термінами, якщо вона порожня."""
    with open_db(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term VARCHAR(120) NOT NULL UNIQUE,
                category VARCHAR(80) NOT NULL,
                definition TEXT NOT NULL,
                example TEXT DEFAULT ''
            );
            """
        )
        cur = conn.execute("SELECT COUNT(*) FROM terms;")
        count = cur.fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO terms (term, category, definition, example) VALUES (?, ?, ?, ?);",
                INITIAL_TERMS,
            )


def create_app(db_path: Optional[str] = None) -> Flask:
    """Фабрика додатку Flask «Словник термінів»."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "knuca-lab9-variant11-secret")
    app.config["DATABASE"] = db_path or DEFAULT_DB_PATH

    init_db(app.config["DATABASE"])

    @app.route("/")
    def index():
        query = request.args.get("q", "").strip()
        selected_category = request.args.get("category", "").strip()

        sql = "SELECT id, term, category, definition, example FROM terms WHERE 1=1"
        params: list = []

        if query:
            sql += " AND (LOWER_UA(term) LIKE ? OR LOWER_UA(definition) LIKE ?)"
            like_pattern = f"%{query.lower()}%"
            params.extend([like_pattern, like_pattern])

        if selected_category:
            sql += " AND category = ?"
            params.append(selected_category)

        sql += " ORDER BY term COLLATE NOCASE ASC;"

        with open_db(app.config["DATABASE"]) as conn:
            conn.create_function(
                "LOWER_UA", 1, lambda s: s.lower() if isinstance(s, str) else s
            )
            terms = conn.execute(sql, params).fetchall()
            categories_rows = conn.execute(
                "SELECT DISTINCT category FROM terms ORDER BY category ASC;"
            ).fetchall()
            total_count = conn.execute("SELECT COUNT(*) FROM terms;").fetchone()[0]

        categories = [row["category"] for row in categories_rows]
        return render_template(
            "index.html",
            terms=terms,
            categories=categories,
            query=query,
            selected_category=selected_category,
            total_count=total_count,
        )

    @app.route("/add", methods=["POST"])
    def add_term():
        term = request.form.get("term", "").strip()
        category = request.form.get("category", "").strip() or "Загальне"
        definition = request.form.get("definition", "").strip()
        example = request.form.get("example", "").strip()

        if not term or not definition:
            flash("Будь ласка, заповніть назву терміна та його визначення.", "error")
            return redirect(url_for("index"))

        try:
            with open_db(app.config["DATABASE"]) as conn:
                conn.execute(
                    "INSERT INTO terms (term, category, definition, example) VALUES (?, ?, ?, ?);",
                    (term, category, definition, example),
                )
            flash(f"Термін «{term}» успішно додано до словника!", "success")
        except sqlite3.IntegrityError:
            flash(f"Термін «{term}» вже існує у словнику.", "error")

        return redirect(url_for("index"))

    @app.route("/edit/<int:term_id>", methods=["GET", "POST"])
    def edit_term(term_id: int):
        with open_db(app.config["DATABASE"]) as conn:
            term_row = conn.execute(
                "SELECT id, term, category, definition, example FROM terms WHERE id = ?;",
                (term_id,),
            ).fetchone()

        if term_row is None:
            abort(404)

        if request.method == "POST":
            new_term = request.form.get("term", "").strip()
            new_category = request.form.get("category", "").strip() or "Загальне"
            new_definition = request.form.get("definition", "").strip()
            new_example = request.form.get("example", "").strip()

            if not new_term or not new_definition:
                flash("Назва терміна та визначення не можуть бути порожніми.", "error")
                return render_template("edit.html", item=term_row)

            try:
                with open_db(app.config["DATABASE"]) as conn:
                    conn.execute(
                        """
                        UPDATE terms
                        SET term = ?, category = ?, definition = ?, example = ?
                        WHERE id = ?;
                        """,
                        (new_term, new_category, new_definition, new_example, term_id),
                    )
                flash(f"Термін «{new_term}» оновлено.", "success")
                return redirect(url_for("index"))
            except sqlite3.IntegrityError:
                flash(f"Термін з назвою «{new_term}» вже існує.", "error")

        return render_template("edit.html", item=term_row)

    @app.route("/delete/<int:term_id>", methods=["POST", "GET"])
    def delete_term(term_id: int):
        with open_db(app.config["DATABASE"]) as conn:
            cur = conn.execute("DELETE FROM terms WHERE id = ?;", (term_id,))
            if cur.rowcount > 0:
                flash("Термін видалено зі словника.", "success")
        return redirect(url_for("index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
