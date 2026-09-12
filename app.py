from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from data_models import db, Author, Book

db.init_app(app)


@app.route('/')
def home():
    sort_by = request.args.get('sort_by', 'title')
    search_query = request.args.get('search', '')

    try:
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

        return render_template('home.html', books=books, search_query=search_query, sort_by=sort_by)

    except Exception as e:
        flash(f'Error retrieving books: {str(e)}', 'error')
        return render_template('home.html', books=[], search_query=search_query)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            birth_date_str = request.form.get('birth_date', '').strip()
            death_date_str = request.form.get('date_of_death', '').strip()

            if not name:
                flash('Author name is required!', 'warning')
                return render_template('add_author.html')

            birth_date = None
            death_date = None

            if birth_date_str:
                try:
                    birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid birth date format!', 'warning')
                    return render_template('add_author.html')

            if death_date_str:
                try:
                    death_date = datetime.strptime(death_date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid death date format!', 'warning')
                    return render_template('add_author.html')

            new_author = Author(name=name, birth_date=birth_date, date_of_death=death_date)
            db.session.add(new_author)
            db.session.commit()

            flash(f'Author "{name}" added successfully!', 'success')
            return redirect(url_for('home'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding author: {str(e)}', 'error')
            return render_template('add_author.html')

    return render_template('add_author.html')


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    authors = Author.query.all()

    if request.method == 'POST':
        try:
            isbn = request.form.get('isbn', '').strip()
            title = request.form.get('title', '').strip()
            publication_year = request.form.get('publication_year', '').strip()
            author_id = request.form.get('author_id', '').strip()

            if not isbn:
                flash('ISBN is required!', 'warning')
                return render_template('add_book.html', authors=authors)

            if not title:
                flash('Book title is required!', 'warning')
                return render_template('add_book.html', authors=authors)

            if not publication_year:
                flash('Publication year is required!', 'warning')
                return render_template('add_book.html', authors=authors)

            if not author_id:
                flash('Author selection is required!', 'warning')
                return render_template('add_book.html', authors=authors)

            try:
                pub_year = int(publication_year)
                if pub_year < 0 or pub_year > datetime.now().year:
                    flash(f'Publication year must be between 0 and {datetime.now().year}!', 'warning')
                    return render_template('add_book.html', authors=authors)
            except ValueError:
                flash('Publication year must be a number!', 'warning')
                return render_template('add_book.html', authors=authors)

            new_book = Book(isbn=isbn, title=title, publication_year=pub_year, author_id=int(author_id))
            db.session.add(new_book)
            db.session.commit()

            flash(f'Book "{title}" added successfully!', 'success')
            return redirect(url_for('home'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding book: {str(e)}', 'error')
            return render_template('add_book.html', authors=authors)

    return render_template('add_book.html', authors=authors)


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    try:
        book = Book.query.get(book_id)

        if not book:
            flash('Book not found!', 'error')
            return redirect(url_for('home'))

        book_title = book.title
        author = book.author

        db.session.delete(book)
        db.session.commit()

        if author and len(author.books) == 0:
            db.session.delete(author)
            db.session.commit()

        flash(f'Book "{book_title}" deleted successfully!', 'success')
        return redirect(url_for('home'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting book: {str(e)}', 'error')
        return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)