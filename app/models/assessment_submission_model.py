from psycopg2.extras import RealDictCursor

def submit_assessment_and_enroll_certificate(conn, user_id, course_id, answers):
    try:
        with conn.cursor() as cursor:
            # Start transaction
            cursor.execute("BEGIN")
            
            # First, get the certificate_id for the course
            cursor.execute("""
                SELECT certificate_id
                FROM lms.certificate_master
                WHERE course_id = %s
            """, (course_id,))
            
            result = cursor.fetchone()
            if not result:
                raise Exception("No certificate found for this course")
            
            certificate_id = result[0]
            
            # Insert into user_certificate_enrollment
            cursor.execute("""
                INSERT INTO lms.user_certicate_enrollment(certificate_id, user_id)
                VALUES (%s, %s)
            """, (certificate_id, user_id))
            
            # Here you would typically also insert the assessment answers
            # This is a placeholder - adjust according to your actual assessment table structure
            for answer in answers:
                cursor.execute("""
                    INSERT INTO lms.course_assessment_responses
                    (user_id, course_id, question_id, selected_option_id)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, course_id, answer['question_id'], answer['selected_option_id']))
            
            # Commit transaction
            conn.commit()
            return True
            
    except Exception as e:
        # Rollback transaction on error
        conn.rollback()
        raise e 