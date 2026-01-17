#Smart Blog Smart social feed powered by AI.

Project Name: Smart Blog: a Safe and Smart Blogging Site that is AI-powered.  

Author: Ayman Rehman  

Institution: IU International University of Applied Sciences.  

Phase: 2 - Development/ Reflection Phase.  

Project Vision and Purpose  
The Smart Blog is an operational web application that is aimed at providing the user with a smart and safe blogging experience. I incorporated generative AI because this way, people will be able to write quality posts and the system will ensure that everything is safe by screening unsafe or sensitive posts. This project has brought me upon a crude concept to code that actually works and takes care of all aspects of creating a new content till the point of verifying, storing, and allowing people to play with it.  

Design and Architecture Technical.  
The application is designed to be decoupled and modular architecture to enable it to scale and maintain the code clean.  

Frontend (UI/UX)  

Technologies: Vanilla JavaScript, CSS3, and HTML5.  

Responsiveness: This was done by CSS media queries and a flexible layout to ensure the site is attractive on desktops, tablets, and smartphones.  

SPA Logic: I used a Single-Page application-style in order to enable its users to alternate the Feed and Create options without the need to reload the page, which is much more native.  

Backend (Logic & API)  

Affirmation: Pythons of Flask together with Blueprints, which decouple AI, Posts, and Moderation issues.  

AI Integration: I connected it to Google Gemini (gemma-3-1b-it) to create content and determine whether something is unsafe.  

Database: SQLite serves as a storage of all the posts, comments, likes, and moderation reports.  

Core Features  

Markdown Writer: Parses the user input and produces well-formatted JSON, which contains titles, content, categories, and hashtags.  

AI Checker: It is a required layer of safety which will scan all posts prior to hitting the database in order to cross discover a sensitive content.  

Community Moderation: The users can report posts, and when a post receives three reports, it automatically becomes flagged to be reviewed.  

Admin Moderation: The admin checks posts that have been flagged and determines which post is to be maintained or deleted.  

Engagement Tracking: I follow the number of distinct IPs reading a post, and allow the users to like the posts or talk about the news using the commenting section.  

Installation and Setup  

These are important steps to follow to ensure that the software works as required.  

Prerequisites  
Python 3.8+  
pip or Python Package Installer (Python) is a command-line utility that helps install and manage Python packages.<|human|>pip Python Package Installer pip Python Package Installer (Python) is a command used to install and manage Python packages.  

Installation Steps  

De-packaged Items: A project folder has been zip-unzipped.  

Install Dependencies: To install all the necessary libraries, one runs the following:  

Bash  
# Install the exact versions used during development
pip install -r requirements.txt
Environment Configuration:  

Harvest indegenous file called.env in the root which stores credentials.  

Put in your Gemini API Key GEMINIAPIKEY="yourrealkeyhere".  

I included one so that you can use it to test the API locally.  

Execution Instructions  

Starting Database: There is no need to prepare the Database as the app automatically creates blog.db and the required tables.  

Initialization of the Server: Execute the basic file:  

Bash  
python app.py  

Apply Access. The browser will open to the URL127.0.0.1:5000.  

Testing Outcomes  

Input Validation: The backend has validated HTML getting rid of XSS without loss of basic formatting.  

Profanity Filter: All posts and comments containing blacklisted words (via Config), receive a 400 Bad Request.  

Spam Prevention: This is a cookie-based system that prevents an individual user to report the same post in less than 30 days.
