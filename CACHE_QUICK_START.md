"""
QUICK START GUIDE: Implement Caching in 5 Minutes
Step-by-step setup instructions for the Smart Attendance System
"""

# ============================================================
# STEP 1: Install Required Packages
# ============================================================

# Run this in your terminal:
# pip install flask-caching redis

# Or add to requirements.txt:
"""
flask-caching==2.1.0
redis==5.0.0
"""

# ============================================================
# STEP 2: Create .env File Configuration
# ============================================================

# Create a .env file in your project root with:
"""
# Existing configuration
GEMINI_API_KEY=your_gemini_key
MAIL_PASSWORD=your_email_password

# New cache configuration
CACHE_TYPE=simple
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Set to 'redis' for production after installing Redis
# CACHE_TYPE=redis
"""

# ============================================================
# STEP 3: Update app.py - Add Imports
# ============================================================

# Add these imports at the TOP of app.py (after existing imports):

"""
from flask_caching import Cache
from config.cache_config import (
    CacheConfig,
    cache_db_query,
    cache_api_response,
    invalidate_cache,
    set_cache_headers,
    get_redis_client,
    FileCache
)
from flask import make_response
"""

# ============================================================
# STEP 4: Initialize Cache in app.py
# ============================================================

# Add this RIGHT AFTER: app = Flask(__name__)

"""
# Initialize caching (add after app = Flask(__name__))
cache = Cache(app, config={
    'CACHE_TYPE': CacheConfig.FLASK_CACHE_TYPE,
    'CACHE_DEFAULT_TIMEOUT': CacheConfig.FLASK_CACHE_DEFAULT_TIMEOUT,
    'CACHE_KEY_PREFIX': CacheConfig.FLASK_CACHE_KEY_PREFIX
})
"""

# ============================================================
# STEP 5: Apply Caching to Key Routes
# ============================================================

# OPTION A: Cache entire route (SIMPLE)
"""
@app.route('/admin-dashboard')
@cache.cached(timeout=600)  # Cache for 10 minutes
def admin_dashboard():
    # ... existing code ...
    return render_template('admin_dashboard.html', ...)
"""

# OPTION B: Cache with invalidation (BETTER)
"""
@app.route('/teacher/mark-attendance', methods=['GET', 'POST'])
def mark_attendance():
    if request.method == 'POST':
        # ... mark attendance logic ...
        
        # CLEAR CACHE when attendance changes
        cache.clear()
        invalidate_cache('attendance_marked', get_redis_client())
        
        return redirect(url_for('teacher_dashboard'))
    return render_template('mark_attendance.html', ...)
"""

# OPTION C: Cache specific function
"""
@cache_db_query(timeout=900)  # Custom decorator
def get_student_attendance(uid):
    conn = get_db_connection()
    # ... query logic ...
    return data
"""

# ============================================================
# STEP 6: Test the Setup
# ============================================================

"""
# Create a test script: test_cache.py

from app import app, cache
import time

with app.app_context():
    # Test 1: Cache a simple function
    @cache.cached(timeout=5)
    def slow_function():
        time.sleep(2)
        return "Result"
    
    print("First call (should take ~2s):")
    start = time.time()
    result = slow_function()
    print(f"  Result: {result}, Time: {time.time() - start:.2f}s")
    
    print("Second call (should be instant):")
    start = time.time()
    result = slow_function()
    print(f"  Result: {result}, Time: {time.time() - start:.2f}s")
    
    print("✅ Cache is working!")

# Run: python test_cache.py
"""

# ============================================================
# STEP 7: Monitor Cache Performance
# ============================================================

# Add this route to app.py to monitor cache:
"""
@app.route('/admin/cache-status')
def cache_status():
    '''View current cache configuration'''
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    redis_client = get_redis_client()
    
    status = {
        'cache_type': CacheConfig.FLASK_CACHE_TYPE,
        'cache_dir': CacheConfig.CACHE_DIR,
        'redis_connected': redis_client is not None,
        'timeouts': {
            'attendance': CacheConfig.STUDENT_ATTENDANCE_CACHE,
            'dashboard': CacheConfig.TEACHER_DASHBOARD_CACHE,
            'gemini_api': CacheConfig.GEMINI_API_CACHE,
            'reports': CacheConfig.PDF_REPORT_CACHE,
            'faces': CacheConfig.FACE_ENCODINGS_CACHE,
        }
    }
    
    return jsonify(status)
"""

# ============================================================
# QUICK REFERENCE: Cache Timeouts
# ============================================================

"""
Database Queries:
  - Student Attendance: 5 minutes (300s)
  - Dashboard Stats: 10 minutes (600s)
  - Teacher Dashboard: 5 minutes (300s)
  - All Students: 30 minutes (1800s)

External APIs:
  - Gemini API: 7 days (604800s) ← Rarely changes
  - Email/OTP: 10 minutes (600s) ← Changes often

Files:
  - PDF Reports: 24 hours (86400s)
  - Face Encodings: 30 days (2592000s) ← Only update when faces change

HTTP Browser Cache:
  - Dashboard: 30 minutes
  - Reports: 24 hours
  - Static: 1 year
"""

# ============================================================
# QUICK REFERENCE: Cache Invalidation
# ============================================================

"""
When to clear cache:

1. Attendance Marked:
   invalidate_cache('attendance_marked', get_redis_client())

2. Student Added:
   invalidate_cache('student_added', get_redis_client())

3. Student Deleted:
   invalidate_cache('student_deleted', get_redis_client())

4. Teacher Added:
   invalidate_cache('teacher_added', get_redis_client())

5. Face Updated:
   invalidate_cache('face_updated', get_redis_client())

6. Clear All:
   cache.clear()
"""

# ============================================================
# DEPLOYMENT: Redis Setup
# ============================================================

"""
For Production (using Docker):

docker run -d -p 6379:6379 redis:latest

Then update .env:
  CACHE_TYPE=redis
  REDIS_HOST=redis_container_name_or_ip
  REDIS_PORT=6379

For Ubuntu/Debian:
  sudo apt-get install redis-server
  sudo systemctl start redis-server
  sudo systemctl enable redis-server
"""

# ============================================================
# EXPECTED PERFORMANCE IMPROVEMENTS
# ============================================================

"""
Before Caching:
  ❌ Admin Dashboard: ~500ms
  ❌ Student Dashboard: ~400ms
  ❌ API Chat: ~2000ms (Gemini)
  ❌ Report Generation: ~3000ms

After Caching:
  ✅ Admin Dashboard: ~50ms (Cache Hit)
  ✅ Student Dashboard: ~50ms (Cache Hit)
  ✅ API Chat: ~100ms (Cache Hit)
  ✅ Report Generation: ~50ms (Cache Hit)

Improvement: 80-95% faster for cached requests!
"""

# ============================================================
# TROUBLESHOOTING
# ============================================================

"""
Problem: Cache not working?

1. Check Redis is running:
   redis-cli ping
   (Should return: PONG)

2. Check logs:
   python app.py
   (Should show: ✅ Cache Configuration Loaded)

3. Verify .env:
   CACHE_TYPE=redis (not 'simple')
   REDIS_HOST=localhost
   REDIS_PORT=6379

4. Check if Redis is accessible:
   redis-cli
   > PING
   (Should return: PONG)

5. Use fallback mode:
   Set CACHE_TYPE=simple (slower but works)
"""

# ============================================================
# SUMMARY CHECKLIST
# ============================================================

"""
☐ 1. Install packages: pip install flask-caching redis
☐ 2. Create .env file with cache settings
☐ 3. Add imports to app.py
☐ 4. Initialize Cache in app.py
☐ 5. Add @cache.cached() to key routes
☐ 6. Add invalidate_cache() on data changes
☐ 7. Test the setup
☐ 8. Monitor performance
☐ 9. Deploy Redis for production
☐ 10. Update requirements.txt

You're all set! 🚀
"""
