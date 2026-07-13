from flask import Flask, render_template_string, request, jsonify
import requests
import time
import random
import threading
import string
import os

app = Flask(__name__)

# एक्टिव टास्क्स को ट्रैक करने के लिए डिक्शनरी
active_tasks = {}
DB_FILE = "processed_posts.txt"

def load_processed_posts():
    """परमानेंट फ़ाइल से पुरानी प्रोसेस्ड पोस्ट्स की लिस्ट लोड करना"""
    if not os.path.exists(DB_FILE):
        return set()
    with open(DB_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_post(post_id):
    """नई प्रोसेस्ड पोस्ट को परमानेंट फ़ाइल में सेव करना"""
    with open(DB_FILE, "a") as f:
        f.write(f"{post_id}\n")

def generate_task_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def add_reaction(post_id, token):
    url = f"https://graph.facebook.com/{post_id}/reactions"
    payload = {'access_token': token, 'type': 'LIKE'}
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass

def post_comment(post_id, message, token):
    url = f"https://graph.facebook.com/{post_id}/comments"
    payload = {'access_token': token, 'message': message}
    try:
        return requests.post(url, data=payload, timeout=5).json()
    except:
        return {}

def bot_worker(task_id, token, target_uids, comments_pool):
    processed_posts = load_processed_posts()
    print(f"[Task {task_id}] 🚀 2-कमेंट स्पेशल बॉट शुरू! पुरानी पोस्ट्स इग्नोर की जाएंगी।")
    
    while active_tasks.get(task_id, False):
        processed_posts = load_processed_posts()
        
        for uid in target_uids:
            if not active_tasks.get(task_id, False):
                break
                
            url = f"https://graph.facebook.com/v20.0/{uid}/posts?access_token={token}&limit=1"
            try:
                data = requests.get(url, timeout=5).json()
                for post in data.get('data', []):
                    if not active_tasks.get(task_id, False):
                        break
                        
                    pid = post['id']
                    
                    # अगर पोस्ट पर पहले कमेंट हो चुका है, तो छोड़ दो
                    if pid in processed_posts:
                        continue
                        
                    print(f"[Task {task_id}] 🔥 एकदम नई पोस्ट मिली: {pid} (इस पर 2 कमेंट्स होंगे)")
                    
                    # 1. पहले रिएक्शन दें
                    add_reaction(pid, token)
                    time.sleep(2)
                    
                    # 2. पहला कमेंट करें
                    comment_1 = random.choice(comments_pool)
                    res1 = post_comment(pid, comment_1, token)
                    if 'id' in res1:
                        print(f"[Task {task_id}] ✅ पहला कमेंट सफल: {comment_1}")
                    else:
                        print(f"[Task {task_id}] ⚠️ पहला कमेंट फेल: {res1}")
                    
                    # पहले और दूसरे कमेंट के बीच 15 से 30 सेकंड का गैप (ताकि फेसबुक स्पैम न समझे)
                    time.sleep(random.randint(15, 30))
                    
                    # 3. दूसरा कमेंट करें (कोशिश करेंगे कि पहला और दूसरा कमेंट अलग हो)
                    remaining_comments = [c for c in comments_pool if c != comment_1]
                    comment_2 = random.choice(remaining_comments) if remaining_comments else comment_1
                    
                    res2 = post_comment(pid, comment_2, token)
                    if 'id' in res2:
                        print(f"[Task {task_id}] ✅ दूसरा कमेंट भी सफल: {comment_2}")
                    else:
                        print(f"[Task {task_id}] ⚠️ दूसरा कमेंट फेल: {res2}")
                    
                    # दोनों कमेंट होने के बाद पोस्ट को मेमोरी में सेव करें ताकि दोबारा इस पर कमेंट न हो
                    processed_posts.add(pid)
                    save_processed_post(pid)
                    
                    # अगली पोस्ट पर जाने से पहले सेफ गैप
                    time.sleep(random.randint(5, 8))
            except Exception as e:
                print(f"[Task {task_id}] एरर (UID {uid}): {e}")
            
            time.sleep(2)
        
        # 'Just Now' चेकिंग के लिए 20 से 40 सेकंड का गैप
        sleep_time = random.randint(20, 40)
        print(f"[Task {task_id}] 🕒 {sleep_time} सेकंड बाद नई पोस्ट्स के लिए दोबारा स्कैन होगा...")
        for _ in range(sleep_time):
            if not active_tasks.get(task_id, False):
                break
            time.sleep(1)
            
    print(f"[Task {task_id}] 🛑 बॉट पूरी तरह से रुक गया है।")

# HTML इंटरफ़ेस (बस इसमें "Bot powered by Munna Mehar" जोड़ा गया है)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ Double Comment FB Bot</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 600px; background: white; padding: 20px; margin: auto; box-shadow: 0px 0px 10px rgba(0,0,0,0.1); border-radius: 8px; }
        h2, h3 { color: #333; text-align: center; margin-top: 5px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; color: #444; }
        input[type="text"], textarea, input[type="file"] { width: 100%; padding: 10px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; background: #fff; }
        .info-text { font-size: 12px; color: #666; margin-top: 2px; }
        button { width: 100%; padding: 12px; background-color: #ffc107; color: #333; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; font-weight: bold; }
        button:hover { background-color: #e0a800; }
        button.stop-btn { background-color: #dc3545; color: white; margin-top: 10px; }
        button.stop-btn:hover { background-color: #bd2130; }
        .response { margin-top: 15px; padding: 10px; border-radius: 4px; display: none; text-align: center; font-weight: bold; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .footer { text-align: center; font-size: 14px; color: #888; margin-top: 20px; border-top: 1px solid #eee; padding-top: 10px; }
    </style>
</head>
<body>

<div class="container">
    <h2>⚡ Double Comment FB बॉट पैनल</h2>
    <p style="text-align: center; font-size: 13px; color: #555;">(हर नई पोस्ट पर लगातार 2 अलग-अलग कमेंट्स होंगे)</p>
    <hr>
    
    <form id="startForm" enctype="multipart/form-data">
        <div class="form-group">
            <label>Access Token:</label>
            <input type="text" name="access_token" placeholder="अपना फेसबुक टोकन यहाँ डालें" required>
        </div>
        
        <div class="form-group" style="background: #e9ecef; padding: 10px; border-radius: 5px;">
            <label style="color: #856404;">👥 Target IDs File (.txt Upload):</label>
            <input type="file" name="id_file" accept=".txt" required>
            <div class="info-text">नोट: आपके पुराने और नए दोस्तों की IDs वाली फ़ाइल।</div>
        </div>
        
        <div class="form-group">
            <label>Comments Pool (कम से कम 3-4 अलग कमेंट्स डालें):</label>
            <textarea name="comments" rows="5" placeholder="Awesome! 🔥&#10;बहुत बढ़िया भाई ❤️&#10;Love it ✨&#10;Op Bhai 👑" required></textarea>
        </div>
        
        <button type="submit">🚀 2x कमेंट बॉट चालू करें</button>
    </form>

    <hr style="margin: 25px 0;">

    <h3>🛑 बॉट बंद करें</h3>
    <form id="stopForm">
        <div class="form-group">
            <label>Task ID दर्ज करें:</label>
            <input type="text" name="task_id" placeholder="उदाहरण: AB12CD" required>
        </div>
        <button type="submit" class="stop-btn">बॉट स्टॉप करें</button>
    </form>

    <div id="resBox" class="response"></div>

    <!-- ✅ बस यह लाइन जोड़ी गई है -->
    <div class="footer">🤖 Bot powered by <strong>Munna Mehar</strong></div>
</div>

<script>
    const resBox = document.getElementById('resBox');

    function showMessage(msg, isSuccess) {
        resBox.innerText = msg;
        resBox.style.display = 'block';
        resBox.className = 'response ' + (isSuccess ? 'success' : 'error');
    }

    document.getElementById('startForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        showMessage("बॉट चालू हो रहा है...", true);
        
        const res = await fetch('/start', { method: 'POST', body: formData });
        const data = await res.json();
        showMessage(data.message, data.status === 'success');
        if(data.status === 'success') e.target.reset();
    });

    document.getElementById('stopForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const res = await fetch('/stop', { method: 'POST', body: formData });
        const data = await res.json();
        showMessage(data.message, data.status === 'success');
        if(data.status === 'success') e.target.reset();
    });
</script>

</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start', methods=['POST'])
def start_bot():
    token = request.form.get('access_token')
    comments_raw = request.form.get('comments')
    id_file = request.files.get('id_file')
    
    if not token or not comments_raw or not id_file:
        return jsonify({"status": "error", "message": "कृपया सभी फील्ड्स भरें!"})
    
    try:
        file_content = id_file.read().decode('utf-8')
        target_uids = [uid.strip() for uid in file_content.split('\n') if uid.strip()]
    except Exception as e:
        return jsonify({"status": "error", "message": f"फ़ाइल पढ़ने में एरर: {str(e)}"})
        
    if not target_uids:
        return jsonify({"status": "error", "message": "फ़ाइल खाली है!"})
        
    comments_pool = [comment.strip() for comment in comments_raw.split('\n') if comment.strip()]
    
    task_id = generate_task_id()
    active_tasks[task_id] = True
    
    t = threading.Thread(target=bot_worker, args=(task_id, token, target_uids, comments_pool))
    t.daemon = True
    t.start()
    
    return jsonify({
        "status": "success", 
        "message": f"🔥 बॉट चालू! हर पोस्ट पर 2 कमेंट्स होंगे। Task ID: {task_id}", 
        "task_id": task_id
    })

@app.route('/stop', methods=['POST'])
def stop_bot():
    task_id = request.form.get('task_id').strip().upper()
    
    if task_id in active_tasks and active_tasks[task_id]:
        active_tasks[task_id] = False
        return jsonify({"status": "success", "message": f"Task {task_id} को रोकने का सिग्नल भेज दिया गया।"})
    else:
        return jsonify({"status": "error", "message": "गलत Task ID या टास्क पहले से ही बंद है।"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
