"""
Implementation Guide for Cache Configuration
Shows how to integrate caching into your Flask application
"""

# ================= STEP 1: Import the cache config =================
# Add this to the top of app.py:

from config.cache_config import (
    CacheConfig,
    cache_db_query,
    cache_api_response,
    invalidate_cache,
    set_cache_headers,
    get_redis_client,
    FileCache
)
from flask_caching import Cache

# ================= STEP 2: Initialize Flask-Caching =================
# Add after app = Flask(__name__):

app = Flask(__name__)
app.secret_key = "super-secret-key"

# Initialize caching
cache = Cache(app, config={
    'CACHE_TYPE': CacheConfig.FLASK_CACHE_TYPE,
    'CACHE_REDIS_HOST': CacheConfig.REDIS_HOST,
    'CACHE_REDIS_PORT': CacheConfig.REDIS_PORT,
    'CACHE_REDIS_DB': CacheConfig.REDIS_DB,
    'CACHE_REDIS_PASSWORD': CacheConfig.REDIS_PASSWORD,
    'CACHE_DEFAULT_TIMEOUT': CacheConfig.FLASK_CACHE_DEFAULT_TIMEOUT,
    'CACHE_KEY_PREFIX': CacheConfig.FLASK_CACHE_KEY_PREFIX
})


# ================= STEP 3: Cache Database Queries =================
# Example 1: Cache student attendance data

@app.route('/student-dashboard/<uid>')
@cache.cached(timeout=CacheConfig.STUDENT_ATTENDANCE_CACHE)
def student_dashboard(uid):
    """Dashboard is cached for 5 minutes"""
    conn = get_db_connection()
    
    student = conn.execute(
        "SELECT * FROM students WHERE uid=?",
        (uid,)
    ).fetchone()
    
    attendance_rows = conn.execute("""
    SELECT
        subject,
        COUNT(*) AS total_classes,
        SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS attended_classes
    FROM daily_attendance
    WHERE student_uid=?
    GROUP BY subject
    """, (uid,)).fetchall()
    
    conn.close()
    
    # ... rest of the code ...
    
    return render_template('student_dashboard.html', ...)


# Example 2: Cache admin dashboard stats
@app.route('/admin-dashboard')
@cache.cached(timeout=CacheConfig.CLASS_STATS_CACHE)
def admin_dashboard():
    """Admin dashboard cached for 10 minutes"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    total_students = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]
    
    total_teachers = conn.execute(
        "SELECT COUNT(*) FROM teachers"
    ).fetchone()[0]
    
    total_records = conn.execute(
        "SELECT COUNT(*) FROM daily_attendance"
    ).fetchone()[0]
    
    conn.close()
    
    return render_template(
        'admin_dashboard.html',
        total_students=total_students,
        total_teachers=total_teachers,
        total_records=total_records
    )


# ================= STEP 4: Cache External API Calls =================
# Cache Gemini API responses

@app.route("/ai-chat", methods=["POST"])
@cache_api_response(timeout=CacheConfig.GEMINI_API_CACHE)
def ai_chat():
    """Gemini API responses cached for 7 days"""
    data = request.get_json()
    user_message = data.get("message", "").lower()
    uid = data.get("uid")
    
    # ... attendance logic ...
    
    # Fallback to Gemini API (cached)
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message
        )
        return jsonify({"reply": response.text})
    except:
        return jsonify({"reply": "AI service unavailable"})


# ================= STEP 5: Cache with Custom Decorator =================
# Using the custom @cache_db_query decorator

@cache_db_query(cache_type='query', timeout=CacheConfig.ALL_STUDENTS_CACHE)
def get_all_students():
    """Cached for 30 minutes"""
    conn = get_db_connection()
    students = conn.execute("SELECT uid, name, email FROM students").fetchall()
    conn.close()
    return [dict(s) for s in students]


# ================= STEP 6: Invalidate Cache on Updates =================
# Clear cache when attendance is marked

@app.route('/teacher/mark-attendance', methods=['GET', 'POST'])
def mark_attendance():
    if 'teacher_logged_in' not in session:
        return redirect(url_for('teacher_login'))
    
    conn = get_db_connection()
    
    # ... existing code ...
    
    if request.method == 'POST':
        # ... mark attendance logic ...
        
        conn.commit()
        conn.close()
        
        # 🔥 INVALIDATE CACHE
        cache.clear()  # Option 1: Clear all cache
        
        # OR Option 2: Selective invalidation
        invalidate_cache('attendance_marked', get_redis_client())
        
        # OR Option 3: Clear specific cached items
        cache.delete_memoized('admin_dashboard')
        cache.delete_memoized('student_dashboard')
        
        return redirect(url_for('teacher_dashboard'))
    
    # ... rest of code ...


# ================= STEP 7: Invalidate on Add/Delete =================

@app.route('/admin/add-student', methods=['GET', 'POST'])
def admin_add_student():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        uid = request.form['uid']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO students (uid, name, email, password) VALUES (?, ?, ?, ?)",
            (uid, name, email, password)
        )
        conn.commit()
        conn.close()
        
        # 🔥 INVALIDATE CACHE - New student added
        invalidate_cache('student_added', get_redis_client())
        
        return redirect(url_for('admin_students'))
    
    return render_template('admin_add_student.html')


@app.route('/admin/delete-student/<uid>')
def admin_delete_student(uid):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    conn.execute("DELETE FROM students WHERE uid=?", (uid,))
    conn.commit()
    conn.close()
    
    # 🔥 INVALIDATE CACHE - Student deleted
    invalidate_cache('student_deleted', get_redis_client())
    
    return redirect(url_for('admin_students'))


# ================= STEP 8: Set Cache Headers for Responses =================

@app.route('/download-report/<uid>')
def download_report(uid):
    """PDF reports cached in browser for 24 hours"""
    conn = get_db_connection()
    
    # ... PDF generation code ...
    
    response = make_response(send_file(buffer, ...))
    
    # 🔥 Set cache headers
    response = set_cache_headers(response, cache_type='report')
    
    return response


@app.route('/attendance/<uid>')
def student_attendance(uid):
    """Attendance page cached for 30 minutes"""
    # ... attendance logic ...
    
    response = make_response(render_template('student_attendance.html', ...))
    
    # 🔥 Set cache headers
    response = set_cache_headers(response, cache_type='dashboard')
    
    return response


# ================= STEP 9: Cache Face Recognition Data =================

def load_faces():
    """Load and cache face encodings"""
    face_path = os.path.join(BASE_DIR, "faces")
    
    if not os.path.exists(face_path):
        os.makedirs(face_path)
    
    # Try to load from cache first
    cache_key = "face_encodings_all"
    cached_faces = FileCache.get('face', cache_key, CacheConfig.FACE_ENCODINGS_CACHE)
    
    if cached_faces:
        print("✅ Loaded face encodings from cache")
        return cached_faces['faces'], cached_faces['ids']
    
    # Load from disk if cache expired
    KNOWN_FACES = []
    KNOWN_IDS = []
    
    for file in os.listdir(face_path):
        img_path = os.path.join(face_path, file)
        
        img = face_recognition.load_image_file(img_path)
        enc = face_recognition.face_encodings(img)
        
        if len(enc) > 0:
            KNOWN_FACES.append(enc[0])
            KNOWN_IDS.append(file.split('.')[0])
    
    # Cache the encodings
    FileCache.set('face', cache_key, {
        'faces': KNOWN_FACES,
        'ids': KNOWN_IDS
    }, CacheConfig.FACE_ENCODINGS_CACHE)
    
    print(f"✅ Cached {len(KNOWN_FACES)} face encodings")
    return KNOWN_FACES, KNOWN_IDS


# ================= STEP 10: Cache Performance Monitoring =================

@app.route('/admin/cache-stats')
def cache_stats():
    """View cache statistics"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    redis_client = get_redis_client()
    
    if redis_client:
        info = redis_client.info('stats')
        total_commands = info.get('total_commands_processed', 0)
        
        return jsonify({
            'status': 'Redis Connected',
            'total_commands': total_commands,
            'memory_usage': info.get('used_memory_human', 'N/A')
        })
    else:
        return jsonify({
            'status': 'Using File-Based Cache',
            'cache_dir': CacheConfig.CACHE_DIR
        })


# ================= ENVIRONMENT VARIABLES (.env) =================
# Add these to your .env file:

"""
# Cache Configuration
CACHE_TYPE=redis  # or 'simple' for development
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password_here

# API Keys
GEMINI_API_KEY=your_gemini_key
MAIL_PASSWORD=your_email_password
"""


# ================= INSTALL REQUIRED PACKAGES =================
# Add to requirements.txt:

"""
flask-caching==2.1.0
redis==5.0.0
"""

# Then install:
# pip install -r requirements.txt
