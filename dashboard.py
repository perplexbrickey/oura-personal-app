import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from oura_auth import get_oura_data
from perplexity_integration import PerplexityClient
from auth_config import check_password
from data_storage import HealthDataStorage
import time

# ... your other imports ...

load_dotenv()

# INITIALIZE SESSION STATE FIRST (before password check)
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()
if 'password_correct' not in st.session_state:
    st.session_state.password_correct = False

# Password authentication (NOW it can access session state)
if not check_password():
    st.stop()

# Page config
st.set_page_config(page_title="Personal Health Dashboard", page_icon="💍", layout="wide")

# AUTO-REFRESH FEATURE (Move this AFTER page config and password)
with st.sidebar:
    st.markdown("### ⚙️ Auto-Refresh Settings")
    auto_refresh_enabled = st.checkbox("Enable Auto-Refresh", value=False)
    
    if auto_refresh_enabled:
        refresh_interval = st.select_slider(
            "Refresh Every:",
            options=[30, 60, 120, 180, 240, 300],
            value=120,
            format_func=lambda x: f"{x//60} hour{'s' if x//60 != 1 else ''}" if x >= 60 else f"{x} min"
        )
        
        time_since_refresh = int(time.time() - st.session_state.last_refresh)
        time_until_refresh = refresh_interval * 60 - time_since_refresh
        
        if time_until_refresh > 0:
            st.caption(f"⏱️ Next refresh in {time_until_refresh // 60}m {time_until_refresh % 60}s")
        
        if time_since_refresh >= (refresh_interval * 60):
            st.session_state.last_refresh = time.time()
            st.rerun()
    else:
        st.caption("💡 Enable to get updated guidance throughout your day")
    
    st.markdown("---")
    st.markdown("### 📱 Quick Actions")
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.session_state.last_refresh = time.time()
        st.cache_data.clear()
        st.rerun()

# Custom CSS
st.markdown("""
    <style>
    .main-header {font-size: 3rem; color: #FF6B6B; text-align: center; margin-bottom: 2rem;}
    .readiness-high {background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 2rem; border-radius: 15px; text-align: center; font-size: 2rem; font-weight: bold; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    .readiness-medium {background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 2rem; border-radius: 15px; text-align: center; font-size: 2rem; font-weight: bold; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    .readiness-low {background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; padding: 2rem; border-radius: 15px; text-align: center; font-size: 2rem; font-weight: bold; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    .summary-box {background-color: #f8f9fa; border-left: 5px solid #667eea; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">💍 Personal Health Dashboard</h1>', unsafe_allow_html=True)

# Initialize
storage = HealthDataStorage()
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'perplexity_client' not in st.session_state:
    try:
        st.session_state.perplexity_client = PerplexityClient()
    except:
        st.session_state.perplexity_client = None

@st.cache_data(ttl=3600)
def load_oura_data():
    try:
        return get_oura_data()
    except Exception as e:
        st.error(f"Error loading Oura data: {str(e)}")
        return None

data = load_oura_data()

if data:
    today = datetime.now().date()
    storage.add_daily_entry(today, data.get('sleep_score', 0), data.get('readiness_score', 0), 
                           data.get('activity_score', 0), data.get('heart_rate'), data.get('hrv'), 
                           data.get('temperature'), data.get('total_sleep'))
    
    readiness = data.get('readiness_score', 0) if data.get('readiness_score') != 'N/A' else 0
    sleep_score = data.get('sleep_score', 0) if data.get('sleep_score') != 'N/A' else 0
    activity_score = data.get('activity_score', 0) if data.get('activity_score') != 'N/A' else 0
    
        # MORNING READINESS ALERT WITH TIME-BASED UPDATES
    st.markdown("## 🌅 Your Readiness Alert")
    
    current_hour = datetime.now().hour
    
    # Determine time of day context
    if 4 <= current_hour < 9:
        time_context = "Early Morning (4-9 AM)"
        time_emoji = "🌅"
    elif 9 <= current_hour < 12:
        time_context = "Mid-Morning (9 AM-12 PM)"
        time_emoji = "☀️"
    elif 12 <= current_hour < 15:
        time_context = "Early Afternoon (12-3 PM)"
        time_emoji = "🌤️"
    elif 15 <= current_hour < 18:
        time_context = "Late Afternoon (3-6 PM)"
        time_emoji = "🌆"
    elif 18 <= current_hour < 21:
        time_context = "Evening (6-9 PM)"
        time_emoji = "🌙"
    else:
        time_context = "Night (9 PM-4 AM)"
        time_emoji = "🌃"
    
    st.caption(f"{time_emoji} **{time_context}** - Last updated: {datetime.now().strftime('%I:%M %p')}")
    
    # Main readiness display
    if readiness >= 80:
        st.markdown(f'<div class="readiness-high">🟢 GO TIME! Readiness: {readiness}<br/><span style="font-size: 1.2rem;">Perfect for intense workouts, important meetings, or challenging projects</span></div>', unsafe_allow_html=True)
        
        # Time-specific guidance for HIGH readiness
        if 4 <= current_hour < 9:
            quick_action = "✅ **Morning Plan:** Great start! Tackle your hardest tasks first. Schedule important meetings or intense workout."
        elif 9 <= current_hour < 12:
            quick_action = "✅ **Mid-Morning:** Still going strong! Perfect time for deep work or challenging projects."
        elif 12 <= current_hour < 15:
            quick_action = "✅ **Afternoon:** Maintain momentum! Good for collaboration and important decisions."
        elif 15 <= current_hour < 18:
            quick_action = "✅ **Late Afternoon:** Energy holding steady. Finish strong with priority tasks."
        elif 18 <= current_hour < 21:
            quick_action = "✅ **Evening:** Great recovery today! Light activity or meal prep for tomorrow's success."
        else:
            quick_action = "✅ **Wind Down:** Excellent readiness today! Prioritize sleep to maintain tomorrow."
            
    elif readiness >= 60:
        st.markdown(f'<div class="readiness-medium">🟡 STEADY APPROACH - Readiness: {readiness}<br/><span style="font-size: 1.2rem;">Good for moderate activity and standard work tasks</span></div>', unsafe_allow_html=True)
        
        # Time-specific guidance for MODERATE readiness
        if 4 <= current_hour < 9:
            quick_action = "⚖️ **Morning Plan:** Start slow. Warm up with routine tasks before big work. Consider light exercise."
        elif 9 <= current_hour < 12:
            quick_action = "⚖️ **Mid-Morning:** Pace yourself. Alternate challenging work with easier tasks."
        elif 12 <= current_hour < 15:
            quick_action = "⚖️ **Afternoon:** Energy may be dipping. Take a walk, grab healthy lunch, stay hydrated."
        elif 15 <= current_hour < 18:
            quick_action = "⚖️ **Late Afternoon:** Focus on wrapping up, not starting new big projects. Plan for tomorrow."
        elif 18 <= current_hour < 21:
            quick_action = "⚖️ **Evening:** Light dinner, gentle movement. Prep for good sleep tonight."
        else:
            quick_action = "⚖️ **Wind Down:** Rest time. Tomorrow requires better recovery - prioritize sleep."
            
    else:
        st.markdown(f'<div class="readiness-low">🔴 RECOVERY MODE - Readiness: {readiness}<br/><span style="font-size: 1.2rem;">Prioritize rest and essential tasks only</span></div>', unsafe_allow_html=True)
        
        # Time-specific guidance for LOW readiness
        if 4 <= current_hour < 9:
            quick_action = "🛑 **Morning Plan:** Your body needs recovery. Stick to essential tasks only. Skip intense workout. Consider going back to sleep if possible."
        elif 9 <= current_hour < 12:
            quick_action = "🛑 **Mid-Morning:** Take it easy. Delegate what you can. Focus on simple, low-energy tasks."
        elif 12 <= current_hour < 15:
            quick_action = "🛑 **Afternoon:** Rest if possible. Light walk, healthy meal, hydrate. Avoid caffeine after 2 PM."
        elif 15 <= current_hour < 18:
            quick_action = "🛑 **Late Afternoon:** Almost through the day. Minimal effort mode. Clear calendar for tomorrow if needed."
        elif 18 <= current_hour < 21:
            quick_action = "🛑 **Evening:** Early to bed tonight! Light dinner, no screen time before sleep. Tomorrow depends on tonight's recovery."
        else:
            quick_action = "🛑 **Get Sleep Now:** Your body desperately needs rest. Set up for 8+ hours of quality sleep."
    
    st.info(quick_action)
    
    # Add refresh reminder
    if current_hour >= 4:
        st.caption("💡 Refresh this page every few hours for updated guidance based on time of day and energy levels.")
    
    # TABS
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Today's Metrics", "🍽️ Smart Meal Recommendations", "📈 Trend Graphs", "📋 Weekly Summary", "🤖 AI Coach"])    # TAB 1: TODAY'S METRICS
    with tab1:
        st.header("Today's Health Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sleep Score", sleep_score)
        with col2:
            st.metric("Readiness Score", readiness)
        with col3:
            st.metric("Activity Score", activity_score)
        
        st.subheader("Detailed Metrics")
        col4, col5 = st.columns(2)
        with col4:
            st.info(f"💓 **Heart Rate**: {data.get('heart_rate', 'N/A')} bpm")
            st.info(f"🫁 **HRV**: {data.get('hrv', 'N/A')} ms")
        with col5:
            st.info(f"🌡️ **Temperature**: {data.get('temperature', 'N/A')}°F")
            st.info(f"😴 **Total Sleep**: {data.get('total_sleep', 'N/A')} hours")
    
        # TAB 2: MEAL RECOMMENDATIONS
    with tab2:
        st.header("🍽️ Smart Meal Recommendations")
        st.write("Personalized nutrition suggestions based on your health data and recovery needs.")
        
        # Determine meal strategy based on readiness
        if readiness >= 80:
            meal_strategy = "🟢 **High Performance Nutrition**"
            meal_focus = "Focus on protein-rich meals to support your peak performance. Good for pre/post workout meals."
            meal_types = ["Grilled chicken or salmon", "Lean steak with vegetables", "High-protein bowls", "Performance smoothies"]
            avoid = ["Heavy, fried foods", "High-sugar meals"]
        elif readiness >= 60:
            meal_strategy = "🟡 **Balanced Nutrition**"
            meal_focus = "Opt for well-rounded meals with good protein, complex carbs, and vegetables."
            meal_types = ["Balanced grain bowls", "Lean proteins with rice", "Mediterranean-style meals", "Salads with protein"]
            avoid = ["Excessive sugar", "Very heavy meals"]
        else:
            meal_strategy = "🔴 **Recovery Nutrition**"
            meal_focus = "Choose light, easy-to-digest, anti-inflammatory foods to support recovery."
            meal_types = ["Light soups", "Grilled fish", "Vegetable-forward dishes", "Anti-inflammatory foods"]
            avoid = ["Heavy fried foods", "Spicy foods", "Large portions"]
        
        st.markdown(f"### {meal_strategy}")
        st.info(meal_focus)
        
        col_meal1, col_meal2 = st.columns(2)
        with col_meal1:
            st.markdown("**✅ Recommended:**")
            for meal in meal_types:
                st.write(f"• {meal}")
        
        with col_meal2:
            st.markdown("**❌ Avoid:**")
            for item in avoid:
                st.write(f"• {item}")
        
        # Meal timing recommendations
        st.markdown("---")
        st.subheader("⏰ Optimal Meal Timing")
        
        current_hour = datetime.now().hour
        
        if sleep_score < 70:
            st.write("🌙 **Tonight's dinner:** Eat light 3+ hours before bed to improve sleep quality")
            st.write("☀️ **Tomorrow's breakfast:** Focus on protein to stabilize energy")
        
        if readiness >= 75:
            st.write("💪 **Pre-workout:** 1-2 hours before - light protein & complex carbs")
            st.write("🥤 **Post-workout:** Within 30 min - protein shake or meal")
        
        if activity_score < 70:
            st.write("🥗 **Keep it light:** Smaller, frequent meals may help with energy")
        
        # AI-Powered Restaurant Finder
        st.markdown("---")
        st.subheader("🤖 AI-Powered Restaurant Finder")
        
        if st.session_state.perplexity_client:
            col_ai1, col_ai2 = st.columns(2)
            
            with col_ai1:
                if st.button("🍴 Find Healthy Restaurants Near Me", use_container_width=True):
                    with st.spinner("Searching for healthy options in Plano, TX..."):
                        context = {
                            "Location": "Plano, Texas",
                            "Readiness Score": readiness,
                            "Meal Strategy": meal_strategy
                        }
                        prompt = f"I'm in Plano, Texas and my fitness readiness score is {readiness}/100. Recommend 5 healthy restaurants or meal options available for delivery (DoorDash, Uber Eats) that would support my current health state. Include restaurant names and what to order."
                        
                        recommendations = st.session_state.perplexity_client.ask_health_question(prompt, context)
                        st.markdown("### 📍 Restaurant Recommendations:")
                        st.markdown(recommendations)
            
            with col_ai2:
                if st.button("🥗 What Should I Eat Today?", use_container_width=True):
                    with st.spinner("Analyzing your health data..."):
                        context = {
                            "Sleep Score": sleep_score,
                            "Readiness Score": readiness,
                            "Activity Score": activity_score,
                            "Location": "Plano, Texas"
                        }
                        prompt = f"Based on my health scores (Sleep: {sleep_score}, Readiness: {readiness}, Activity: {activity_score}), what specific meals should I prioritize today? Give me 3 specific meal ideas for breakfast, lunch, and dinner that support my recovery and performance."
                        
                        meal_plan = st.session_state.perplexity_client.ask_health_question(prompt, context)
                        st.markdown("### 🍱 Today's Personalized Meal Plan:")
                        st.markdown(meal_plan)
        else:
            st.warning("⚠️ Perplexity AI not configured. AI recommendations unavailable.")
        
        # Quick Links
        st.markdown("---")
        st.subheader("🚀 Quick Order Links")
        
        col_link1, col_link2, col_link3 = st.columns(3)
        
        with col_link1:
            st.markdown("[![DoorDash](https://img.shields.io/badge/DoorDash-FF3008?style=for-the-badge&logo=doordash&logoColor=white)](https://www.doordash.com)")
            st.caption("Order delivery in Plano")
        
        with col_link2:
            st.markdown("[![Uber Eats](https://img.shields.io/badge/Uber_Eats-5FB709?style=for-the-badge&logo=ubereats&logoColor=white)](https://www.ubereats.com)")
            st.caption("Browse nearby restaurants")
        
        with col_link3:
            st.markdown("[![Grubhub](https://img.shields.io/badge/Grubhub-F63440?style=for-the-badge&logo=grubhub&logoColor=white)](https://www.grubhub.com)")
            st.caption("Find local options")
        
        # Hydration reminder
        st.markdown("---")
        st.info("💧 **Hydration Reminder:** Based on your activity score of " + str(activity_score) + ", aim for at least " + 
               ("10 cups" if activity_score >= 75 else "8 cups" if activity_score >= 60 else "6-8 cups") + " of water today.")
    # TAB 3: TREND GRAPHS
    with tab3:
        st.header("📈 Health Trends")
        period = st.selectbox("View Period", ["7 Days", "30 Days", "90 Days", "All Time"])
        days_map = {"7 Days": 7, "30 Days": 30, "90 Days": 90, "All Time": 36500}
        selected_days = days_map[period]
        entries = storage.get_recent_entries(selected_days)
        
        if len(entries) > 1:
            df = pd.DataFrame(entries)
            df['date'] = pd.to_datetime(df['date'])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['sleep_score'], name='Sleep Score', line=dict(color='#4A90E2', width=2), mode='lines+markers'))
            fig.add_trace(go.Scatter(x=df['date'], y=df['readiness_score'], name='Readiness Score', line=dict(color='#50C878', width=2), mode='lines+markers'))
            fig.add_trace(go.Scatter(x=df['date'], y=df['activity_score'], name='Activity Score', line=dict(color='#FF6B6B', width=2), mode='lines+markers'))
            fig.update_layout(title=f"Health Scores - {period}", xaxis_title="Date", yaxis_title="Score", hovermode='x unified', height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            if any(df['total_sleep'].notna()):
                fig2 = go.Figure(data=[go.Bar(x=df['date'], y=df['total_sleep'], marker_color='#9B59B6')])
                fig2.update_layout(title="Total Sleep Hours", xaxis_title="Date", yaxis_title="Hours", height=350)
                st.plotly_chart(fig2, use_container_width=True)
            
            st.subheader("📊 Period Statistics")
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.metric("Avg Sleep Score", f"{df['sleep_score'].mean():.0f}")
            with col_stat2:
                st.metric("Avg Readiness", f"{df['readiness_score'].mean():.0f}")
            with col_stat3:
                st.metric("Avg Activity", f"{df['activity_score'].mean():.0f}")
        else:
            st.info(f"Not enough data for {period} view. Keep using the dashboard daily to build your trends!")
    
    # TAB 4: WEEKLY SUMMARY
    with tab4:
        st.header("📋 Weekly Executive Summary")
        st.caption(f"Summary for the week ending {today}")
        summary = storage.get_weekly_summary()
        
        if summary and summary['total_days'] > 0:
            st.markdown('<div class="summary-box">', unsafe_allow_html=True)
            st.subheader("📊 This Week's Averages")
            col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
            with col_sum1:
                st.metric("Avg Sleep", f"{summary['sleep_avg']}")
            with col_sum2:
                st.metric("Avg Readiness", f"{summary['readiness_avg']}")
            with col_sum3:
                st.metric("Avg Activity", f"{summary['activity_avg']}")
            with col_sum4:
                st.metric("Avg Sleep Hours", f"{summary['avg_sleep_hours']}")
            
            st.subheader("🎯 Week Highlights")
            if summary['best_day']:
                st.success(f"**Best Day:** {summary['best_day']['date']} (Readiness: {summary['best_day']['readiness_score']})")
            if summary['worst_day']:
                st.warning(f"**Recovery Needed:** {summary['worst_day']['date']} (Readiness: {summary['worst_day']['readiness_score']})")
            
            st.subheader("💡 Recommendations for Next Week")
            if summary['sleep_avg'] < 70:
                st.write("🛏️ Focus on improving sleep quality - aim for consistent bedtime")
            if summary['readiness_avg'] < 70:
                st.write("⚡ Your body needs more recovery - consider lighter workouts")
            if summary['avg_sleep_hours'] < 7:
                st.write("😴 Increase sleep duration - target 7-8 hours nightly")
            if summary['readiness_avg'] >= 75:
                st.write("✨ Great recovery week! You're ready for challenging goals")
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Use the dashboard for at least 3 days to see your weekly summary!")
    # TAB 5: AI COACH
    with tab5:
        st.header("🤖 AI Health Coach powered by Perplexity")
        if st.session_state.perplexity_client is None:
            st.warning("⚠️ Perplexity API key not configured.")
        else:
            if st.button("🎯 Get Today's Health Insights", use_container_width=True):
                with st.spinner("Analyzing your health data..."):
                    insights = st.session_state.perplexity_client.get_health_insights(sleep_score, readiness, activity_score)
                    st.session_state.chat_history.append({"role": "assistant", "content": insights})
            
            st.markdown("---")
            st.subheader("💬 Ask Your Health Questions")
            
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f"**You:** {message['content']}")
                else:
                    st.markdown(f"**AI Coach:** {message['content']}")
                st.markdown("---")
            
            user_question = st.text_input("Ask a question about your health data:", placeholder="e.g., Why is my readiness score low today?")
            
            col_send, col_clear = st.columns([3, 1])
            with col_send:
                if st.button("Send", use_container_width=True) and user_question:
                    st.session_state.chat_history.append({"role": "user", "content": user_question})
                    with st.spinner("Thinking..."):
                        context = {
                            "Sleep Score": sleep_score,
                            "Readiness Score": readiness,
                            "Activity Score": activity_score,
                            "Heart Rate": data.get('heart_rate', 'N/A'),
                            "HRV": data.get('hrv', 'N/A')
                        }
                        response = st.session_state.perplexity_client.ask_health_question(user_question, context)
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.rerun()
            
            with col_clear:
                if st.button("Clear Chat", use_container_width=True):
                    st.session_state.chat_history = []
                    st.rerun()

else:
    st.error("Unable to load Oura data. Please check your authentication.")
    st.info("Make sure you've run authentication and your API credentials are configured.")

st.markdown("---")
st.caption("🔒 Your data is private and secure. All processing happens with encrypted credentials.")

