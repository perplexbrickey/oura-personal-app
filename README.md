# Oura Personal Dashboard

Personal wellness data tracker for analyzing Oura Ring health metrics and integrating with personal productivity systems.

## Overview

This project provides a secure way to access and analyze your personal Oura Ring data through the Oura API. All credentials and health data remain local on your machine - this repository only contains code templates and public-facing documentation.

## What's Included

- **Privacy Policy & Terms of Service**: Public documentation required for Oura API access
- **Python Scripts**: Template code for OAuth authentication and data retrieval (coming soon)
- **Setup Guide**: Instructions for safely configuring your local environment

## Security Note

🔒 **Your data is private**: This repository is configured to keep your API credentials, tokens, and personal health data LOCAL ONLY. The `.gitignore` file ensures sensitive information never gets committed to GitHub.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Oura Ring and account
- Your Oura API credentials (from the [Oura Developer Portal](https://developer.ouraring.com))

### Setup

1. Clone this repository
2. Create a `.env` file in the project root (never commit this!)
3. Add your Oura API credentials to the `.env` file:
   ```
   CLIENT_ID=your_client_id_here
   CLIENT_SECRET=your_client_secret_here
   ```
4. Follow the authentication flow to get your access token

## Project Structure

```
oura-personal-app/
├── index.html          # Landing page
├── privacy.html        # Privacy policy
├── terms.html          # Terms of service
├── .gitignore          # Protects sensitive files
└── README.md           # This file
```

## Privacy & Data

Your health data is personal and sensitive. This project:
- Keeps all credentials in local `.env` files (never committed)
- Stores downloaded data locally only
- Uses OAuth for secure API access
- Never shares your data with third parties

## Resources

- [Oura API Documentation](https://cloud.ouraring.com/v2/docs)
- [Oura Developer Portal](https://developer.ouraring.com)

## License

Personal use only.
