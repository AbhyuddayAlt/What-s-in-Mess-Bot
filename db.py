import psycopg2
from psycopg2 import pool

# Database configuration
DB_NAME = 'railway'
DB_USER = 'postgres'
DB_PASSWORD = 'lYHvrGIWEvlneKyJuPohebsjqbaXikuV'
DB_HOST = 'postgres.railway.internal'
DB_PORT = '5432'

# Create a connection pool
connection_pool = pool.SimpleConnectionPool(
    1,  # minconn
    10,  # maxconn
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

def init_db():
    """Initialize the database and create necessary tables"""
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            # Create users table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    auto_updates BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        connection_pool.putconn(conn)

def save_user(user_id, username=None, first_name=None, last_name=None):
    """Save or update user information"""
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, last_interaction)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    last_interaction = CURRENT_TIMESTAMP
            """, (user_id, username, first_name, last_name))
            conn.commit()
    except Exception as e:
        print(f"Error saving user: {e}")
        raise
    finally:
        connection_pool.putconn(conn)

def get_all_users():
    """Get all user IDs from the database"""
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users")
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"Error getting users: {e}")
        return []
    finally:
        connection_pool.putconn(conn)

def update_notification_settings(user_id, auto_updates=None):
    """Update user's notification settings"""
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            if auto_updates is not None:
                cur.execute("""
                    UPDATE users 
                    SET auto_updates = %s
                    WHERE user_id = %s
                """, (auto_updates, user_id))
                conn.commit()
    except Exception as e:
        print(f"Error updating notification settings: {e}")
        raise
    finally:
        connection_pool.putconn(conn)

def get_user_settings(user_id):
    """Get user's notification settings"""
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT auto_updates 
                FROM users 
                WHERE user_id = %s
            """, (user_id,))
            result = cur.fetchone()
            return (15, result[0]) if result else None
    except Exception as e:
        print(f"Error getting user settings: {e}")
        return None
    finally:
        connection_pool.putconn(conn) 
