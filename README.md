 🤖 Smart Blog – AI-Powered Blogging Platform

> University Project : DLBCSPJWD01 – Project Java and Web Development
> Author: Ayman Rehman
> Institution: IU International University of Applied Sciences

---

 📖 Project Overview

Smart Blog is a secure, intelligent web application designed to modernize the blogging experience. By integrating Generative AI (Google Gemini), the platform not only assists users in writing high-quality content but also acts as an automated moderator, scanning every post for safety before it goes live.

This project represents the transition from a conceptual design to a fully functional software product, featuring a responsive frontend, a modular Flask backend, and a robust SQLite database.

---

 🚀 Key Features

 🧠 AI-Powered Core
- AI Writer: Generates structured blog drafts (Title, Content, Hashtags, Category) from simple user prompts.
- AI Safety Checker: A mandatory security layer that scans all content for hate speech, harassment, or sensitive topics before saving to the database.

 🛡️ Moderation System
- Community Flagging: Users can report inappropriate content.
- Auto-Flag Logic: If a post receives 3 unique reports, it is automatically flagged for review.
- Admin Dashboard: A dedicated interface for admins to review flagged posts, delete content, or ban abusive IPs.

 ⚡ User Experience
- Responsive Design: Fully optimized for Mobile, Tablet, and Desktop using CSS Media Queries.
- Engagement: Unique view tracking (per IP), likes, and commenting system.
- SPA Feel: Seamless navigation between the Feed and Creation tools without full page reloads.

---

 🛠️ Technical Architecture

The application follows a modular architecture using Flask Blueprints to separate concerns (AI logic, Post routes, Admin routes).

| Component | Technology Stack |
| :--- | :--- |
| Frontend | HTML5, CSS3, Vanilla JavaScript (ES6+) |
| Backend | Python 3, Flask, Werkzeug |
| AI Engine | Google Gemini API (`gemma-3-1b-it` model) |
| Database | SQLite (File-based, zero-config) |
| Security | Flask-Bcrypt, Dotenv, IP-based Rate Limiting |

---

 ⚙️ Installation & Setup Guide

Follow these steps to set up the project locally.

 1️⃣ Prerequisites
* Python 3.8 or higher installed.
* pip (Python Package Installer).

 2️⃣ Clone & Unzip
Extract the project folder to your desired location and open a terminal inside that folder.

bash
cd path/to/smart-blog


---
3️⃣ Create a Virtual Environment (Recommended)
It is best practice to use a virtual environment to manage dependencies so they don't conflict with other Python projects.

Windows:
python -m venv venv
venv\Scripts\activate


Mac/Linux:
python3 -m venv venv
source venv/bin/activate
---

4️⃣ Install Dependencies
Install all required libraries using the provided requirements.txt file.

Bash
pip install -r requirements.txt

5️⃣ Environment Configuration
Locate the .env file in the root directory.

Open it and add your Google Gemini API key:

Code snippet

GEMINI_API_KEY="your_actual_api_key_here"
I have added my env file with my key, and that can be used

1. Initialize the Server
You don't need to create the database manually; the app will automatically generate blog.db for the first run.

Bash

python app.py
2. Access the App
Open your web browser and navigate to: 👉 https://www.google.com/search?q=
http://127.0.0.1:5000


Test Scenario, Outcome, Status
Input Validation, Backend sanitizes HTML input to prevent XSS attacks while preserving basic formatting.✅ Passed
Profanity Filter, Posts/Comments with blacklisted words return a 400 Bad Request error.✅ Passed
Spam Prevention: Cookie-based logic prevents a user from reporting the same post twice within 30 days.✅ Passed
AI Safety, "The /api/check endpoint successfully blocks prompts categorized as "HATE_SPEECH" or "HARASSMENT"."✅ Passed


/smart-blog
├── /static              CSS, JS,
├── /templates           HTML files
├── /routes              Flask Blueprints (ai_bp.py, posts_bp.py, etc.)
├── app.py               Main entry point
├── models.py            Database Schema (SQLAlchemy)
├── requirements.txt     Dependency list
├── .env                 API Keys & Config
└── README.md            Documentation

