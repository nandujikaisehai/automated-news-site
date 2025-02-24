from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
import requests, openai, os, json
from flask_cors import CORS  # Enable CORS to allow frontend requests

app = Flask(__name__)
CORS(app)  # Apply CORS to allow requests from the frontend
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
db = SQLAlchemy(app)

celery = Celery(app.name, broker=os.getenv("REDIS_URL"))
celery.conf.update(app.config)

# News Model
class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    source_url = db.Column(db.String(255))
    published_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source_url": self.source_url
        }

# Fetch News from GNews API with GPT-Based Rewording
@celery.task()
def fetch_news():
    API_URL = "https://gnews.io/api/v4/search?q=latest&lang=en&country=in&max=10&apikey=1a0a27010faea6c340da0de32484439d"

    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Raises an error for 4xx/5xx responses

        data = response.json()
        if "articles" not in data:
            return "Error: No 'articles' field in response"

        articles = data.get("articles", [])

        for article in articles:
            title = article.get("title", "No Title")
            original_content = article.get("description", "No Content Available")
            source_url = article.get("url", "#")

            # 🔹 Reword Content using GPT API
            rewritten_content = rewrite_content(original_content)

            # Store news article in the database
            new_article = NewsArticle(title=title, content=rewritten_content, source_url=source_url)
            db.session.add(new_article)

        db.session.commit()
        return "News updated successfully with GPT-reworded content"

    except requests.exceptions.RequestException as e:
        return f"Error fetching news: {str(e)}"
    except json.decoder.JSONDecodeError:
        return "Error: Invalid JSON response from GNews API"

# Rewriting Content with GPT for SEO Optimization
def rewrite_content(text):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    try:
        response = openai.Completion.create(
            engine="gpt-4",
            prompt=f"Reword this news article in an SEO-friendly way: {text}",
            max_tokens=200
        )
        return response.choices[0].text.strip()
    except Exception as e:
        print(f"Error in GPT rewriting: {e}")
        return text  # Return original content if GPT fails

# Get News from Database
@app.route('/news', methods=['GET'])
def get_news():
    articles = NewsArticle.query.order_by(NewsArticle.published_at.desc()).limit(10).all()
    return jsonify([article.serialize() for article in articles])

# Manually trigger fetching news
@app.route('/fetch-news', methods=['GET'])
def trigger_news_fetch():
    result = fetch_news()  # Calls the Celery task to fetch news
    return jsonify({"message": result}), 200

# Run Flask App with Open Port
if __name__ == '__main__':
    with app.app_context():  # Fix application context issue
        db.create_all()

    port = int(os.environ.get("PORT", 10000))  # Get PORT from environment variables, default 10000
    app.run(host='0.0.0.0', port=port)
