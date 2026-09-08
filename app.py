from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from data_models import db, Author, Book

db.init_app(app)


@app.route('/')
def home():
    sort_by = request.args.get('sort_by', 'title')
    search_query = request.args.get('search', '')

    if search_query:
        books = db.session.query(Book).filter(
            (Book.title.ilike(f'%{search_query}%')) |
            (Book.author.has(Author.name.ilike(f'%{search_query}%')))
        ).all()
    else:
        if sort_by == 'author':
            books = db.session.query(Book).join(Author).order_by(Author.name).all()
        else:
            books = Book.query.order_by(Book.title).all()

    return render_template('home.html', books=books, search_query=search_query)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        name = request.form.get('name')
        birth_date_str = request.form.get('birth_date')
        death_date_str = request.form.get('date_of_death')

        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date() if birth_date_str else None
        death_date = datetime.strptime(death_date_str, '%Y-%m-%d').date() if death_date_str else None

        new_author = Author(name=name, birth_date=birth_date, date_of_death=death_date)
        db.session.add(new_author)
        db.session.commit()

        return render_template('add_author.html', success=True)

    return render_template('add_author.html', success=False)


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    authors = Author.query.all()

    if request.method == 'POST':
        isbn = request.form.get('isbn')
        title = request.form.get('title')
        publication_year = request.form.get('publication_year')
        author_id = request.form.get('author_id')

        new_book = Book(isbn=isbn, title=title, publication_year=int(publication_year), author_id=int(author_id))
        db.session.add(new_book)
        db.session.commit()

        return render_template('add_book.html', authors=authors, success=True)

    return render_template('add_book.html', authors=authors, success=False)


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get(book_id)

    if book:
        author = book.author
        db.session.delete(book)
        db.session.commit()

        if author and len(author.books) == 0:
            db.session.delete(author)
            db.session.commit()

    return redirect('/')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)