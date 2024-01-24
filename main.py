from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Response, Request
from sqlalchemy import column, func
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import schemas
from typing import List, Annotated
import auth
from models import Member, Review, Book, BorrowRecord
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from middleware import log_requests
# from middleware import router as log_requests_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Middleware for logging all requests
app.add_middleware(BaseHTTPMiddleware, dispatch=log_requests)

app.include_router(auth.router)
# app.include_router(log_requests_router)


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[Session, Depends(auth.get_current_user)]

# user


@app.get("/users", status_code=status.HTTP_200_OK)
async def user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException("Authentication Failed")
    return {'User': user}


# CRUD operations for books
@app.post("/books/", response_model=schemas.Book)
def create_book(user: user_dependency, book: schemas.BookCreate, db: Session = Depends(get_db)):
    db_book = models.Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@app.get("/books/{book_id}", response_model=schemas.Book)
def read_book(user: user_dependency, book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.put("/books/{book_id}", response_model=schemas.Book)
def update_book(user: user_dependency, book_id: int, book: schemas.BookCreate, db: Session = Depends(get_db)):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    for key, value in book.dict().items():
        setattr(db_book, key, value)

    db.commit()
    db.refresh(db_book)
    return db_book


@app.delete("/books/{book_id}", response_model=schemas.Book)
def delete_book(user: user_dependency, book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return book


@app.get("/books/", response_model=list[schemas.Book])
def list_books(user: user_dependency, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    books = db.query(models.Book).offset(skip).limit(limit).all()
    return books


# CRUD operations for members
@app.post("/members/", response_model=schemas.Member)
def create_member(user: user_dependency, member: schemas.MemberCreate, db: Session = Depends(get_db)):
    db_member = models.Member(**member.dict())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@app.get("/members/{member_id}", response_model=schemas.Member)
def read_member(user: user_dependency, member_id: int, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@app.put("/members/{member_id}", response_model=schemas.Member)
def update_member(user: user_dependency, member_id: int, member: schemas.MemberCreate, db: Session = Depends(get_db)):
    db_member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if db_member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    for key, value in member.dict().items():
        setattr(db_member, key, value)

    db.commit()
    db.refresh(db_member)
    return db_member


@app.delete("/members/{member_id}", response_model=schemas.Member)
def delete_member(user: user_dependency, member_id: int, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    db.delete(member)
    db.commit()
    return member


@app.get("/members/", response_model=list[schemas.Member])
def list_members(user: user_dependency, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    members = db.query(models.Member).offset(skip).limit(limit).all()
    return members


@app.post("/borrow/{book_id}/{member_id}", response_model=schemas.BorrowRecord)
def borrow_book(user: user_dependency, book_id: int, member_id: int, db: Session = Depends(get_db)):
    # Check if the book is already borrowed
    existing_record = db.query(BorrowRecord).filter(
        BorrowRecord.book_id == book_id, BorrowRecord.return_date.is_(None)
    ).first()

    if existing_record and existing_record.member_id != member_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This book is already borrowed by another member."
        )

    # Check if the member has already borrowed the same book
    existing_record_same_book = db.query(BorrowRecord).filter(
        BorrowRecord.member_id == member_id, BorrowRecord.book_id == book_id, BorrowRecord.return_date.is_(None)
    ).first()

    if existing_record_same_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already borrowed this book. Return it before borrowing it again."
        )

    borrow_record = BorrowRecord(
        borrow_date=datetime.utcnow(),
        book_id=book_id,
        member_id=member_id
    )

    db.add(borrow_record)
    db.commit()
    db.refresh(borrow_record)

    return borrow_record


@app.post("/return/{book_id}/{member_id}", response_model=schemas.BorrowRecord)
def return_book(user: user_dependency, book_id: int, member_id: int, db: Session = Depends(get_db)):
    # Check if the book is borrowed by the specified member
    borrow_record = db.query(BorrowRecord).filter(
        BorrowRecord.book_id == book_id,
        BorrowRecord.member_id == member_id,
        BorrowRecord.return_date.is_(None)
    ).first()

    if not borrow_record:
        raise ValueError("This book is not borrowed by the specified member.")

    # Set the return date to the current timestamp
    borrow_record.return_date = datetime.utcnow()

    # Delete the BorrowRecord from the database
    db.delete(borrow_record)

    # Commit the changes to the database
    db.commit()

    # Return the updated BorrowRecord as the response
    return borrow_record


@app.get("/members/{member_id}/borrowed_books", response_model=List[schemas.BorrowRecord])
def read_borrowed_books(user: user_dependency, member_id: int, db: Session = Depends(get_db)):
    member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return member.borrow_records


@app.get("/books/{book_id}/borrowing_members", response_model=List[schemas.Member])
def read_borrowing_members(user: user_dependency, book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    borrowing_members = [record.member for record in book.borrow_records if record.member]
    return borrowing_members


@app.get("/borrow-records/{record_id}", response_model=schemas.BorrowRecord)
def read_borrow_record(user: user_dependency, record_id: int, db: Session = Depends(get_db)):
    borrow_record = db.query(models.BorrowRecord).filter(models.BorrowRecord.id == record_id).first()
    if borrow_record is None:
        raise HTTPException(status_code=404, detail="Borrow Record not found")
    return borrow_record


@app.get("/borrow-records/", response_model=list[schemas.BorrowRecord])
def list_borrow_records(user: user_dependency, db: Session = Depends(get_db)):
    borrow_records = db.query(models.BorrowRecord).all()
    return borrow_records


@app.put("/borrow-records/{record_id}", response_model=schemas.BorrowRecord)
def update_borrow_record(user: user_dependency, record_id: int, return_date: schemas.BorrowRecordBase,
                         db: Session = Depends(get_db)):
    borrow_record = db.query(models.BorrowRecord).filter(models.BorrowRecord.id == record_id).first()
    if borrow_record is None:
        raise HTTPException(status_code=404, detail="Borrow Record not found")

    if borrow_record.return_date is not None:
        raise HTTPException(status_code=400, detail="Book has already been returned")

    borrow_record.return_date = return_date.return_date
    db.commit()
    db.refresh(borrow_record)
    return borrow_record


@app.delete("/borrow-records/{record_id}", response_model=schemas.BorrowRecord)
def delete_borrow_record(user: user_dependency, record_id: int, db: Session = Depends(get_db)):
    borrow_record = db.query(models.BorrowRecord).filter(models.BorrowRecord.id == record_id).first()
    if borrow_record is None:
        raise HTTPException(status_code=404, detail="Borrow Record not found")
    db.delete(borrow_record)
    db.commit()
    return borrow_record


# CRUD operations for book reviews
@app.post("/reviews/", response_model=schemas.Review)
def create_review(user: user_dependency, review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    db_review = models.Review(**review.dict())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@app.get("/reviews/{review_id}", response_model=schemas.Review)
def read_review(user: user_dependency, review_id: int, db: Session = Depends(get_db)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@app.get("/reviews/", response_model=List[schemas.Review])
def list_reviews(user: user_dependency, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    reviews = db.query(models.Review).offset(skip).limit(limit).all()
    return reviews


@app.put("/reviews/{review_id}", response_model=schemas.Review)
def update_review(user: user_dependency, review_id: int, review: schemas.ReviewCreate, db: Session = Depends(get_db)):
    db_review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if db_review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    for key, value in review.dict().items():
        setattr(db_review, key, value)

    db.commit()
    db.refresh(db_review)
    return db_review


@app.delete("/reviews/{review_id}", response_model=schemas.Review)
def delete_review(user: user_dependency, review_id: int, db: Session = Depends(get_db)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    db.delete(review)
    db.commit()
    return review


# Endpoint for book recommendations
@app.get("/recommend/{member_id}", response_model=List[schemas.Book])
def recommend_books(user: user_dependency, member_id: int, db: Session = Depends(get_db)):
    # Get the most frequently borrowed book type by the member
    most_borrowed_type = db.query(Book.type_of_book).join(
        BorrowRecord, BorrowRecord.book_id == Book.id
    ).filter(
        BorrowRecord.member_id == member_id, BorrowRecord.return_date.is_(None)
    ).group_by(Book.type_of_book).order_by(func.count().desc()).first()

    if not most_borrowed_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No borrowing history found for the member."
        )

    # Get books of the same type that the member has not already borrowed
    recommended_books = db.query(Book).filter(
        Book.type_of_book == most_borrowed_type[0],
        ~Book.id.in_(
            db.query(BorrowRecord.book_id).filter(
                BorrowRecord.member_id == member_id, BorrowRecord.return_date.is_(None)
            )
        )
    ).all()

    if not recommended_books:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recommended books found."
        )

    return recommended_books
