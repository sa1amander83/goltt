import psycopg2

try:
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='123',
        host='127.0.0.1',
        port=5434
    )
    print("Подключение успешно!")
except Exception as e:
    print(f"Ошибка: {e}")
