# -*- coding: utf-8 -*-
"""
Лабораторна робота № 9: Інструкції та запуск веб-додатку Варіанту 11 («Словник термінів»).
Студент: Фесюк Максим Ігорович (КН-25-2)
"""
import sys


def print_instructions() -> None:
    """Виводить інструкції для запуску веб-додатку Варіанту 11 та навчальних прикладів."""
    print("=" * 80)
    print("Лабораторна робота № 9 (Варіант 11): Веб-додаток «Словник термінів» (Flask)")
    print("=" * 80)
    print("\nОсновний реалізований проєкт знаходиться у директорії: src/glossary_app/\n")
    print("Щоб запустити веб-додаток «Словник термінів», виконайте з кореня репозиторію:")
    print("   python src/glossary_app/app.py")
    print("або:")
    print("   python src/lab9.py --run\n")
    print("Після запуску відкрийте у браузері: http://127.0.0.1:5000\n")

    print("-" * 26 + " Навчальні приклади шаблону " + "-" * 26)
    print("1. Flask Example:  cd src/flask_example  && python app.py")
    print("2. Django Example: cd src/django_example && python manage.py migrate && python manage.py runserver")
    print("=" * 80)


if __name__ == "__main__":
    if "--run" in sys.argv:
        from glossary_app.app import app

        app.run(debug=True)
    else:
        print_instructions()
