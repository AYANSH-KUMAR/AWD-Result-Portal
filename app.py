import os
import time
import base64
import sqlite3
import logging
import requests
from functools import wraps
from collections import defaultdict
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, redirect

app = Flask(__name__)

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# --- In-Memory Rate Limiter ---
request_counts = defaultdict(list)
RATE_LIMIT_PER_MIN = 10

def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr
        now = time.time()
        request_counts[ip] = [t for t in request_counts[ip] if now - t < 60]
        if len(request_counts[ip]) >= RATE_LIMIT_PER_MIN:
            return "Too many requests! Please wait a minute.", 429
        request_counts[ip].append(now)
        return f(*args, **kwargs)
    return decorated

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('bteup_pro.db')
    conn.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, html TEXT, fetched_at INTEGER)')
    conn.commit()
    conn.close()

init_db()

def to_base64(text):
    return base64.b64encode(text.encode()).decode()

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
@rate_limit
def generate():
    enroll = request.form.get('enrollment', '').strip()
    dob = request.form.get('dob', '').strip()
    exam_type = request.form.get('exam_type', 'Odd_Semester')

    if not enroll or not dob:
        return "Enrollment and DOB are required!", 400

    # BTEUP Result logic with Base64 encoding
    # Note: BTEUP links change often. This uses your provided logic.
    enc_id = to_base64(enroll)
    enc_id2 = to_base64(dob)
    
    # Try different URL structures if one fails
    target_url = f"https://result.bteexam.com/{exam_type}/main/result.aspx?id={enc_id}&id2={enc_id2}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        logger.info(f"Fetching result for {enroll}...")
        response = requests.get(target_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Finding the result table
            result_table = soup.find('table')
            if result_table:
                return render_template('result.html', table_html=str(result_table), enroll=enroll)
            else:
                return "<h2>Result Table Not Found. Check your details or BTEUP Server.</h2>", 404
        else:
            # Fallback to direct redirect if scraping fails
            return redirect(target_url)

    except Exception as e:
        logger.error(f"Error: {e}")
        # Last resort: Direct Redirect
        return redirect(target_url)

# --- Render Deployment Settings ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
