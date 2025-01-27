from psycopg2.extras import RealDictCursor

def get_home_headers(conn):
    query = "SELECT header_id, header_name FROM lms.home_header"
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()  # Fetch all rows as dictionaries
