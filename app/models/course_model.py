from psycopg2.extras import RealDictCursor
import pandas as pd

def create_course(conn, course_data):
    insert_query = """
    INSERT INTO lms.course_master(
        course_name, course_short_description, course_type, 
        course_duration_hours, course_duration_minutes, 
        language, rating, course_profile_image)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING course_id
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(insert_query, (
            course_data.get('course_name'),
            course_data.get('course_short_description'),
            course_data.get('course_type'),
            course_data.get('course_duration_hours'),
            course_data.get('course_duration_minutes'),
            course_data.get('language'),
            course_data.get('rating'),
            course_data.get('course_profile_image')
        ))
        conn.commit()
        result = cursor.fetchone()
        return result

def create_course_enrollment(conn, enrollment_data):
    insert_query = """
    INSERT INTO lms.course_enrollment(
        course_id, course_description, course_objective, 
        pre_requirments, course_level, roles, course_type)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING course_enrollment_id as enrollment_id
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # First verify if the course_id exists
        cursor.execute("SELECT course_id FROM lms.course_master WHERE course_id = %s", 
                      (enrollment_data.get('course_id'),))
        if not cursor.fetchone():
            raise ValueError("Course ID does not exist")
            
        cursor.execute(insert_query, (
            enrollment_data.get('course_id'),
            enrollment_data.get('course_description'),
            enrollment_data.get('course_objective'),
            enrollment_data.get('pre_requirments'),
            enrollment_data.get('course_level'),
            enrollment_data.get('roles'),
            enrollment_data.get('course_type')
        ))
        conn.commit()
        result = cursor.fetchone()
        return result

def create_course_content(conn, course_contents):
    insert_query = """
    INSERT INTO lms.course_content(
        course_id, course_mastertitle_breakdown_id, course_mastertitle_breakdown,
        course_subtitle_id, course_subtitle, subtitle_content,
        subtitle_code, subtitle_help_text, helpfull_links)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING course_content_id
    """
    
    inserted_ids = []
    errors = []
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # First verify if the course_id exists
        course_id = course_contents[0].get('course_id')
        cursor.execute("SELECT course_id FROM lms.course_master WHERE course_id = %s", (course_id,))
        if not cursor.fetchone():
            raise ValueError(f"Course ID {course_id} does not exist")
        
        for row_num, content in enumerate(course_contents, start=1):
            try:
                # Clean and validate the data
                cleaned_content = {
                    'course_id': content.get('course_id'),
                    'course_mastertitle_breakdown_id': content.get('course_mastertitle_breakdown_id'),
                    'course_mastertitle_breakdown': str(content.get('course_mastertitle_breakdown', '')).strip(),
                    'course_subtitle_id': content.get('course_subtitle_id'),
                    'course_subtitle': str(content.get('course_subtitle', '')).strip(),
                    'subtitle_content': str(content.get('subtitle_content', '')).strip(),
                    'subtitle_code': str(content.get('subtitle_code', '')).strip(),
                    'subtitle_help_text': str(content.get('subtitle_help_text', '')).strip(),
                    'helpfull_links': str(content.get('helpfull_links', '')).strip()
                }
                
                # Validate required fields
                if not all([cleaned_content['course_id'], 
                          cleaned_content['course_mastertitle_breakdown_id'],
                          cleaned_content['course_subtitle_id']]):
                    raise ValueError("Missing required fields: course_id, course_mastertitle_breakdown_id, or course_subtitle_id")
                
                cursor.execute(insert_query, (
                    cleaned_content['course_id'],
                    cleaned_content['course_mastertitle_breakdown_id'],
                    cleaned_content['course_mastertitle_breakdown'],
                    cleaned_content['course_subtitle_id'],
                    cleaned_content['course_subtitle'],
                    cleaned_content['subtitle_content'],
                    cleaned_content['subtitle_code'],
                    cleaned_content['subtitle_help_text'],
                    cleaned_content['helpfull_links']
                ))
                
                result = cursor.fetchone()
                inserted_ids.append(result['course_content_id'])
                
            except Exception as e:
                errors.append({
                    'row': row_num,
                    'error': str(e)
                })
                continue
        
        if len(errors) == len(course_contents):
            # If all rows failed, rollback and raise exception
            conn.rollback()
            raise ValueError(f"All rows failed to insert. First error: {errors[0]['error']}")
        
        # If some rows succeeded, commit those
        conn.commit()
        
        return {
            'inserted_ids': inserted_ids,
            'total_rows': len(course_contents),
            'successful_inserts': len(inserted_ids),
            'errors': errors
        }
