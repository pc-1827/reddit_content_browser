# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import praw
from models import RedditPost, Base
from dotenv import load_dotenv
import textrazor

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Reddit API Setup
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

# TextRazor setup
TEXT_RAZOR_API_KEY = os.getenv('TEXT_RAZOR_API_KEY')
textrazor.api_key = TEXT_RAZOR_API_KEY
client = textrazor.TextRazor(extractors=["entities", "topics"])

def optimize_keywords(question):
    try:
        response = client.analyze(question)
        keywords = []

        for entity in response.entities():
            keywords.append(entity.id)

        for topic in response.topics():
            keywords.append(topic.label)

        seen = set()
        unique_keywords = []
        for keyword in keywords:
            lower_kw = keyword.lower()
            if lower_kw not in seen:
                seen.add(lower_kw)
                unique_keywords.append(keyword)

        # Fallback if no keywords found
        if not unique_keywords:
            return question.strip()

        optimized_keywords = ', '.join(unique_keywords)
        print(f"Optimized Keywords: {optimized_keywords}")
        return optimized_keywords

    except textrazor.TextRazorError as e:
        print(f"TextRazor Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None

@app.route('/api/search', methods=['POST'])
def search_reddit():
    data = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'No question provided.'}), 400

    optimized_keywords = optimize_keywords(question)
    if optimized_keywords is None:
        return jsonify({'error': 'Failed to generate optimized keywords.'}), 500

    # Fetch posts using the optimized keywords
    posts = fetch_reddit_posts(optimized_keywords)

    # Extract unique subreddits from the fetched posts
    subreddits = list({post['subreddit'] for post in posts})

    return jsonify({'posts': posts, 'subreddits': subreddits}), 200

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

@app.route('/api/comments', methods=['POST'])
def fetch_comments():
    data = request.get_json()
    post_permalink = data.get('permalink', '').strip()

    if not post_permalink:
        return jsonify({'error': 'No permalink provided.'}), 400

    try:
        submission = reddit.submission(url=f"https://reddit.com{post_permalink}")
        submission.comments.replace_more(limit=0)  # Remove "MoreComments" objects
        comments = [
            {
                'id': comment.id,
                'author': comment.author.name if comment.author else 'Unknown',
                'body': comment.body,
                'score': comment.score,
                'created_utc': comment.created_utc
            }
            for comment in submission.comments.list()
        ]
        return jsonify({'comments': comments}), 200
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return jsonify({'error': 'Failed to fetch comments.'}), 500

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

    # Save to database
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
