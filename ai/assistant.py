import requests

SYSTEM_PROMPT = """You are SAS Assistant, an academic advisor for college students in India.
Help with: grades, CGPA, attendance, study strategies, placement prep, internships, stress management.
Keep responses concise and practical. Use bullet points for steps. Be encouraging but realistic.
Do not use emojis. Speak professionally."""


def get_ai_response(messages: list, api_key: str, model: str) -> str:
    if not api_key:
        return _fallback(messages[-1]['content'] if messages else '')

    try:
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': model,
                'messages': [{'role': 'system', 'content': SYSTEM_PROMPT}] + messages,
                'max_tokens': 512,
                'temperature': 0.7
            },
            timeout=15
        )
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Could not reach AI service. Using offline mode.\n\n{_fallback(messages[-1]['content'] if messages else '')}"


def _fallback(msg: str) -> str:
    msg = msg.lower()

    if any(w in msg for w in ['attendance', 'absent', 'bunk']):
        return (
            "**Attendance Guidelines**\n\n"
            "- Minimum 75% attendance is required for exam eligibility.\n"
            "- If below 75%, submit a medical certificate or leave letter to the Dean's office.\n"
            "- Plan leaves in advance and use the 25% buffer carefully.\n"
            "- Speak to your faculty if you've missed classes due to health issues.\n\n"
            "_To enable full AI responses, add a free Groq API key in config.py_"
        )

    if any(w in msg for w in ['cgpa', 'grade', 'marks', 'score', 'fail', 'backlog']):
        return (
            "**Grade & CGPA Guidance**\n\n"
            "- CGPA = Sum of (Grade Points × Credits) / Total Credits\n"
            "- Focus on high-credit subjects — they affect CGPA more.\n"
            "- For backlogs, clear older subjects first.\n"
            "- Aim for at least 7.5 CGPA for most campus placements.\n"
            "- Internal marks (30%) are easier to score — never miss assignments.\n\n"
            "_To enable full AI responses, add a free Groq API key in config.py_"
        )

    if any(w in msg for w in ['placement', 'job', 'intern', 'company', 'interview', 'campus']):
        return (
            "**Placement Preparation Roadmap**\n\n"
            "- DSA: Solve LeetCode Top 150 problems (Easy to Medium first)\n"
            "- Core CS: OS, DBMS, Networks, OOP — these are asked in every interview\n"
            "- Projects: One well-documented GitHub project is better than ten incomplete ones\n"
            "- CGPA: Most companies shortlist at 6.0 to 7.5 minimum\n"
            "- Start preparation at least 6 months before placement season\n\n"
            "_To enable full AI responses, add a free Groq API key in config.py_"
        )

    if any(w in msg for w in ['study', 'exam', 'prepare', 'schedule', 'tips']):
        return (
            "**Study Strategy**\n\n"
            "- Use the Pomodoro technique: 25 minutes study, 5 minutes break\n"
            "- Study the hardest subject first when your mind is fresh\n"
            "- Make short notes and mind maps for quick revision\n"
            "- Solve previous year question papers — most important step\n"
            "- Get 7 to 8 hours of sleep — memory consolidates during sleep\n\n"
            "_To enable full AI responses, add a free Groq API key in config.py_"
        )

    if any(w in msg for w in ['stress', 'anxious', 'worried', 'tired', 'overwhelm', 'burnout']):
        return (
            "**Managing Academic Stress**\n\n"
            "It is normal to feel overwhelmed during exams. Here is what helps:\n\n"
            "- Break large tasks into small daily goals — small wins build momentum\n"
            "- Take real breaks: go for a walk, talk to a friend\n"
            "- Avoid comparing your progress to others\n"
            "- Speak to your faculty advisor or the college counsellor\n"
            "- The Dean's office has a student support cell for academic concerns\n\n"
            "Every student has difficult semesters. You will get through this."
        )

    if any(w in msg for w in ['ml', 'machine learning', 'dsa', 'leetcode', 'python', 'algorithm']):
        return (
            "**CSE Learning Path**\n\n"
            "For Machine Learning:\n"
            "- Andrew Ng's ML Course on Coursera, then hands-on with scikit-learn, then Kaggle\n"
            "- Focus on: regression, classification, clustering\n\n"
            "For DSA and Placements:\n"
            "- Arrays, Strings, Linked Lists, Trees, Graphs, Dynamic Programming\n"
            "- LeetCode Top 150 is the standard preparation list\n"
            "- Aim for 2 to 3 problems per day consistently\n\n"
            "_To enable full AI responses, add a free Groq API key in config.py_"
        )

    return (
        "**Hello, I am the SAS Academic Advisor.**\n\n"
        "I can help you with:\n"
        "- Understanding your grades and CGPA\n"
        "- Attendance management\n"
        "- Study plans and exam preparation\n"
        "- Placement and internship guidance\n"
        "- Managing academic stress\n\n"
        "What would you like help with today?\n\n"
        "_Add a free Groq API key in config.py to enable full AI-powered conversations._"
    )
