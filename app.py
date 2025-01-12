# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
import os
import praw
from models import RedditPost, Audience, Subreddit, Base
from dotenv import load_dotenv
import textrazor
from collections import Counter

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Reddit API Setup
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

# TextRazor setup
TEXT_RAZOR_API_KEY = os.getenv('TEXT_RAZOR_API_KEY')
textrazor.api_key = TEXT_RAZOR_API_KEY
textrazor_client = textrazor.TextRazor(extractors=["entities", "topics"])

@app.route('/api/audiences', methods=['GET'])
def get_audiences():
    session = Session()
    audiences = session.query(Audience).all()
    result = []
    for audience in audiences:
        result.append({
            'name': audience.name,
            'subreddits': [sub.name for sub in audience.subreddits]
        })
    session.close()
    return jsonify({'audiences': result}), 200

@app.route('/api/audiences', methods=['POST'])
def create_audience():
    data = request.get_json()
    name = data.get('name', '').strip()
    subreddits = data.get('subreddits', [])

    if not name:
        return jsonify({'error': 'Audience name is required.'}), 400

    if not isinstance(subreddits, list) or not subreddits:
        return jsonify({'error': 'A list of subreddits is required.'}), 400

    session = Session()
    existing = session.query(Audience).filter_by(name=name).first()
    if existing:
        session.close()
        return jsonify({'error': 'Audience already exists.'}), 400

    new_audience = Audience(name=name)
    session.add(new_audience)
    session.commit()

    # Add subreddits to the audience
    for sub in subreddits:
        sub = sub.strip()
        if not sub:
            continue
        existing_sub = session.query(Subreddit).filter_by(name=sub).first()
        if not existing_sub:
            new_sub = Subreddit(name=sub)
            session.add(new_sub)
            session.commit()
            existing_sub = new_sub
        if existing_sub not in new_audience.subreddits:
            new_audience.subreddits.append(existing_sub)

    session.commit()
    session.close()
    return jsonify({'message': f'Audience "{name}" created successfully with {len(subreddits)} subreddits.'}), 201

@app.route('/api/search_audience', methods=['POST'])
def search_audience():
    data = request.get_json()
    query = data.get('question', '').strip()
    audience_name = data.get('audience', '').strip()

    if not query or not audience_name:
        return jsonify({'error': 'Question and audience are required.'}), 400

    session = Session()
    audience = session.query(Audience).filter_by(name=audience_name).first()
    if not audience:
        session.close()
        return jsonify({'error': 'Audience not found.'}), 404

    subreddits = [sub.name for sub in audience.subreddits]
    if not subreddits:
        session.close()
        return jsonify({'error': 'Audience has no subreddits.'}), 400

    # Use raw query without optimization
    search_text = query

    # Fetch posts from all subreddits
    posts = []
    for sub in subreddits:
        try:
            subreddit = reddit.subreddit(sub)
            search_results = subreddit.search(search_text, limit=50)
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
        except Exception as e:
            print(f"Error fetching posts from {sub}: {e}")
            continue

    # Order posts by score descendingly
    posts_sorted = sorted(posts, key=lambda x: x['score'], reverse=True)

    session.close()
    return jsonify({'posts': posts_sorted, 'topics': []}), 200  # Topics will be fetched separately

@app.route('/api/get_topics', methods=['POST'])
def get_topics():
    data = request.get_json()
    audience_name = data.get('audience', '').strip()

    if not audience_name:
        return jsonify({'error': 'Audience is required.'}), 400

    session = Session()
    audience = session.query(Audience).filter_by(name=audience_name).first()
    if not audience:
        session.close()
        return jsonify({'error': 'Audience not found.'}), 404

    subreddits = [sub.name for sub in audience.subreddits]
    if not subreddits:
        session.close()
        return jsonify({'error': 'Audience has no subreddits.'}), 400

    # Fetch recent posts from all subreddits
    posts = []
    for sub in subreddits:
        try:
            subreddit = reddit.subreddit(sub)
            recent_posts = subreddit.new(limit=100)  # Fetch recent 100 posts
            for post in recent_posts:
                posts.append(post.title)
        except Exception as e:
            print(f"Error fetching posts from {sub}: {e}")
            continue

    session.close()

    # Extract topics from combined text
    topics = extract_topics_from_text(' '.join(posts))

    # Get the 10 most common topics
    top_topics = topics.most_common(10)

    # Convert to list of topic labels
    top_topics_labels = [topic for topic, count in top_topics]

    return jsonify({'topics': top_topics_labels}), 200

def extract_topics_from_text(text):
    try:
        response = textrazor_client.analyze(text)
        topics = [topic.label for topic in response.topics()]
        counter = Counter(topics)
        return counter
    except textrazor.TextRazorError as e:
        print(f"TextRazor Error: {e}")
        return Counter()
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return Counter()

@app.route('/api/filter_posts', methods=['POST'])
def filter_posts():
    data = request.get_json()
    topic = data.get('topic', '').strip()
    audience_name = data.get('audience', '').strip()

    if not topic or not audience_name:
        return jsonify({'error': 'Topic and audience are required.'}), 400

    session = Session()
    audience = session.query(Audience).filter_by(name=audience_name).first()
    if not audience:
        session.close()
        return jsonify({'error': 'Audience not found.'}), 404

    subreddits = [sub.name for sub in audience.subreddits]
    if not subreddits:
        session.close()
        return jsonify({'error': 'Audience has no subreddits.'}), 400

    # Fetch posts containing the topic
    posts = []
    for sub in subreddits:
        try:
            subreddit = reddit.subreddit(sub)
            search_results = subreddit.search(topic, limit=50)
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
        except Exception as e:
            print(f"Error fetching posts from {sub}: {e}")
            continue

    # Order posts by score descendingly
    posts_sorted = sorted(posts, key=lambda x: x['score'], reverse=True)

    session.close()
    return jsonify({'posts': posts_sorted}), 200

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

    session = Session()
    existing_post = session.query(RedditPost).filter_by(post_id=post_id).first()
    if existing_post:
        session.close()
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
    session.close()
    return jsonify({'message': 'Post saved successfully.'}), 201

if __name__ == '__main__':
    app.run(debug=True)
