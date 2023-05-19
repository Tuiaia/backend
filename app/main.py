from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from app.Utils.RedisConnection import redisConnection
from app.Utils.channelParameters import channel
from datetime import datetime
from fastapi.responses import StreamingResponse
from app.Dashboard.wordcloud_generator import WordCloudGenerator
import io

# Create an instance of the RedisConnection class
redis = redisConnection()

app = FastAPI()

# Create an instance of the WordCloudGenerator class
wordcloud_generator = WordCloudGenerator()

# Define the News model
class News(BaseModel):
    news: str

# Schedule the get_feed function to run every 30 seconds on startup
@app.on_event("startup")
@repeat_every(seconds=30)
def get_feed():
    # Publish messages to trigger scraping of news sources
    redis.r.publish(channel['forbes'], 0)
    redis.r.publish(channel['b3'], 0)
    redis.r.publish(channel['googleNews'], 0)

# Run the necessary connections and tasks on startup
@app.on_event("startup")
def run_connections():
    redis.run_mongo()
    redis.run_scraping()
    redis.run_classifer()
    redis.run_feedclassifer()

# Configure CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Classify news based on input text
@app.post('/')
async def classify(news: News):
    return redis.get_classifier(news.news)

# Get the newsletter within a specified date range
@app.get('/feed')
async def newsletter(startdate: str = datetime.today().strftime("%d/%m/%Y"),
                     enddate: str = datetime.today().strftime("%d/%m/%Y")):
    return redis.get_newsletter({'inicio': startdate, 'fim': enddate})

# Generate and stream a word cloud image
@app.get('/wordcloud', response_class=StreamingResponse)
async def get_wordcloud(startdate: str = datetime.today().strftime("%d/%m/%Y"),
                        enddate: str = datetime.today().strftime("%d/%m/%Y")):
    news = redis.get_newsletter({'inicio': startdate, 'fim': enddate})
    news_text = [x['title'] for x in news]
    text = ' '.join(news_text)  # Concatenate all news titles
    wordcloud = wordcloud_generator.generate_wordcloud(text)
    image_bytes = wordcloud_generator.get_wordcloud_image(wordcloud)
    return StreamingResponse(io.BytesIO(image_bytes), media_type="image/png")

# Generate and stream a bar graph word cloud image
@app.get('/barwordcloud', response_class=StreamingResponse)
async def get_wordcloud(startdate: str = datetime.today().strftime("%d/%m/%Y"),
                        enddate: str = datetime.today().strftime("%d/%m/%Y")):
    news = redis.get_newsletter({'inicio': startdate, 'fim': enddate})
    news_text = [x['title'] for x in news]
    text = ' '.join(news_text)  # Concatenate all news titles
    return StreamingResponse(io.BytesIO(wordcloud_generator.get_bar_graph(text)), media_type="image/png")
