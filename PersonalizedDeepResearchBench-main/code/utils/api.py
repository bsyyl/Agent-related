import os
from typing import Optional, Dict, Any
# from google import genai
# from google.genai import types
import requests
import logging
from openai import OpenAI

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


logging.getLogger('google').setLevel(logging.WARNING)
logging.getLogger('google.genai').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

# Read API keys from environment variables
API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("BASE_URL", "")
READ_API_KEY = os.environ.get("JINA_API_KEY", "")
FACT_Model = "gpt-5-mini"
Model = "gpt-5"

class AIClient:
    def __init__(self, api_key=API_KEY, base_url=BASE_URL, model=Model):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("LLM API key not provided! Please set OPENAI_API_KEY environment variable.")
        self.base_url = base_url or os.environ.get("BASE_URL")
        if not self.base_url:
            self.base_url = "https://api.openai.com/v1"
        
        # Configure client
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.model = model

    def generate(self, user_prompt: str, system_prompt: str = "", model: Optional[str] = None) -> str:
        """
        Generate text response
        """
        model_to_use = model or self.model
        
        # Build request content
        contents = []
        
        # Add system prompt
        if system_prompt:
            contents.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add user prompt
        contents.append({
            "role": "user", 
            "content": user_prompt
        })
        
        try:
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=contents
            )
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Failed to generate content: {str(e)}")


class WebScrapingJinaTool:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("JINA_API_KEY")
        if not self.api_key:
            raise ValueError("Jina API key not provided! Please set JINA_API_KEY environment variable.")

    def __call__(self, url: str) -> Dict[str, Any]:
        try:
            jina_url = f'https://r.jina.ai/{url}'
            headers = {
                "Accept": "application/json",
                'Authorization': self.api_key,
                'X-Timeout': "60000",
                "X-With-Generated-Alt": "true",
            }
            response = requests.get(jina_url, headers=headers)

            if response.status_code != 200:
                raise Exception(f"Jina AI Reader Failed for {url}: {response.status_code}")

            response_dict = response.json()

            return {
                'url': response_dict['data']['url'],
                'title': response_dict['data']['title'],
                'description': response_dict['data']['description'],
                'content': response_dict['data']['content'],
                'publish_time': response_dict['data'].get('publishedTime', 'unknown')
            }

        except Exception as e:
            logger.error(str(e))
            return {
                'url': url,
                'content': '',
                'error': str(e)
            }
        
jina_tool = WebScrapingJinaTool()

def scrape_url(url: str) -> Dict[str, Any]:
    return jina_tool(url)
    
def call_model(user_prompt: str) -> str:
    client = AIClient(model=FACT_Model)
    return client.generate(user_prompt)

if __name__ == "__main__":
    url = ""
    result = scrape_url(url)
    print(result)