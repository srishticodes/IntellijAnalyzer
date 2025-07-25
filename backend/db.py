from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../data/intellijanalyzer.db')
engine = create_engine(f'sqlite:///{DB_PATH}', connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Receipt(Base):
    __tablename__ = 'receipts'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    upload_date = Column(Date, nullable=False)
    transactions = relationship("Transaction", back_populates="receipt", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey('receipts.id'), nullable=False, index=True)
    vendor = Column(String, index=True)
    date = Column(Date, index=True)
    amount = Column(Float)
    category = Column(String, index=True)
    currency = Column(String, nullable=True)
    receipt = relationship("Receipt", back_populates="transactions")
    line_items = relationship("LineItem", back_populates="transaction", cascade="all, delete-orphan")

class LineItem(Base):
    __tablename__ = 'line_items'
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False, index=True)
    item = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    transaction = relationship("Transaction", back_populates="line_items")


Index('ix_transactions_date', Transaction.date)
Index('ix_transactions_vendor', Transaction.vendor)


Base.metadata.create_all(bind=engine, checkfirst=True) 