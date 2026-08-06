"""
Cache Configuration for Smart Attendance Management System
Optimizes API calls, database queries, and external service responses
"""

import os
import hashlib
import json
import time
from functools import wraps
from datetime import datetime, timedelta
import redis

# ================= CACHE SETTINGS =================

class CacheConfig:
    """Configuration for different cache types"""
    
    # Cache directories
    CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')
    FACE_CACHE_DIR = os.path.join(CACHE_DIR, 'faces')
    API_CACHE_DIR = os.path.join(CACHE_DIR, 'api')
    REPORT_CACHE_DIR = os.path.join(CACHE_DIR, 'reports')
    
    # Ensure directories exist
    for directory in [CACHE_DIR, FACE_CACHE_DIR, API_CACHE_DIR, REPORT_CACHE_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    # ================= TIMEOUT SETTINGS (in seconds) =================
    
    # Database Query Cache
    STUDENT_ATTENDANCE_CACHE = 300  # 5 minutes
    STUDENT_PROFILE_CACHE = 900  # 15 minutes
    CLASS_STATS_CACHE = 600  # 10 minutes
    TEACHER_DASHBOARD_CACHE = 300  # 5 minutes
    ALL_STUDENTS_CACHE = 1800  # 30 minutes
    ALL_TEACHERS_CACHE = 1800  # 30 minutes
    
    # External API Cache
    GEMINI_API_CACHE = 604800  # 7 days (rarely changes)
    EMAIL_OTP_CACHE = 600  # 10 minutes
    PDF_REPORT_CACHE = 86400  # 24 hours
    
    # Face Recognition Cache
    FACE_ENCODINGS_CACHE = 2592000  # 30 days (until DB update)
    FACE_COMPARISON_CACHE = 3600  # 1 hour
    
    # HTTP Response Cache
    DASHBOARD_HTTP_CACHE = 1800  # 30 minutes (for browser)
    REPORT_HTTP_CACHE = 86400  # 24 hours
    STATIC_HTTP_CACHE = 31536000  # 1 year
    
    # ================= REDIS SETTINGS =================
    
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # Flask-Caching configuration
    FLASK_CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')  # 'simple', 'redis', or 'filesystem'
    FLASK_CACHE_DEFAULT_TIMEOUT = 300
    FLASK_CACHE_KEY_PREFIX = 'attendance_'
    
    # ================= CACHE INVALIDATION EVENTS =================
    
    INVALIDATE_EVENTS = {
        'attendance_marked': ['class_stats', 'student_attendance', 'teacher_dashboard'],
        'student_added': ['all_students', 'class_stats'],
        'student_deleted': ['all_students', 'class_stats'],
        'teacher_added': ['all_teachers'],
        'face_updated': ['face_encodings', 'face_comparison'],
    }


# ================= REDIS CLIENT =================

def get_redis_client():
    """Get Redis client instance"""
    try:
        client = redis.Redis(
            host=CacheConfig.REDIS_HOST,
            port=CacheConfig.REDIS_PORT,
            db=CacheConfig.REDIS_DB,
            password=CacheConfig.REDIS_PASSWORD,
            decode_responses=True
        )
        client.ping()
        return client
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}. Using fallback caching.")
        return None


# ================= FILE-BASED CACHE UTILITIES =================

class FileCache:
    """File-based cache for non-critical data"""
    
    @staticmethod
    def _get_cache_path(cache_type, key):
        """Generate cache file path"""
        cache_hash = hashlib.md5(key.encode()).hexdigest()
        
        if cache_type == 'api':
            return os.path.join(CacheConfig.API_CACHE_DIR, f"{cache_hash}.json")
        elif cache_type == 'face':
            return os.path.join(CacheConfig.FACE_CACHE_DIR, f"{cache_hash}.pkl")
        elif cache_type == 'report':
            return os.path.join(CacheConfig.REPORT_CACHE_DIR, f"{cache_hash}.pdf")
        return os.path.join(CacheConfig.CACHE_DIR, f"{cache_hash}.json")
    
    @staticmethod
    def get(cache_type, key, timeout):
        """Retrieve cached data"""
        cache_path = FileCache._get_cache_path(cache_type, key)
        
        if not os.path.exists(cache_path):
            return None
        
        # Check if expired
        file_age = time.time() - os.path.getmtime(cache_path)
        if file_age > timeout:
            os.remove(cache_path)
            return None
        
        try:
            with open(cache_path, 'r') as f:
                return json.load(f).get('data')
        except Exception as e:
            print(f"❌ Cache read error: {e}")
            return None
    
    @staticmethod
    def set(cache_type, key, value, timeout):
        """Store data in cache"""
        cache_path = FileCache._get_cache_path(cache_type, key)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'data': value,
                    'cached_at': datetime.now().isoformat(),
                    'expires_at': (datetime.now() + timedelta(seconds=timeout)).isoformat()
                }, f)
        except Exception as e:
            print(f"❌ Cache write error: {e}")
    
    @staticmethod
    def delete(cache_type, key):
        """Delete cached data"""
        cache_path = FileCache._get_cache_path(cache_type, key)
        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
        except Exception as e:
            print(f"❌ Cache delete error: {e}")
    
    @staticmethod
    def clear(cache_type):
        """Clear all cache of a type"""
        if cache_type == 'api':
            directory = CacheConfig.API_CACHE_DIR
        elif cache_type == 'face':
            directory = CacheConfig.FACE_CACHE_DIR
        elif cache_type == 'report':
            directory = CacheConfig.REPORT_CACHE_DIR
        else:
            directory = CacheConfig.CACHE_DIR
        
        try:
            for file in os.listdir(directory):
                os.remove(os.path.join(directory, file))
        except Exception as e:
            print(f"❌ Cache clear error: {e}")


# ================= CACHE DECORATORS =================

def cache_db_query(cache_type='query', timeout=300, key_prefix=''):
    """Decorator for caching database queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix or func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try Redis first
            redis_client = get_redis_client()
            if redis_client:
                cached = redis_client.get(cache_key)
                if cached:
                    print(f"✅ Cache HIT: {cache_key}")
                    return json.loads(cached)
            
            # Try file cache
            cached = FileCache.get(cache_type, cache_key, timeout)
            if cached is not None:
                print(f"✅ File Cache HIT: {cache_key}")
                return cached
            
            # Execute function
            print(f"❌ Cache MISS: {cache_key} (Executing...)")
            result = func(*args, **kwargs)
            
            # Store in cache
            if redis_client:
                redis_client.setex(cache_key, timeout, json.dumps(result, default=str))
            FileCache.set(cache_type, cache_key, result, timeout)
            
            return result
        return wrapper
    return decorator


def cache_api_response(timeout=604800):
    """Decorator for caching external API responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"api_{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try cache
            cached = FileCache.get('api', cache_key, timeout)
            if cached is not None:
                print(f"✅ API Cache HIT: {cache_key}")
                return cached
            
            # Execute API call
            print(f"🔄 API Call: {cache_key}")
            result = func(*args, **kwargs)
            
            # Cache result
            FileCache.set('api', cache_key, result, timeout)
            return result
        return wrapper
    return decorator


# ================= CACHE INVALIDATION =================

def invalidate_cache(event_type, redis_client=None):
    """Invalidate cache based on event"""
    if event_type not in CacheConfig.INVALIDATE_EVENTS:
        return
    
    cache_keys = CacheConfig.INVALIDATE_EVENTS[event_type]
    
    if redis_client is None:
        redis_client = get_redis_client()
    
    for key in cache_keys:
        if redis_client:
            # Delete all keys matching pattern
            for cache_key in redis_client.keys(f"attendance_*{key}*"):
                redis_client.delete(cache_key)
                print(f"🗑️ Invalidated Redis: {cache_key}")
        
        # Clear file cache type
        FileCache.clear(key)
        print(f"🗑️ Invalidated File Cache: {key}")


# ================= RESPONSE CACHE HEADERS =================

def set_cache_headers(response, cache_type='dashboard'):
    """Set appropriate cache headers for HTTP responses"""
    
    if cache_type == 'dashboard':
        response.headers['Cache-Control'] = 'public, max-age=1800'  # 30 min
    elif cache_type == 'report':
        response.headers['Cache-Control'] = 'public, max-age=86400'  # 24 hours
    elif cache_type == 'static':
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    elif cache_type == 'no-cache':
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    response.headers['Vary'] = 'Accept-Encoding'
    return response


# ================= CACHE STATISTICS =================

class CacheStats:
    """Track cache performance"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
    
    def hit_rate(self):
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0
    
    def report(self):
        """Print cache statistics"""
        print(f"""
        ========== CACHE STATISTICS ==========
        Hits: {self.hits}
        Misses: {self.misses}
        Hit Rate: {self.hit_rate():.2f}%
        ======================================
        """)


# ================= INITIALIZATION =================

cache_stats = CacheStats()
redis_client = get_redis_client()

print(f"""
✅ Cache Configuration Loaded:
   - Cache Type: {CacheConfig.FLASK_CACHE_TYPE}
   - Cache Directory: {CacheConfig.CACHE_DIR}
   - Redis Status: {'✅ Connected' if redis_client else '⚠️ Fallback Mode'}
   - Face Cache: {CacheConfig.FACE_ENCODINGS_CACHE}s
   - API Cache: {CacheConfig.GEMINI_API_CACHE}s
   - Report Cache: {CacheConfig.PDF_REPORT_CACHE}s
""")
