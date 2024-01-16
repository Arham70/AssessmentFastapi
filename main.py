from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import schemas
from typing import List, Annotated
import auth
from starlette import status

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router)


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


@app.post("/borrow-records/", response_model=schemas.BorrowRecord)
def create_borrow_record(user: user_dependency, borrow_record: schemas.BorrowRecordCreate,
                         db: Session = Depends(get_db)):
    # Check if the book is available for borrowing
    book = db.query(models.Book).filter(models.Book.id == borrow_record.book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if any(record.return_date is None for record in book.borrow_records):
        raise HTTPException(status_code=400, detail="Book is already borrowed")

    # Check if the member exists
    member = db.query(models.Member).filter(models.Member.id == borrow_record.member_id).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    db_borrow_record = models.BorrowRecord(**borrow_record.dict())
    db.add(db_borrow_record)
    db.commit()
    db.refresh(db_borrow_record)
    return db_borrow_record


@app.get("/borrow-records/{record_id}", response_model=schemas.BorrowRecord)
def read_borrow_record(user: user_dependency, record_id: int, db: Session = Depends(get_db)):
    borrow_record = db.query(models.BorrowRecord).filter(models.BorrowRecord.id == record_id).first()
    if borrow_record is None:
        raise HTTPException(status_code=404, detail="Borrow Record not found")
    return borrow_record


@app.get("/borrow-records/", response_model=list[schemas.BorrowRecord])
def list_borrow_records(user: user_dependency, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    borrow_records = db.query(models.BorrowRecord).offset(skip).limit(limit).all()
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
