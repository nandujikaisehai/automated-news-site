from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from celery import Celery
from flask_cors import CORS  # Enable CORS to allow frontend requests
import requests, openai, os

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")  # Use env variable for security
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Enable Flask-Migrate
CORS(app)  # Enable CORS for frontend access

# Initialize Celery for Background Tasks
celery = Celery(app.name, broker=os.getenv("REDIS_URL"))  # Use Redis URL from env
celery.conf.update(app.config)

# NewsArticle Model (Includes Image Support)
class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    source_url = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)  # ✅ Added Image URL Support
    published_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source_url": self.source_url,
            "image_url": self.image_url
        }

# ✅ Background Task to Fetch News
@celery.task()
def fetch_news():
    API_URL = "https://gnews.io/api/v4/search?q=latest&lang=en&country=in&max=10&apikey=1a0a27010faea6c340da0de32484439d"
    response = requests.get(API_URL)
    articles = response.json().get("articles", [])

    for article in articles:
        title = article.get("title")
        content = article.get("description")
        source_url = article.get("url")
        image_url = article.get("image")  # ✅ Fetch the image URL

        # Reword Content with GPT for SEO
        new_content = rewrite_content(content)

        # Store in the database
        new_article = NewsArticle(title=title, content=new_content, source_url=source_url, image_url=image_url)
        db.session.add(new_article)

    db.session.commit()
    return "News updated"

# ✅ Function to Reword Content for SEO
def rewrite_content(text):
    if not text:
        return "No content available"
    
    openai.api_key = os.getenv("OPENAI_API_KEY")  # Use OpenAI API key from env

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional journalist. Reword the following news article in an SEO-friendly way, keeping it factual and engaging."},
            {"role": "user", "content": text}
        ],
        max_tokens=250
    )
    
    return response.choices[0].message["content"].strip()

# ✅ API Endpoint to Trigger News Fetching Manually
@app.route('/fetch-news', methods=['GET'])
def trigger_news_fetch():
    fetch_news()
    return jsonify({"message": "News updated successfully from GNews API"})

# ✅ API Endpoint to Fetch Stored News
@app.route('/news', methods=['GET'])
def get_news():
    articles = NewsArticle.query.order_by(NewsArticle.published_at.desc()).limit(10).all()
    return jsonify([article.serialize() for article in articles])

# ✅ Start Flask App
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

