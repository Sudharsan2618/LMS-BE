from psycopg2.extras import RealDictCursor

def get_all_jobs(conn):
    query = "SELECT * FROM lms.jobs_master"
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()

def get_jobs_by_user_courses(conn, user_id):
    # First get all course titles for the user
    course_query = """
        SELECT DISTINCT cm.course_name as course_title 
        FROM lms.user_course_enrollment uce
        JOIN lms.course_master cm ON uce.course_id = cm.course_id
        WHERE uce.user_id = %s
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(course_query, (user_id,))
        courses = cursor.fetchall()
        
        if not courses:
            return []
            
        # Create a list to store all search terms
        search_terms = []
        for course in courses:
            # Split course title into words and add to search terms
            words = course['course_title'].split()
            search_terms.extend(words)
            
        # Remove duplicates and create the LIKE conditions
        search_terms = list(set(search_terms))
        like_conditions = " OR ".join([f"description ILIKE %s" for _ in search_terms])
        search_params = [f"%{term}%" for term in search_terms]
        
        # Final query to search jobs
        jobs_query = f"""
            SELECT DISTINCT jm.* 
            FROM lms.jobs_master jm
            WHERE {like_conditions}
        """
        
        cursor.execute(jobs_query, search_params)
        return cursor.fetchall()
