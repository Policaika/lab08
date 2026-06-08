# Лабораторная работа №8

## Структура проекта

```zsh
┌──(p㉿Policai)-[~/…/Policaika/workspace/reports/lab08]
└─$ tree -L 3
.
├── app
│   ├── app.py
│   ├── models.py
│   ├── requirements.txt
│   └── templates
│       └── index.html
├── db
│   └── init.sql
├── docker-compose.yml
└── Dockerfile
```

Начнем с описания каждого файла, что и для чего.

## app.py

app.py - главный файл приложения, по сути точка входа в flask-приложения.
Он отвечает за поднятие сервера и за маршрутизацию.

```python
# Импортируем Flask для создания веб-приложения
# render_template нужен для рендеринга HTML-шаблонов
from flask import Flask, render_template

# Импортируем класс Database из файла models.py
# Он отвечает за подключение к MySQL и выполнение запросов
from models import Database

# Создаём экземпляр Flask-приложения
# __name__ нужен Flask, чтобы понимать, где находится приложение
app = Flask(__name__)

# Создаём объект для работы с базой данных
database = Database()

# Декоратор @app.route('/') задаёт маршрут: какой URL обрабатывает функция
# В данном случае '/' — это главная страница сайта
@app.route('/')
def home():
    # Запрашиваем у модели список всех книг из БД
    books = database.fetch_books()
    
    # Рендерим шаблон index.html и передаём в него список книг
    # В шаблоне к ним можно обращаться через переменную {{ books }}
    return render_template('index.html', books=books)

# Эта часть выполняется только если файл запущен напрямую (не импортирован)
if __name__ == "__main__":
    # host="0.0.0.0" — слушать на всех сетевых интерфейсах
    # Это важно для Docker: иначе приложение будет недоступно снаружи контейнера
    # port=8080 — порт, на котором работает Flask
    # Должен совпадать с портом в docker-compose.yml и EXPOSE в Dockerfile
    app.run(host="0.0.0.0", port=8080)
```

## models.py

Класс для работы с базой данных. Настройки подключения (хост, логин, пароль, имя БД) берутся из переменных окружения с резервными значениями на случай, если переменные не заданы. 

```python
import os
import mysql.connector

class Database:
    def __init__(self):
        self.params = {
            'host': os.getenv('DB_HOST', 'database'),
            'port': 3306,
            'user': os.getenv('DB_USER', 'admin'),
            'password': os.getenv('DB_PASSWORD', 'secret'),
            'database': os.getenv('DB_NAME', 'library'),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_general_ci'
        }

    def fetch_books(self):
        try:
            connection = mysql.connector.connect(**self.params)
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT title, author FROM books ORDER BY id')
            result = cursor.fetchall()
            cursor.close()
            connection.close()
            return result
        except mysql.connector.Error as err:
            print(f"DB error: {err}")
            return []
```

## requirements.txt

Список Python-зависимостей, которые устанавливаются при сборке Docker-образа. Flask — микрофреймворк для веб-приложений, mysql-connector-python — официальный драйвер для подключения к MySQL.

```
Flask==3.0.0
mysql-connector-python==8.2.0
```

## index.html

HTML-шаблон Jinja2. Получает список книг из контроллера и с помощью цикла {% for book in books %} отображает каждую книгу в виде элемента списка: название жирным шрифтом и автор.

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Библиотечный каталог</title>
</head>
<body>
    <h1>Книги в базе</h1>
    <ul>
    {% for book in books %}
        <li><b>{{ book.title }}</b> — {{ book.author }}</li>
    {% endfor %}
    </ul>
</body>
</html>
```

## docker-compose.yml

Файл описывает стек из двух сервисов: веб-приложение на Flask и базу данных MySQL.

```yaml
services:                     # Главный раздел, в котором перечисляются контейнеры
  web:                        # Имя сервиса веб-приложения
    build: .                  # Указывает на то, что образ нужно собрать из Dockerfile в текущей директории
    container_name: flask_app # Задаёт имя контейнера
    ports:
      - "8080:8080"           # внешний:внутренний порт для сервиса web
    depends_on:               # управляет порядком запуска и условиями готовности
      database:               # имя сервиса, от которого зависит web
        condition: service_healthy # ждать не просто старта контейнера database, а пока его healthcheck не сообщит статус healthy
    env_file:                 # загружает переменные окружения из файла .env
      - .env
    restart: unless-stopped   # автоперезапуск при падении, кроме случаев ручной остановки

  database:                   # имя сервиса базы данных
    image: mysql:8.4          # использовать готовый образ MySQL версии 8.4 с Docker Hub
    container_name: mysql_server # Имя контейнера
    restart: always           # если контейнер упадет, то произойдет рестарт
    env_file:                 # переменные окружения из .env
      - .env
    ports:
      - "3307:3306"           # Проброс порта: 3307 хоста -> 3306 контейнера
    volumes:                  # подключение томов
      - mysql_storage:/var/lib/mysql  # именованный том для хранения данных БД
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro  # инициализация БД (read-only)
    healthcheck:              # проверка работоспособности контейнера
      test: ["CMD", "mysqladmin", "ping", "-h", "127.0.0.1"]  # команда проверки
      interval: 15s           # запускать каждые 15 секунд
      timeout: 10s            # время ожидания ответа
      retries: 3              # количество повторов перед пометкой как unhealthy

volumes:                      # объявление именованного тома
  mysql_storage:
```

## Dockerfile

В нем хранится инструкция по сборке Docker-образа.

```Dockerfile
FROM python:3.10-alpine       # Указывает базовый образ — облегчённый Linux Alpine с Python 3.10

WORKDIR /service              # Задаёт рабочую папку внутри контейнера

RUN apk add --no-cache gcc musl-dev  # Установка компилятора и заголовочных файлов (нужны для сборки некоторых Python-пакетов)

COPY app/requirements.txt .   # Копирует файл зависимостей внутрь образа

RUN pip install --no-cache-dir -r requirements.txt  # Устанавливает Python-зависимости.
# Флаг --no-cache-dir отключает кэширование pip, чтобы уменьшить размер образа

COPY app/ .                   # Копирует все содержимое папки app в рабочую директорию

EXPOSE 8080                   # Документирует, что контейнер слушает порт 8080

ENTRYPOINT ["python", "app.py"]  # Задаёт команду, которая будет выполнена при запуске контейнера
```

## init.sql

Данный файл создаёт таблицу books с полями id, title, author, принудительно задав кодировку utf8mb4 для хранения данных. Затем заполняет таблицу двумя тестовыми записями.

```sql
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(150) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO books (title, author) VALUES
    ('Война и мир', 'Лев Толстой'),
    ('Преступление и наказание', 'Фёдор Достоевский');
```

## .env

Файл с переменными окружения. Вынесен отдельно, чтобы не хранить пароли в коде и не коммитить их в git (файл добавлен в .gitignore).

```
#Для MySQL
MYSQL_ROOT_PASSWORD=rootpass123
MYSQL_DATABASE=library
MYSQL_USER=admin
MYSQL_PASSWORD=secret

# Для приложения(используются models.py)
DB_HOST=database
DB_USER=admin
DB_PASSWORD=secret
DB_NAME=library
```

## .gitignore

Тут добавляем .env, чтобы парали от БД не попали в репо

```
.env
```

# Часть I. Docker

Теперь опишем процесс выполнения лабораторной работы. Изначально docker отсутствовал в системе, выполнялась на Kali Linux.

```zsh
sudo apt update
sudo apt install -y docker.io docker-compose
```

Для запуска Docker без прав суперпользователя текущий пользователь был добавлен в группу docker и выполнена перезагрузка сеанса:

```zsh
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

При первой попытке скачать образы с Docker Hub возникла ошибка TLS handshake timeout — реестр был недоступен. Проблема была решена настройкой зеркал Docker Hub. Создан файл /etc/docker/daemon.json:

```json
{
  "registry-mirrors": [
    "https://mirror.gcr.io",
    "https://dockerhub.timeweb.cloud",
    "https://huecker.io",
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
```

После чего docker успешно установился

## 1. Добавьте в код Dockerfile, который позволит запустить web-приложение с исходным кодом в каталоге app/ через docker.

См. содержимое выше

## 2. Выполните запуск контейнера с этим приложением.

```zsh
┌──(p㉿Policai)-[~/…/Policaika/workspace/reports/lab08]
└─$ docker compose up -d --build
[+] Building 0.9s (13/13) FINISHED                                                                                                                                               
 => [internal] load local bake definitions                                                                                                                                  0.0s
 => => reading from stdin 567B                                                                                                                                              0.0s
 => [internal] load build definition from Dockerfile                                                                                                                        0.0s
 => => transferring dockerfile: 350B                                                                                                                                        0.0s
 => [internal] load metadata for docker.io/library/python:3.10-alpine                                                                                                       0.7s
 => [internal] load .dockerignore                                                                                                                                           0.0s
 => => transferring context: 2B                                                                                                                                             0.0s
 => [1/6] FROM docker.io/library/python:3.10-alpine@sha256:b974a5de91b4ac6da8313502cd5bfe65c499e390d32658e1f2deea26fa5afb14                                                 0.0s
 => [internal] load build context                                                                                                                                           0.0s
 => => transferring context: 514B                                                                                                                                           0.0s
 => CACHED [2/6] WORKDIR /service                                                                                                                                           0.0s
 => CACHED [3/6] RUN apk add --no-cache gcc musl-dev                                                                                                                        0.0s
 => CACHED [4/6] COPY app/requirements.txt .                                                                                                                                0.0s
 => CACHED [5/6] RUN pip install --no-cache-dir     --index-url https://pypi.tuna.tsinghua.edu.cn/simple     --default-timeout=100     -r requirements.txt                  0.0s
 => [6/6] COPY app/ .                                                                                                                                                       0.0s
 => exporting to image                                                                                                                                                      0.0s
 => => exporting layers                                                                                                                                                     0.0s
 => => writing image sha256:c42c17f1a24ddf09a0d1ec337f290bf393998a60195f6ab704694d17f4f6023c                                                                                0.0s
 => => naming to docker.io/library/lab08-web                                                                                                                                0.0s
 => resolving provenance for metadata file                                                                                                                                  0.0s
[+] Running 4/4
 ✔ lab08-web               Built                                                                                                                                            0.0s 
 ✔ Network lab08_default   Created                                                                                                                                          0.0s 
 ✔ Container mysql_server  Healthy                                                                                                                                         15.7s 
 ✔ Container flask_app     Started  
```

Проверим, что все контейнеры запустились:

```zsh
┌──(p㉿Policai)-[~/…/Policaika/workspace/reports/lab08]
└─$ docker compose ps
NAME           IMAGE       COMMAND                  SERVICE    CREATED          STATUS                    PORTS
flask_app      lab08-web   "python app.py"          web        18 seconds ago   Up 2 seconds              0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp
mysql_server   mysql:8.4   "docker-entrypoint.s…"   database   18 seconds ago   Up 18 seconds (healthy)   33060/tcp, 0.0.0.0:3307->3306/tcp, [::]:3307->3306/tcp
```

3. Скопируйте из консоли в каталог /home/ контейнера файл README.md.

```zsh
┌──(p㉿Policai)-[~/…/Policaika/workspace/reports/lab08]
└─$ docker cp README.md flask_app:/home/
Successfully copied 18.9kB to flask_app:/home/
```

## 4. Подключитесь к терминалу контейнера с приложением в интерактивном режиме. Проверьте, что скопированный файл находится в нужном каталоге.

```zsh
┌──(p㉿Policai)-[~/…/Policaika/workspace/reports/lab08]
└─$ docker exec -it flask_app /bin/sh
/service # ls /home
README.md
/service # exit
```

exec – выполняет команду внутри уже запущенного контейнера.
it – интерактивный режим, позволяющий взаимодействовать с оболочкой.

## 6. Остановите контейнер с приложением.

```zsh
┌──(p㉿Policai)-[~/…/Policaika/workspace/reports/lab08]
└─$ docker stop flask_app
flask_app
```

````
┌──(p㉿Policai)-[~/…/Policaika/workspace/reports/lab08]
└─$ docker ps -a
CONTAINER ID   IMAGE       COMMAND                  CREATED          STATUS                            PORTS                                                    NAMES
6d76f356263b   lab08-web   "python app.py"          37 minutes ago   Exited (137) About a minute ago                                                            flask_app
d1e8f0918712   mysql:8.4   "docker-entrypoint.s…"   37 minutes ago   Up 37 minutes (healthy)           33060/tcp, 0.0.0.0:3307->3306/tcp, [::]:3307->3306/tcp   mysql_server
````

# Часть II. Docker compose

## 1. Создайте файл docker-compose.yml таким образом, чтобы совместно с описанным в части 1 контейнером работала бы база данных mysql. Файл инициализации БД в каталоге db/init.sql. Также пропишите порт подключения к приложению. Например 8080.

Сам файл был показан выше.


## 2. Запустите связку web-приложение - БД.

С помощью docker compose down -v мы отсанавливаем и удаляем связанные тома, а 
с помощью docker compose up -d --build собираем и запускаем в фоновом режиме.

```zsh
┌──(p㉿Policai)-[~/…/Policaika/workspace/reports/lab08]
└─$ docker compose down -v 
[+] Running 4/4
 ✔ Container flask_app         Removed                                                                                                                                      0.0s 
 ✔ Container mysql_server      Removed                                                                                                                                      1.0s 
 ✔ Volume lab08_mysql_storage  Removed                                                                                                                                      0.0s 
 ✔ Network lab08_default       Removed                                                                                                                                      0.4s 
``` 
 
```zsh
┌──(p㉿Policai)-[~/…/Policaika/workspace/reports/lab08]
└─$ docker compose up -d --build 
[+] Building 2.7s (13/13) FINISHED                                                                                                                                               
 => [internal] load local bake definitions                                                                                                                                  0.0s
 => => reading from stdin 567B                                                                                                                                              0.0s
 => [internal] load build definition from Dockerfile                                                                                                                        0.0s
 => => transferring dockerfile: 350B                                                                                                                                        0.0s
 => [internal] load metadata for docker.io/library/python:3.10-alpine                                                                                                       2.6s
 => [internal] load .dockerignore                                                                                                                                           0.0s
 => => transferring context: 2B                                                                                                                                             0.0s
 => [1/6] FROM docker.io/library/python:3.10-alpine@sha256:b974a5de91b4ac6da8313502cd5bfe65c499e390d32658e1f2deea26fa5afb14                                                 0.0s
 => [internal] load build context                                                                                                                                           0.0s
 => => transferring context: 204B                                                                                                                                           0.0s
 => CACHED [2/6] WORKDIR /service                                                                                                                                           0.0s
 => CACHED [3/6] RUN apk add --no-cache gcc musl-dev                                                                                                                        0.0s
 => CACHED [4/6] COPY app/requirements.txt .                                                                                                                                0.0s
 => CACHED [5/6] RUN pip install --no-cache-dir     --index-url https://pypi.tuna.tsinghua.edu.cn/simple     --default-timeout=100     -r requirements.txt                  0.0s
 => CACHED [6/6] COPY app/ .                                                                                                                                                0.0s
 => exporting to image                                                                                                                                                      0.0s
 => => exporting layers                                                                                                                                                     0.0s
 => => writing image sha256:c42c17f1a24ddf09a0d1ec337f290bf393998a60195f6ab704694d17f4f6023c                                                                                0.0s
 => => naming to docker.io/library/lab08-web                                                                                                                                0.0s
 => resolving provenance for metadata file                                                                                                                                  0.0s
[+] Running 5/5
 ✔ lab08-web                   Built                                                                                                                                        0.0s 
 ✔ Network lab08_default       Created                                                                                                                                      0.0s 
 ✔ Volume lab08_mysql_storage  Created                                                                                                                                      0.0s 
 ✔ Container mysql_server      Healthy                                                                                                                                     15.7s 
 ✔ Container flask_app         Started                                                                                                                                     15.8s 
```

## 3. Проверьте подключение к приложению через браузер. Сделайте снимок экрана.

## 4. Проверьте работу приложения через браузер.

![Локалка](https://www.stom-firms.ru/p_a2_customImageUploader_imageViewer?img=NjFfMjNlNjBkYjhkZWZmZjI0M2RkMGI3YzljOTQ5ZDU4ZTc=)

Так же можно проверить работу через curl:

```zsh
┌──(p㉿Policai)-[~/…/Policaika/workspace/reports/lab08]
└─$ curl http://localhost:8080
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Библиотечный каталог</title>
</head>
<body>
    <h1>Книги в базе</h1>
    <ul>
    
        <li><b>Война и мир</b> — Лев Толстой</li>
    
        <li><b>Преступление и наказание</b> — Фёдор Достоевский</li>
    
    </ul>
</body>
</html>                                                                                                                                                                                 
```
