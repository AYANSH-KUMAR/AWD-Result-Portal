from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import base64
import sqlite3

app = Flask(__name__)

# --- Database Setup (Cache Layer) ---
def init_db():
    conn = sqlite3.connect('bteup_universal.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, html TEXT)')
    conn.commit()
    conn.close()

# सर्वर शुरू होते ही डेटाबेस चेक करेगा
init_db()

# --- Helper: Base64 Encoding ---
def to_base64(text):
    return base64.b64encode(text.encode()).decode()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    enroll = request.form.get('enrollment', '').strip()
    dob = request.form.get('dob', '').strip()
    exam_type = request.form.get('exam_type', 'Odd_Semester') # Dropdown value
    
    if not enroll or not dob:
        return "<h3>Enrollment and DOB are required!</h3>"

    cache_key = f"{enroll}_{dob}_{exam_type}"

    # 1. Caching Check (Fast Response)
    try:
        conn = sqlite3.connect('bteup_universal.db')
        cursor = conn.cursor()
        cursor.execute("SELECT html FROM cache WHERE key=?", (cache_key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return render_template('result.html', table_html=row[0], enroll=enroll, source="⚡ Fast Cache")
    except Exception as e:
        print(f"Cache Error: {e}")

    # 2. BTEUP URL Construction
    enc_id = to_base64(enroll)
    enc_id2 = to_base64(dob)
    # Dynamic URL: Odd_Semester, Even_Semester, or Back_Paper
    target_url = f"https://result.bteexam.com/{exam_type}/main/result.aspx?id={enc_id}&id2={enc_id2}"

    # 3. Request to BTEUP Server
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        }
        response = requests.get(target_url, headers=headers, timeout=25)
        
        if response.status_code != 200:
            return f"<h3>BTEUP Server Error: {response.status_code}</h3>"

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Result Table Scraping
        # BTEUP results are usually inside a <table>
        result_table = soup.find('table') 

        if result_table:
            html_content = str(result_table)
            
            # 4. Save to Cache for next time
            conn = sqlite3.connect('bteup_universal.db')
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO cache VALUES (?, ?)", (cache_key, html_content))
            conn.commit()
            conn.close()

            return render_template('result.html', table_html=html_content, enroll=enroll, source="📡 Live BTEUP Server")
        else:
            return "<h2 style='text-align:center; color:red; margin-top:50px;'>Result Not Found!<br>Check your Enrollment, DOB and Exam Type.</h2>"

    except Exception as e:
        return f"<h2 style='color:red;'>Connection Failed: {str(e)}</h2>"

if __name__ == '__main__':
    # Termux के लिए host 0.0.0.0 ताकि लोकल नेटवर्क पर चले
    app.run(host='0.0.0.0', port=8080, debug=True)
