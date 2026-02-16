#!/usr/bin/env python3
"""
Oura Ring OAuth Authentication Script

This script handles the OAuth 2.0 authentication flow for accessing
the Oura API. It will:
1. Open a browser for user authorization
2. Start a local server to receive the authorization code
3. Exchange the code for access and refresh tokens
4. Save tokens to your .env file

IMPORTANT: Your credentials and tokens stay LOCAL.
Never commit your .env file to GitHub!
"""

import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:8080')

# Oura OAuth endpoints
AUTHORIZE_URL = 'https://cloud.ouraring.com/oauth/authorize'
TOKEN_URL = 'https://api.ouraring.com/oauth/token'

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles the OAuth callback from Oura"""
    
    def do_GET(self):
        # Parse the authorization code from the callback URL
        query_components = parse_qs(urlparse(self.path).query)
        
        if 'code' in query_components:
            self.server.auth_code = query_components['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authorization successful!</h1><p>You can close this window and return to your terminal.</p></body></html>')
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authorization failed</h1><p>No authorization code received.</p></body></html>')
    
    def log_message(self, format, *args):
        # Suppress log messages
        pass

def get_authorization_url():
    """Generate the OAuth authorization URL"""
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'email personal daily heartrate workout tag session spo2 stress'
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    return f"{AUTHORIZE_URL}?{query_string}"

def exchange_code_for_tokens(auth_code):
    """Exchange authorization code for access and refresh tokens"""
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    response = requests.post(TOKEN_URL, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def save_tokens_to_env(access_token, refresh_token):
    """Save tokens to .env file"""
    env_file = '.env'
    
    # Create .env if it doesn't exist
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            f.write(f"CLIENT_ID={CLIENT_ID}\n")
            f.write(f"CLIENT_SECRET={CLIENT_SECRET}\n")
            f.write(f"REDIRECT_URI={REDIRECT_URI}\n")
    
    # Update tokens
    set_key(env_file, 'ACCESS_TOKEN', access_token)
    set_key(env_file, 'REFRESH_TOKEN', refresh_token)
    print(f"\n✓ Tokens saved to {env_file}")

def main():
    """Main OAuth flow"""
    print("\n🔐 Oura OAuth Authentication\n")
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Error: CLIENT_ID and CLIENT_SECRET must be set in .env file")
        print("\nPlease:")
        print("1. Copy .env.example to .env")
        print("2. Fill in your CLIENT_ID and CLIENT_SECRET from https://developer.ouraring.com")
        return
    
    # Step 1: Open authorization URL in browser
    auth_url = get_authorization_url()
    print(f"Opening browser for authorization...")
    print(f"If browser doesn't open, visit: {auth_url}\n")
    webbrowser.open(auth_url)
    
    # Step 2: Start local server to receive callback
    port = int(urlparse(REDIRECT_URI).port or 8080)
    server = HTTPServer(('localhost', port), OAuthCallbackHandler)
    server.auth_code = None
    
    print(f"Waiting for authorization callback on {REDIRECT_URI}...")
    server.handle_request()  # Handle one request (the callback)
    
    if server.auth_code:
        print("\n✓ Authorization code received")
        
        # Step 3: Exchange code for tokens
        print("Exchanging code for access token...")
        tokens = exchange_code_for_tokens(server.auth_code)
        
        if tokens:
            print("✓ Tokens obtained successfully")
            
            # Step 4: Save tokens
            save_tokens_to_env(
                tokens['access_token'],
                tokens['refresh_token']
            )
            
            print("\n🎉 Authentication complete!")
            print("\nYou can now use oura_fetch_data.py to retrieve your health data.")
        else:
            print("\n❌ Failed to obtain tokens")
    else:
        print("\n❌ Authorization failed")

if __name__ == '__main__':
    main()
def get_oura_data():
    """
    Fetch today's health data from Oura API
    Returns a dictionary with key health metrics
    """
    import os
    from datetime import datetime, timedelta
    import requests
    from dotenv import load_dotenv
    import streamlit as st  # ADD THIS LINE
    
    # Load environment variables from .env
    load_dotenv()
    
    # CHANGE THIS LINE:
    access_token = st.secrets.get('OURA_ACCESS_TOKEN', os.getenv('OURA_ACCESS_TOKEN'))
    if not access_token:
        raise ValueError("OURA_ACCESS_TOKEN not found in .env file. Please run authentication first.")
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    # Get date range (last 2 days to ensure we get data)
    today = datetime.now().date()
    two_days_ago = today - timedelta(days=2)
    
    # Initialize result dictionary
    result = {
        'sleep_score': 'N/A',
        'readiness_score': 'N/A',
        'activity_score': 'N/A',
        'heart_rate': 'N/A',
        'hrv': 'N/A',
        'temperature': 'N/A',
        'total_sleep': 'N/A'
    }
    
    try:
        # Fetch daily sleep data
        sleep_url = f'https://api.ouraring.com/v2/usercollection/daily_sleep?start_date={two_days_ago}&end_date={today}'
        sleep_response = requests.get(sleep_url, headers=headers)
        if sleep_response.status_code == 200:
            sleep_data = sleep_response.json()
            if sleep_data.get('data') and len(sleep_data['data']) > 0:
                latest_sleep = sleep_data['data'][-1]  # Get most recent
                result['sleep_score'] = latest_sleep.get('score', 'N/A')
                
                # Get total sleep duration
                total_sleep_seconds = latest_sleep.get('total_sleep_duration', 0)
                if total_sleep_seconds and total_sleep_seconds > 0:
                    result['total_sleep'] = round(total_sleep_seconds / 3600, 1)
                
                # Get average heart rate from sleep
                avg_hr = latest_sleep.get('average_heart_rate')
                if avg_hr:
                    result['heart_rate'] = round(avg_hr)
                
                # Get HRV from sleep data
                hrv_avg = latest_sleep.get('average_hrv')
                if hrv_avg:
                    result['hrv'] = round(hrv_avg)
        
        # Fetch daily readiness data
        readiness_url = f'https://api.ouraring.com/v2/usercollection/daily_readiness?start_date={two_days_ago}&end_date={today}'
        readiness_response = requests.get(readiness_url, headers=headers)
        if readiness_response.status_code == 200:
            readiness_data = readiness_response.json()
            if readiness_data.get('data') and len(readiness_data['data']) > 0:
                latest_readiness = readiness_data['data'][-1]
                result['readiness_score'] = latest_readiness.get('score', 'N/A')
                
                # Get temperature deviation
                temp_deviation = latest_readiness.get('temperature_deviation')
                if temp_deviation is not None:
                    result['temperature'] = f"{temp_deviation:+.2f}"
        
        # Fetch daily activity data
        activity_url = f'https://api.ouraring.com/v2/usercollection/daily_activity?start_date={two_days_ago}&end_date={today}'
        activity_response = requests.get(activity_url, headers=headers)
        if activity_response.status_code == 200:
            activity_data = activity_response.json()
            if activity_data.get('data') and len(activity_data['data']) > 0:
                latest_activity = activity_data['data'][-1]
                result['activity_score'] = latest_activity.get('score', 'N/A')
                
                # Override heart rate with activity data if available
                avg_hr_activity = latest_activity.get('average_met_minutes')
                if not result['heart_rate'] or result['heart_rate'] == 'N/A':
                    low_hr = latest_activity.get('low_activity_met_minutes')
                    if low_hr:
                        result['heart_rate'] = 'Activity tracked'
        
        # Fetch heart rate data for more accurate HR
        heart_rate_url = f'https://api.ouraring.com/v2/usercollection/heartrate?start_datetime={two_days_ago}T00:00:00&end_datetime={today}T23:59:59'
        hr_response = requests.get(heart_rate_url, headers=headers)
        if hr_response.status_code == 200:
            hr_data = hr_response.json()
            if hr_data.get('data') and len(hr_data['data']) > 0:
                # Get most recent heart rate
                recent_hr = hr_data['data'][-1].get('bpm')
                if recent_hr:
                    result['heart_rate'] = round(recent_hr)
        
        return result
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Oura data: {e}")
        return result
    except Exception as e:
        print(f"Unexpected error: {e}")
        return result

