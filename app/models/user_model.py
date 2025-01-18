from psycopg2.extras import RealDictCursor


def find_user_by_email(conn, email, password):
    query = "SELECT * FROM lms.users WHERE email = %s AND password = %s"
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (email, password))
        return cursor.fetchone()

def create_user(conn, username, email, password):
    query = """
    INSERT INTO lms.users (username, email, password) 
    VALUES (%s, %s, %s) 
    RETURNING id, username, email
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (username, email, password))
        conn.commit()
        return cursor.fetchone()