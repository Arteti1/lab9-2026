"""
Юніт-тести для Лабораторної роботи № 9 (Варіант 11: Flask веб-додаток «Словник термінів»).
"""
import os
import tempfile
import unittest

from src.glossary_app.app import create_app


class TestGlossaryWebApp(unittest.TestCase):
    """Перевірка маршрутизації, пошуку та CRUD-операцій веб-додатку «Словник термінів»."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_glossary.db")
        self.app = create_app(db_path=self.db_path)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_index_loads_initial_terms(self):
        """Перевірка відображення головної сторінки та початкових термінів."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Словник термінів", html)
        self.assertIn("Інкапсуляція", html)

    def test_add_search_edit_and_delete_term(self):
        """Перевірка повного життєвого циклу терміна: додавання, пошук, редагування, видалення."""
        # 1. Додавання нового терміна
        add_resp = self.client.post(
            "/add",
            data={
                "term": "Поліморфізм",
                "category": "ООП",
                "definition": "Здатність об'єктів різних класів оброблятися через єдиний інтерфейс.",
                "example": "Метод speak() у класах Dog та Cat.",
            },
            follow_redirects=True,
        )
        self.assertEqual(add_resp.status_code, 200)
        self.assertIn("Поліморфізм", add_resp.data.decode("utf-8"))

        # 2. Пошук за назвою терміна (нечутливий до регістру кирилиці)
        search_resp = self.client.get("/?q=поліморф")
        search_html = search_resp.data.decode("utf-8")
        self.assertIn("Поліморфізм", search_html)
        self.assertNotIn("Зовнішній ключ", search_html)

        # Знаходимо ID створеного терміна (після 6 стартових це id = 7)
        edit_resp = self.client.post(
            "/edit/7",
            data={
                "term": "Поліморфізм (ООП)",
                "category": "ООП",
                "definition": "Оновлене визначення поліморфізму.",
                "example": "len([1, 2]) та len('abc')",
            },
            follow_redirects=True,
        )
        self.assertEqual(edit_resp.status_code, 200)
        self.assertIn("Поліморфізм (ООП)", edit_resp.data.decode("utf-8"))

        # 4. Видалення терміна
        del_resp = self.client.post("/delete/7", follow_redirects=True)
        self.assertEqual(del_resp.status_code, 200)
        self.assertNotIn("Поліморфізм (ООП)", del_resp.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
