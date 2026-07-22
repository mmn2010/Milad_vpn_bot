from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    has_used_test = Column(Boolean, default=False)
    subscriptions = relationship("Subscription", back_populates="user")

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, nullable=False) # نام اشتراک برای نمایش در دکمه
    vpn_username = Column(String, nullable=False)
    volume_name = Column(String)
    volume_bytes = Column(Integer)
    expire_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_test = Column(Boolean, default=False)
    user = relationship("User", back_populates="subscriptions")

engine = create_engine('sqlite:///bot_database.db', connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()
