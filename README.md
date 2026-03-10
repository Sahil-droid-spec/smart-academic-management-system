# Smart Academic Management System

A Flask web application for managing student grades, attendance, notices, and an AI academic advisor chatbot.

## Features
- **Student Dashboard** – View grades, CGPA, attendance, and notices
- **Faculty Dashboard** – Manage courses, update grades and attendance
- **Dean Dashboard** – College-wide analytics, student overview, notice management
- **AI Chatbot** – Academic advisor powered by Groq (with offline fallback)

## Default Login Credentials (for testing)

| Role    | Username  | Password     |
|---------|-----------|--------------|
| Dean    | dean      | dean123      |
| Faculty | faculty1  | faculty123   |
| Faculty | faculty2  | faculty123   |
| Student | student1  | student123   |
| Student | student2  | student123   |

## Setup & Run

### 1. Clone the repository
```bash
git clone https://github.com/Sahil-droid-spec/SAS_FINAL.git
cd SAS_FINAL
```

### 2. Create a virtual environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set environment variables (optional)
Create a `.env` file (copy from `.env.example`):
```
SECRET_KEY=your-secret-key
GROQ_API_KEY=your-groq-api-key   # Get free key at console.groq.com
```

### 5. Run the app
```bash
python app.py
```

Open your browser and go to: **http://127.0.0.1:5000**

> The database (`instance/sas.db`) is created automatically on first run with seed data.

## Tech Stack
- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login
- **Database:** SQLite
- **AI:** Groq API (llama3-8b-8192) with keyword-based offline fallback
- **Frontend:** HTML, CSS, JavaScript
