import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from oura_auth import get_oura_data
from perplexity_integration import PerplexityClient
from auth_config import check_password

# Load environment variables
load_dotenv()

# Password check - must be at the top!
if not check_password():
    st.stop()  # Stop execution if not authenticated

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Personal Health Dashboard",
    page_icon="💍",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .chat-container {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">💍 Personal Health Dashboard</h1>', unsafe_allow_html=True)

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'perplexity_client' not in st.session_state:
    try:
        st.session_state.perplexity_client = PerplexityClient()
    except ValueError as e:
        st.error(f"⚠️ {str(e)}")
        st.session_state.perplexity_client = None

# Fetch Oura data
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_oura_data():
    try:
        return get_oura_data()
    except Exception as e:
        st.error(f"Error loading Oura data: {str(e)}")
        return None

data = load_oura_data()

if data:
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "💤 Sleep Analysis", "🤖 AI Health Coach"])
    
    with tab1:
        st.header("Today's Health Metrics")
        
        # Display key metrics in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            sleep_score = data.get('sleep_score', 'N/A')
            st.metric("Sleep Score", sleep_score, help="Your overall sleep quality score")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            readiness_score = data.get('readiness_score', 'N/A')
            st.metric("Readiness Score", readiness_score, help="Your physical readiness for the day")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            activity_score = data.get('activity_score', 'N/A')
            st.metric("Activity Score", activity_score, help="Your daily activity level")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional metrics
        st.subheader("Detailed Metrics")
        
        col4, col5 = st.columns(2)
        
        with col4:
            st.info(f"💓 **Heart Rate**: {data.get('heart_rate', 'N/A')} bpm")
            st.info(f"🌡️ **Temperature**: {data.get('temperature', 'N/A')}°F")
        
        with col5:
            st.info(f"🫁 **HRV**: {data.get('hrv', 'N/A')} ms")
            st.info(f"😴 **Total Sleep**: {data.get('total_sleep', 'N/A')} hours")
    
    with tab2:
        st.header("Sleep Analysis")
        st.write("📊 Detailed sleep insights coming soon...")
        st.info("This section will display your sleep stages, trends, and patterns.")
    
    with tab3:
        st.header("🤖 AI Health Coach powered by Perplexity")
        
        if st.session_state.perplexity_client is None:
            st.warning("⚠️ Perplexity API key not configured. Add PERPLEXITY_API_KEY to your .env file.")
        else:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            
            # Quick insights button
            if st.button("🎯 Get Today's Health Insights", use_container_width=True):
                with st.spinner("Analyzing your health data..."):
                    sleep_score = data.get('sleep_score', 0)
                    readiness_score = data.get('readiness_score', 0)
                    activity_score = data.get('activity_score', 0)
                    
                    insights = st.session_state.perplexity_client.get_health_insights(
                        sleep_score, readiness_score, activity_score
                    )
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": insights
                    })
            
            st.markdown("---")
            
            # Chat interface
            st.subheader("💬 Ask Your Health Questions")
            
            # Display chat history
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f"**You:** {message['content']}")
                else:
                    st.markdown(f"**AI Coach:** {message['content']}")
                st.markdown("---")
            
            # Chat input
            user_question = st.text_input(
                "Ask a question about your health data:",
                placeholder="e.g., Why is my readiness score low today?"
            )
            
            col_send, col_clear = st.columns([3, 1])
            
            with col_send:
                if st.button("Send", use_container_width=True) and user_question:
                    # Add user message to history
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": user_question
                    })
                    
                    # Get AI response with context
                    with st.spinner("Thinking..."):
                        context = {
                            "Sleep Score": data.get('sleep_score', 'N/A'),
                            "Readiness Score": data.get('readiness_score', 'N/A'),
                            "Activity Score": data.get('activity_score', 'N/A'),
                            "Heart Rate": data.get('heart_rate', 'N/A'),
                            "HRV": data.get('hrv', 'N/A')
                        }
                        
                        response = st.session_state.perplexity_client.ask_health_question(
                            user_question, context
                        )
                        
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response
                        })
                    
                    st.rerun()
            
            with col_clear:
                if st.button("Clear Chat", use_container_width=True):
                    st.session_state.chat_history = []
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("Unable to load Oura data. Please check your authentication.")
    st.info("Make sure you've run `python3 oura_auth.py` to authenticate with Oura.")

# Footer
st.markdown("---")
st.caption("🔒 Your data is private and secure. All processing happens locally on your computer.")
