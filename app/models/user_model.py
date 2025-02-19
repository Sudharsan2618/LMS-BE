from psycopg2.extras import RealDictCursor

def find_user_by_email(conn, email, password):
    query = "SELECT user_id,username, initial_assessment FROM lms.users WHERE email = %s AND password = %s"
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (email, password))
        return cursor.fetchone()

def create_user(conn, username, email, password):
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
        conn.commit()
        return cursor.fetchone()
