from psycopg2.extras import RealDictCursor

def get_courses(conn):
    query = """
    SELECT 
        course_id, 
        course_name, 
        course_short_description, 
        course_type, 
        course_duration_hours, 
        course_duration_minutes,  
        language,
        rating ,
        course_profile_image
    FROM lms.course_master
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()  # Fetch all rows as dictionaries

def get_user_courses_with_validity(conn, user_id):
    query = """
    SELECT 
        cm.course_id, 
        cm.course_name, 
        cm.course_short_description, 
        cm.course_type, 
        cm.course_duration_hours, 
        cm.course_duration_minutes,  
        cm.language,
        cm.rating,
        cm.course_profile_image,
        bc.validity,
        bc.updated_date
    FROM 
        lms.users AS u
    JOIN 
        lms.batch_course AS bc
        ON u.batch_id = bc.batch_id
    JOIN 
        lms.course_master AS cm
        ON bc.course_id = cm.course_id
    WHERE 
        u.user_id = %s
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            print(f"Executing query for user_id: {user_id}")
            cursor.execute(query, (user_id,))
            
            # Use fetchall() and convert to list of dictionaries
            rows = cursor.fetchall()
            if not rows:
                print("No courses found")
                return []
                
            # Convert each row to a dictionary and handle any potential None values
            results = []
            for row in rows:
                if row is not None:
                    row_dict = dict(row)
                    # Ensure all fields have default values if None
                    row_dict.update({
                        'course_id': row_dict.get('course_id'),
                        'course_name': row_dict.get('course_name', ''),
                        'course_short_description': row_dict.get('course_short_description', ''),
                        'course_type': row_dict.get('course_type', ''),
                        'course_duration_hours': row_dict.get('course_duration_hours', 0),
                        'course_duration_minutes': row_dict.get('course_duration_minutes', 0),
                        'language': row_dict.get('language', ''),
                        'rating': row_dict.get('rating', 0),
                        'course_profile_image': row_dict.get('course_profile_image', ''),
                        'validity': row_dict.get('validity', 0),
                        'updated_date': str(row_dict.get('updated_date', ''))
                    })
                    results.append(row_dict)
            
            print(f"Found {len(results)} courses")
            return results

    except Exception as e:
        print(f"Error in get_user_courses_with_validity: {str(e)}")
        print(f"Query: {query}")
        print(f"User ID: {user_id}")
        return []
        
def find_course_by_id(conn, user_id,course_id):
    query = """
    SELECT 
    c.course_id, 
    m.course_name, 
    c.course_description, 
    c.course_objective, 
    c.pre_requirments, 
    c.course_level, 
    c.roles, 
    c.course_type,
    course_profile_image,
    CASE 
        WHEN uce.user_id IS NOT NULL THEN true 
        ELSE false 
    END AS enroll
FROM 
    lms.course_enrollment c
JOIN 
    lms.course_master AS m 
    ON m.course_id = c.course_id
LEFT JOIN 
    lms.user_course_enrollment AS uce
    ON uce.course_id = c.course_id AND uce.user_id = %s
WHERE 
    c.course_id = %s;

    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (user_id,course_id))
        return cursor.fetchone()
    
def enroll_user_in_course(conn, user_id, course_id):
    insert_query = """
    INSERT INTO lms.user_course_enrollment (user_id, course_id, enrollment_date)
    VALUES (%s, %s, CURRENT_DATE)
    RETURNING enrollment_id, user_id, course_id, enrollment_date
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(insert_query, (user_id, course_id))
        conn.commit()
        return cursor.fetchone()