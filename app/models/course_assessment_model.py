from psycopg2.extras import RealDictCursor

def find_answer_by_question_id(conn, question_id):
    query = "SELECT answer FROM lms.course_assessment WHERE question_id = %s"
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (question_id,))
        return cursor.fetchone()
