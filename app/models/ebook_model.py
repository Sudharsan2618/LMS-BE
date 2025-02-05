from psycopg2.extras import RealDictCursor

def get_ebook_details(conn):
    query = """
        SELECT e_book_id, e_book_name, domain, e_book_object_url, updated_date 
        FROM lms.e_book_master
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()
