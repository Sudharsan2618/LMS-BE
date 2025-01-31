from psycopg2.extras import RealDictCursor

def get_user_initial_assessment_details(conn, user_id):
    query = """
        SELECT * 
        FROM lms.calculate_assessment_scores(%s) AS result
        """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        # Convert any non-string keys to strings to ensure JSON compatibility
        if result:
            return {str(k): v for k, v in result.items()}
        return None
