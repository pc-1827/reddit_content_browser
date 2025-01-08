# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import praw
from models import RedditPost, Base
from dotenv import load_dotenv
import spacy

load_dotenv()

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

nlp = spacy.load('en_core_web_sm')

@app.route('/api/search', methods=['POST'])
def search_reddit():
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': 'No question provided.'}), 400

    optimized_keywords = optimize_keywords(question)
    if not optimized_keywords:
        return jsonify({'error': 'Failed to generate optimized keywords.'}), 500

    posts = fetch_reddit_posts(optimized_keywords)

    return jsonify({'posts': posts}), 200

def optimize_keywords(question):
    try:
        doc = nlp(question)

        noun_chunks = list(doc.noun_chunks)
        noun_keywords = [chunk.text for chunk in noun_chunks]

        named_entities = [ent.text for ent in doc.ents]

        keywords = list(set(noun_keywords + named_entities))

        optimized_keywords = ', '.join(keywords)

        print(f"Optimized Keywords: {optimized_keywords}")

        return optimized_keywords
    except Exception as e:
        print(f"spaCy error: {e}")
        return None

def fetch_reddit_posts(keywords):
    try:
        subreddit = reddit.subreddit('all')
        search_results = subreddit.search(keywords, limit=50)
        posts = []
        for post in search_results:
            posts.append({
                'id': post.id,
                'title': post.title,
                'url': post.url,
                'score': post.score,
                'num_comments': post.num_comments,
                'created_utc': post.created_utc,
                'subreddit': post.subreddit.display_name,
                'permalink': post.permalink
            })
        return posts
    except Exception as e:
        print(f"Error fetching Reddit posts: {e}")
        return []

@app.route('/api/save', methods=['POST'])
def save_post():
    data = request.get_json()
    post_id = data.get('id')
    title = data.get('title')
    url = data.get('url')
    score = data.get('score')
    num_comments = data.get('num_comments')
    created_utc = data.get('created_utc')
    subreddit = data.get('subreddit')
    permalink = data.get('permalink')

    if not post_id or not title or not url:
        return jsonify({'error': 'Missing required post information.'}), 400

    try:
        existing_post = session.query(RedditPost).filter_by(post_id=post_id).first()
        if existing_post:
            return jsonify({'message': 'Post already saved.'}), 200

        new_post = RedditPost(
            post_id=post_id,
            title=title,
            url=url,
            score=score,
            num_comments=num_comments,
            created_utc=created_utc,
            subreddit=subreddit,
            permalink=permalink
        )
        session.add(new_post)
        session.commit()
        return jsonify({'message': 'Post saved successfully.'}), 201
    except Exception as e:
        session.rollback()
        print(f"Error saving post: {e}")
        return jsonify({'error': 'Failed to save post.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
