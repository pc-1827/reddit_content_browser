# models.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Float, Table, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

# Association table for Audience and Subreddits
audience_subreddits = Table('audience_subreddits', Base.metadata,
    Column('audience_id', Integer, ForeignKey('audiences.id')),
    Column('subreddit_id', Integer, ForeignKey('subreddits.id'))
)

class RedditPost(Base):
    __tablename__ = 'reddit_posts'
    id = Column(Integer, primary_key=True)
    post_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    score = Column(Integer)
    num_comments = Column(Integer)
    created_utc = Column(Float)  # UNIX timestamp
    subreddit = Column(String)
    permalink = Column(String)

class Audience(Base):
    __tablename__ = 'audiences'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    subreddits = relationship('Subreddit', secondary=audience_subreddits, back_populates='audiences')

class Subreddit(Base):
    __tablename__ = 'subreddits'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    audiences = relationship('Audience', secondary=audience_subreddits, back_populates='subreddits')
