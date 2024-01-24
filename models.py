from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from database import Base
from sqlalchemy.orm import Session

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    isbn = Column(String, unique=True)
    type_of_book = Column(String)  # New field

class Member(Base):
    __tablename__ = 'members'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, index=True)
    membership_id = Column(String, unique=True)


class BorrowRecord(Base):
    __tablename__ = 'borrow_records'
    id = Column(Integer, primary_key=True, index=True)
    borrow_date = Column(DateTime, default=datetime.utcnow)
    return_date = Column(DateTime, nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'))
    member_id = Column(Integer, ForeignKey('members.id'))

    book = relationship('Book', back_populates='borrow_records')
    member = relationship('Member', back_populates='borrow_records')

    def set_return_date(self):
        if self.borrow_date and not self.return_date:
            self.return_date = self.borrow_date + timedelta(days=2)


Book.borrow_records = relationship('BorrowRecord', order_by=BorrowRecord.id, back_populates='book')
Member.borrow_records = relationship('BorrowRecord', order_by=BorrowRecord.id, back_populates='member')

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Float)
    comment = Column(String)
    book_id = Column(Integer, ForeignKey('books.id'))
    member_id = Column(Integer, ForeignKey('members.id'))

    book = relationship('Book', back_populates='reviews')
    member = relationship('Member', back_populates='reviews')


Book.reviews = relationship('Review', order_by=Review.id, back_populates='book')
Member.reviews = relationship('Review', order_by=Review.id, back_populates='member')

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)


class LogRecord(Base):
    __tablename__ = "log_records"

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, index=True)
    method = Column(String)
    url = Column(String)
    status_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration = Column(Float)