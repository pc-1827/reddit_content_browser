# models.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Float

Base = declarative_base()

class RedditPost(Base):
    __tablename__ = 'reddit_posts'
    id = Column(Integer, primary_key=True)
    post_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    score = Column(Integer)
    num_comments = Column(Integer)
    created_utc = Column(Float)
    subreddit = Column(String)
    permalink = Column(String)
