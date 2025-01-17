from psycopg2.extras import RealDictCursor

def fetch_initial_assessment_questions_by_tab_id(conn, tab_id):
    query = """
    SELECT 
        tab_id, tab_name, question_id, sequence_id, question, option_a, option_b, option_c, option_d
    FROM 
        us.initial_assessment_questions
    WHERE 
        tab_id = %s
    ORDER BY 
        sequence_id
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (tab_id,))
        return cursor.fetchall()
