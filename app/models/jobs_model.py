from psycopg2.extras import RealDictCursor

def get_all_jobs(conn):
    query = "SELECT * FROM lms.jobs_master"
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()
