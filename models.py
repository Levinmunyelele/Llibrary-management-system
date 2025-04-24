from flask_sqlalchemy import SQLAlchemy # type: ignore
from datetime import datetime


db = SQLAlchemy()

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    debt = db.Column(db.Float, default=0.0)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    date_issued = db.Column(db.DateTime, default=datetime.utcnow)
    date_returned = db.Column(db.DateTime, nullable=True)

    book = db.relationship('Book', backref='transactions')
    member = db.relationship('Member', backref='transactions')