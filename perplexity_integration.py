import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PerplexityClient:
    """Client for interacting with Perplexity API"""
    
    def __init__(self):
        self.api_key = st.secrets.get('PERPLEXITY_API_KEY', os.getenv('PERPLEXITY_API_KEY'))
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
        
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def ask_health_question(self, question, context=None):
        """
        Ask a health-related question to Perplexity AI
        
        Args:
            question (str): The question to ask
            context (dict): Optional health data context
        
        Returns:
            str: The AI response
        """
        # Build the prompt with health context if provided
        prompt = question
        if context:
            context_str = "\n".join([f"{key}: {value}" for key, value in context.items()])
            prompt = f"Based on this health data:\n{context_str}\n\nQuestion: {question}"
        
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful health and wellness assistant. Provide personalized insights based on the user's health data. Always remind users to consult healthcare professionals for medical advice."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
        
        except requests.exceptions.RequestException as e:
            return f"Error communicating with Perplexity API: {str(e)}"
        except (KeyError, IndexError) as e:
            return f"Error parsing API response: {str(e)}"
    
    def get_health_insights(self, sleep_score, readiness_score, activity_score):
        """
        Get personalized health insights based on Oura scores
        
        Args:
            sleep_score (int): Sleep score from Oura
            readiness_score (int): Readiness score from Oura
            activity_score (int): Activity score from Oura
        
        Returns:
            str: Personalized health insights
        """
        context = {
            "Sleep Score": sleep_score,
            "Readiness Score": readiness_score,
            "Activity Score": activity_score
        }
        
        question = "Based on these scores, what are the top 3 actionable recommendations to improve my health today?"
        
        return self.ask_health_question(question, context)
