import sqlite3
import logging
from datetime import datetime, timedelta
from config import DATABASE_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_PATH)


def init_database():
    """Initialize database tables"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                downloads_count INTEGER DEFAULT 0,
                subscription_end DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create coupons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                duration TEXT NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                used_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                used_at DATETIME
            )
        ''')
        
        # Create mandatory channels table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mandatory_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                channel_name TEXT NOT NULL,
                channel_username TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create admins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def get_user(user_id):
    """Get user from database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'user_id': user[1],
                'downloads_count': user[2],
                'subscription_end': datetime.fromisoformat(user[3]) if user[3] else None,
                'created_at': user[4]
            }
        return None
        
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None


def create_user(user_id):
    """Create new user"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (user_id, downloads_count) VALUES (?, ?)',
            (user_id, 0)
        )
        conn.commit()
        conn.close()
        logger.info(f"Created new user: {user_id}")
        return get_user(user_id)
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None


def increment_downloads(user_id):
    """Increment user download count"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET downloads_count = downloads_count + 1 WHERE user_id = ?',
            (user_id,)
        )
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error incrementing downloads: {e}")


def create_coupon(duration):
    """Create a new coupon"""
    try:
        coupon_code = f"COUPON-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO coupons (code, duration) VALUES (?, ?)',
            (coupon_code, duration)
        )
        conn.commit()
        conn.close()
        logger.info(f"Created coupon: {coupon_code}")
        return coupon_code
        
    except Exception as e:
        logger.error(f"Error creating coupon: {e}")
        return None


def activate_coupon(user_id, coupon_code):
    """Activate a coupon for user"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if coupon exists and is not used
        cursor.execute('SELECT * FROM coupons WHERE code = ? AND used = FALSE', (coupon_code,))
        coupon = cursor.fetchone()
        
        if not coupon:
            conn.close()
            return False
        
        duration = coupon[2]  # duration column
        
        duration_map = {
            '1month': timedelta(days=30),
            '3months': timedelta(days=90),
            'lifetime': timedelta(days=36500)  # ~100 years
        }
        
        duration_delta = duration_map.get(duration)
        if not duration_delta:
            conn.close()
            return False
        
        subscription_end = datetime.now() + duration_delta
        
        # Update user subscription
        cursor.execute(
            'UPDATE users SET subscription_end = ? WHERE user_id = ?',
            (subscription_end.isoformat(), user_id)
        )
        
        # Mark coupon as used
        cursor.execute(
            'UPDATE coupons SET used = TRUE, used_by = ?, used_at = ? WHERE code = ?',
            (user_id, datetime.now().isoformat(), coupon_code)
        )
        
        conn.commit()
        conn.close()
        logger.info(f"Activated coupon {coupon_code} for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error activating coupon: {e}")
        return False


def get_usage_stats():
    """Get usage statistics"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Active subscriptions
        cursor.execute('SELECT COUNT(*) FROM users WHERE subscription_end > ?', (datetime.now().isoformat(),))
        active_subscriptions = cursor.fetchone()[0]
        
        # Total downloads
        cursor.execute('SELECT SUM(downloads_count) FROM users')
        total_downloads = cursor.fetchone()[0] or 0
        
        # Unused coupons
        cursor.execute('SELECT COUNT(*) FROM coupons WHERE used = FALSE')
        unused_coupons = cursor.fetchone()[0]
        
        # Total admins
        cursor.execute('SELECT COUNT(*) FROM admins')
        total_admins = cursor.fetchone()[0]
        
        # Total mandatory channels
        cursor.execute('SELECT COUNT(*) FROM mandatory_channels')
        total_channels = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_subscriptions': active_subscriptions,
            'total_downloads': total_downloads,
            'unused_coupons': unused_coupons,
            'total_admins': total_admins,
            'total_channels': total_channels
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            'total_users': 0,
            'active_subscriptions': 0,
            'total_downloads': 0,
            'unused_coupons': 0,
            'total_admins': 0,
            'total_channels': 0
        }


# Majburiy kanallar uchun funksiyalar
def add_mandatory_channel(channel_id, channel_name, channel_username=None):
    """Add mandatory channel"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO mandatory_channels (channel_id, channel_name, channel_username) VALUES (?, ?, ?)',
            (channel_id, channel_name, channel_username)
        )
        conn.commit()
        conn.close()
        logger.info(f"Added mandatory channel: {channel_name}")
        return True
    except Exception as e:
        logger.error(f"Error adding mandatory channel: {e}")
        return False


def remove_mandatory_channel(channel_id):
    """Remove mandatory channel"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM mandatory_channels WHERE channel_id = ?', (channel_id,))
        conn.commit()
        conn.close()
        logger.info(f"Removed mandatory channel: {channel_id}")
        return True
    except Exception as e:
        logger.error(f"Error removing mandatory channel: {e}")
        return False


def get_mandatory_channels():
    """Get all mandatory channels"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM mandatory_channels')
        channels = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': channel[0],
                'channel_id': channel[1],
                'channel_name': channel[2],
                'channel_username': channel[3],
                'created_at': channel[4]
            }
            for channel in channels
        ]
    except Exception as e:
        logger.error(f"Error getting mandatory channels: {e}")
        return []


# Admin funksiyalar
def add_admin(user_id, username=None):
    """Add admin"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO admins (user_id, username) VALUES (?, ?)',
            (user_id, username)
        )
        conn.commit()
        conn.close()
        logger.info(f"Added admin: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        return False


def remove_admin(user_id):
    """Remove admin"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        logger.info(f"Removed admin: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        return False


def get_all_admins():
    """Get all admins"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins')
        admins = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': admin[0],
                'user_id': admin[1],
                'username': admin[2],
                'created_at': admin[3]
            }
            for admin in admins
        ]
    except Exception as e:
        logger.error(f"Error getting admins: {e}")
        return []
