from psycopg2.extras import RealDictCursor

def find_answer_by_question_and_option(conn, question_id, option_id):
    query = """
    SELECT 
        question_id,
        question,
        answer,
        question_sequenceid
    FROM lms.course_assessment 
    WHERE question_id = %s AND answer_id = %s
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (question_id, option_id))
        return cursor.fetchone()
