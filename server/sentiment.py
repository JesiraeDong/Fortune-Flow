import os
from openai import OpenAI
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def analyze_sentiment(text):
    """
    Analyze the sentiment of the given text using OpenAI's API.
    Returns 'Positive', 'Negative', or 'Neutral'.
    """
    try:
        # Get API key from environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            return "Neutral"
            
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sentiment analysis tool. Analyze the sentiment of the given text and respond with only one word: 'Positive', 'Negative', or 'Neutral'."},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=10
        )
        
        sentiment = response.choices[0].message.content.strip()
        logger.info(f"Analyzed sentiment for text: {text} -> {sentiment}")
        return sentiment
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {str(e)}")
        return "Neutral" 