from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
import requests, openai, os

app = Flask(__name__)
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
        return {"id": self.id, "title": self.title, "content": self.content, "source_url": self.source_url}

# Fetch News from API
@celery.task()
def fetch_news():
    API_URL = "https://newsapi.org/v2/top-headlines?country=us&apiKey=" + os.getenv("NEWS_API_KEY")
    response = requests.get(API_URL)
    articles = response.json().get("articles", [])

    for article in articles:
        title = article.get("title")
        content = article.get("description")
        source_url = article.get("url")

        # Reword Content using GPT API
        new_content = rewrite_content(content)

        new_article = NewsArticle(title=title, content=new_content, source_url=source_url)
        db.session.add(new_article)
    db.session.commit()
    return "News updated"

# Rewriting Content with GPT
def rewrite_content(text):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Reword this in a new way: {text}",
        max_tokens=200
    )
    return response.choices[0].text.strip()

@app.route('/news', methods=['GET'])
def get_news():
    articles = NewsArticle.query.order_by(NewsArticle.published_at.desc()).limit(10).all()
    return jsonify([article.serialize() for article in articles])

# Run Flask App with Open Port
if __name__ == '__main__':
    with app.app_context():  # Fix application context issue
        db.create_all()

    port = int(os.environ.get("PORT", 10000))  # Get PORT from environment variables, default 10000
    app.run(host='0.0.0.0', port=port)

