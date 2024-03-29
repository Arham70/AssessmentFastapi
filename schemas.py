
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    type_of_book: str


class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int

    class Config:
        orm_mode = True

class MemberBase(BaseModel):
    name: str
    email: str
    membership_id: str

class MemberCreate(MemberBase):
    pass

class Member(MemberBase):
    id: int

    class Config:
        orm_mode = True

class BorrowRecordBase(BaseModel):
    borrow_date: Optional[datetime]
    return_date: Optional[datetime]

class BorrowRecordCreate(BorrowRecordBase):
    book_id: int
    member_id: int

class BorrowRecord(BorrowRecordBase):
    id: int
    book: Book
    member: Member

    class Config:
        orm_mode = True


class ReviewBase(BaseModel):
    rating: float
    comment: Optional[str]


class ReviewCreate(BaseModel):
    rating: float
    comment: Optional[str]
    book_id: int
    member_id: int


class Review(ReviewBase):
    id: int
    book: Book
    member: Member

    class Config:
        orm_mode = True


class Recommendation(BaseModel):
    book_id: int


class UserSchema(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True


class LogRecordSchema(BaseModel):
    user: str
    method: str
    url: str
    response_status: int
    timestamp: datetime

    class Config:
        orm_mode = True