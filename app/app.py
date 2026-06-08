from flask import Flask, render_template
from models import Database

app = Flask(__name__)
database = Database()

@app.route('/')
def home():
    books = database.fetch_books()
    return render_template('index.html', books=books)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
