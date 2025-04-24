from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash # type: ignore
from models import db, Book, Member, Transaction
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    books = Book.query.all()
    members = Member.query.all()
    transactions = Transaction.query.all()
    
    # Get most popular books (for simplicity, let's take top 5 books with most transactions)
    popular_books = db.session.query(Book).join(Transaction).group_by(Book.id).order_by(db.func.count(Transaction.id).desc()).limit(5).all()
    
    return render_template('home.html', 
                           books=books, 
                           members=members, 
                           transactions=transactions, 
                           popular_books=popular_books)


# Books
@app.route('/books')
def books():
    search = request.args.get('search', '')
    books = Book.query.filter(
        (Book.title.ilike(f'%{search}%')) | (Book.author.ilike(f'%{search}%'))
    ).all()
    return render_template('books.html', books=books, search=search)


@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']
    quantity = int(request.form['quantity'])
    new_book = Book(title=title, author=author, quantity=quantity)
    db.session.add(new_book)
    db.session.commit()
    flash('Book added successfully!')
    return redirect(url_for('books'))

@app.route('/delete_book/<int:book_id>')
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)

    # If the Book model has a related 'transactions' or similar relationship
    for transaction in book.transactions:
        db.session.delete(transaction)

    db.session.delete(book)
    db.session.commit()
    flash('Book and related records deleted successfully!')
    return redirect(url_for('books'))


# Members
@app.route('/members')
def members():
    search_query = request.args.get('q')
    if search_query:
        members = Member.query.filter(
            (Member.name.ilike(f'%{search_query}%')) |
            (Member.contact.ilike(f'%{search_query}%'))
        ).all()
    else:
        members = Member.query.all()
    return render_template('members.html', members=members)

@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form['name']
    contact = request.form['contact']
    new_member = Member(name=name, contact=contact)
    db.session.add(new_member)
    db.session.commit()
    flash('Member added successfully!')
    return redirect(url_for('members'))

@app.route('/delete_member/<int:member_id>')
def delete_member(member_id):
    member = Member.query.get_or_404(member_id)

    # Delete related transactions first
    for transaction in member.transactions:
        db.session.delete(transaction)

    db.session.delete(member)
    db.session.commit()
    flash('Member and related transactions deleted successfully!')
    return redirect(url_for('members'))


@app.route('/issue', methods=['GET', 'POST'])
def issue():
    books = Book.query.filter(Book.quantity > 0).all()
    members = Member.query.filter(Member.debt <= 500).all()

    if request.method == 'POST':
        book_id = int(request.form['book_id'])
        member_id = int(request.form['member_id'])

        book = Book.query.get(book_id)
        member = Member.query.get(member_id)

        # Check if the book is already issued to this member and not yet returned
        existing_transaction = Transaction.query.filter_by(
            book_id=book_id, 
            member_id=member_id, 
            date_returned=None
        ).first()

        if existing_transaction:
            flash('This member has already borrowed this book and has not returned it.')
            return redirect(url_for('issue'))

        # Check debt limit including future rent fee
        if book and member and book.quantity > 0 and (member.debt + 100) <= 500:
            # Reduce book quantity
            book.quantity -= 1

            # NOTE: Rent fee will be added on return

            # Record the transaction
            new_transaction = Transaction(book_id=book.id, member_id=member.id)
            db.session.add(new_transaction)

            # Commit all changes
            db.session.commit()

            flash('Book issued successfully!')
            return redirect(url_for('home'))
        else:
            flash('Cannot issue: Check stock or debt (KES 500 limit).')
            return redirect(url_for('issue'))

    transactions = Transaction.query.all()
    return render_template('issue.html', books=books, members=members, transactions=transactions)


@app.route('/return', methods=['GET', 'POST'])
def return_book():
    books = Book.query.all()
    members = Member.query.all()

    if request.method == 'POST':
        book_id = int(request.form['book_id'])
        member_id = int(request.form['member_id'])

        book = Book.query.get(book_id)
        member = Member.query.get(member_id)

        # Find the active transaction (not yet returned)
        transaction = Transaction.query.filter_by(
            book_id=book_id, 
            member_id=member_id, 
            date_returned=None
        ).first()

        if transaction and book and member and (member.debt + 100) <= 500:
            # Increase book quantity
            book.quantity += 1

            # Charge rent fee now
            member.debt += 100

            # Mark transaction as returned
            transaction.date_returned = datetime.utcnow()

            db.session.commit()
            flash('Book returned successfully!')
            return redirect(url_for('home'))
        else:
            flash('Cannot return: Check debt or if the book was not issued.')
            return redirect(url_for('return_book'))

    return render_template('return.html', books=books, members=members)

# Search
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    results = Book.query.filter(
        (Book.title.ilike(f'%{query}%')) | (Book.author.ilike(f'%{query}%'))
    ).all()
    return render_template('search.html', books=results, query=query)

@app.route('/edit_member/<int:member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    member = Member.query.get_or_404(member_id)
    if request.method == 'POST':
        member.name = request.form['name']
        member.contact = request.form['contact']
        db.session.commit()
        flash('Member updated successfully!')
        return redirect(url_for('members'))
    return render_template('edit_member.html', member=member)


@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.quantity = int(request.form['quantity'])
        db.session.commit()
        flash('Book updated successfully!')
        return redirect(url_for('books'))
    return render_template('edit_book.html', book=book)


if __name__ == '__main__':
    app.run(debug=True)
