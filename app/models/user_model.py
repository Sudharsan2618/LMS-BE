from psycopg2.extras import RealDictCursor

def find_user_by_email(conn, email, password):
    query = "SELECT user_id,username, initial_assessment FROM lms.users WHERE email = %s AND password = %s"
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (email, password))
        user = cursor.fetchone()
        if user:
            user['site'] = 'user'
        return user

def find_admin_by_email(conn, email, password):
    query = "SELECT admin_id, name FROM lms.admin WHERE email = %s AND password = %s"
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (email, password))
        admin = cursor.fetchone()
        if admin:
            admin['site'] = 'admin'
        return admin

def update_unique_key_status(conn, unique_key):
    update_query = "UPDATE lms.new_login SET used='yes' WHERE code=%s"
    with conn.cursor() as cursor:
        cursor.execute(update_query, (unique_key,))
        conn.commit()
        return cursor.rowcount > 0

def create_user(conn, username, email, password, unique_key):
    # First validate the unique key
    if not validate_unique_key(conn, unique_key):
        return {"error": "Invalid or already used unique key"}

    # Check if the email is already present
    check_email_query = "SELECT email FROM lms.users WHERE email = %s"
    insert_query = """
    INSERT INTO lms.users (username, email, password) 
    VALUES (%s, %s, %s) 
    RETURNING user_id as id, username, email
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Check if the email exists
        cursor.execute(check_email_query, (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:  # If email exists, return a specific message
            return {"error": "Email already exists. Try logging in."}
        
        # If email does not exist, insert the new user
        cursor.execute(insert_query, (username, email, password))
        
        # Update the unique key status
        update_unique_key_status(conn, unique_key)
        
        conn.commit()
        return cursor.fetchone()

def validate_unique_key(conn, unique_key):
    query = "SELECT code FROM lms.new_login WHERE code = %s AND used = 'no'"
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (unique_key,))
        result = cursor.fetchone()
        return bool(result)
