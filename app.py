import os
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# --- Routes ---

@app.route('/')
def index():
    # यह आपकी मुख्य फाइल (index.html) को लोड करेगा
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    roll_no = request.form.get('roll_no')
    if roll_no:
        # BTEUP रिजल्ट का असली लिंक फॉर्मेट
        result_url = f"https://result.bteupexam.in/Odd_Semester/main/result.aspx?roll_no={roll_no}"
        return redirect(result_url)
    return redirect('/')

# --- Render Deployment के लिए सबसे ज़रूरी हिस्सा ---

if __name__ == "__main__":
    # Render को 'PORT' एनवायरनमेंट वेरिएबल की ज़रूरत होती है
    port = int(os.environ.get("PORT", 5000))
    # host='0.0.0.0' इसे बाहरी दुनिया के लिए उपलब्ध कराता है
    app.run(host='0.0.0.0', port=port)

