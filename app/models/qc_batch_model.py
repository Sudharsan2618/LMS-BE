from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
import uuid
import json

def create_qc_batch(qc_batch_name):
    """
    Create a new QC batch and return the qc_id
    """
    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO lms.qcbatch(qc_batch_name) VALUES (%s) RETURNING qc_id",
            (qc_batch_name,)
        )
        qc_id = cursor.fetchone()[0]
        conn.commit()
        return qc_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def update_user_qc_id(user_id, qc_id):
    """
    Update the qc_id for a specific user
    """
    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE lms.users SET qc_id = %s WHERE user_id = %s RETURNING user_id",
            (qc_id, user_id)
        )
        updated_user = cursor.fetchone()
        conn.commit()
        return updated_user[0] if updated_user else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def create_qc_user_course(qc_id, user_id, course_id, validity):
    """
    Create a new QC user course association
    """
    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO lms.qc_user_course(qc_id, user_id, course_id, validity) 
            VALUES (%s, %s, %s, %s) 
            RETURNING qcuc_id
            """,
            (qc_id, user_id, course_id, validity)
        )
        qcuc_id = cursor.fetchone()[0]
        conn.commit()
        return qcuc_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_qc_batch_analytics(conn):
    """
    Get analytics data for all QC batches
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                qc.qc_id,
                qc.qc_batch_name,
                COUNT(DISTINCT u.user_id) as total_users,
                COUNT(DISTINCT qcuc.course_id) as total_courses,
                AVG(qcuc.validity) as avg_validity
            FROM lms.qcbatch qc
            LEFT JOIN lms.users u ON u.qc_id = qc.qc_id
            LEFT JOIN lms.qc_user_course qcuc ON qcuc.qc_id = qc.qc_id
            GROUP BY qc.qc_id, qc.qc_batch_name
            ORDER BY qc.qc_id DESC
        """)
        results = cursor.fetchall()
        return [{
            'qc_id': row[0],
            'batch_name': row[1],
            'total_users': row[2],
            'total_courses': row[3],
            'avg_validity': float(row[4]) if row[4] else 0
        } for row in results]
    except Exception as e:
        raise e

def get_user_qc_id(conn, user_id):
    """
    Get QC ID for a specific user
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT qc_id FROM lms.users WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        raise e

def add_course_to_user(conn, user_id, course_id, validity):
    """
    Add a course to a user's QC batch
    """
    try:
        # First get the user's qc_id
        qc_id = get_user_qc_id(conn, user_id)
        if not qc_id:
            return None

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO lms.qc_user_course(qc_id, user_id, course_id, validity) 
            VALUES (%s, %s, %s, %s) 
            RETURNING qcuc_id
            """,
            (qc_id, user_id, course_id, validity)
        )
        qcuc_id = cursor.fetchone()[0]
        conn.commit()
        return qcuc_id
    except Exception as e:
        conn.rollback()
        raise e

def extend_course_validity(conn, user_id, course_id, new_validity):
    """
    Extend the validity period for a user's course
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE lms.qc_user_course 
            SET validity = %s
            WHERE user_id = %s AND course_id = %s
            RETURNING qcuc_id
            """,
            (new_validity, user_id, course_id)
        )
        result = cursor.fetchone()
        conn.commit()
        return result[0] if result else None
    except Exception as e:
        conn.rollback()
        raise e

def get_detailed_qc_analytics(conn):
    """
    Get detailed analytics data for all QC batches including user course progress
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            WITH user_course_data AS (
    SELECT 
        u.user_id,
        u.username,
        u.qc_id,
        qb.qc_batch_name AS batch_name,
        u.initial_assessment,
        cm.course_id,
        cm.course_name,
        CASE 
            WHEN uce.user_id IS NOT NULL THEN 'Enrolled'
            ELSE 'Not Enrolled' 
        END AS enrollment_status,
        CASE 
            WHEN ce.certificate_id IS NOT NULL THEN 'Completed'
            WHEN uce.user_id IS NOT NULL THEN 'In Progress'
            ELSE 'Not Started'
        END AS completion_status,
        ce.certificate_id,
        GREATEST(COALESCE(qcuc.validity, 0), 0) AS validity,
        GREATEST(COALESCE(qcuc.updated_date, '1970-01-01'), '1970-01-01') AS updated_date
    FROM 
        lms.users AS u
    LEFT JOIN 
        lms.qcbatch AS qb ON qb.qc_id = u.qc_id
    LEFT JOIN 
        lms.qc_user_course AS qcuc ON qcuc.qc_id = u.qc_id AND qcuc.user_id = u.user_id
    LEFT JOIN 
        lms.course_master AS cm ON cm.course_id = qcuc.course_id
    LEFT JOIN 
        lms.user_course_enrollment AS uce ON uce.user_id = u.user_id AND uce.course_id = qcuc.course_id
    LEFT JOIN 
        lms.certificate_master AS cert_m ON cert_m.course_id = cm.course_id
    LEFT JOIN 
        lms.user_certicate_enrollment AS ce ON ce.certificate_id = cert_m.certificate_id AND ce.user_id = u.user_id
    WHERE 
        cm.course_id IS NOT NULL
),
user_courses AS (
    SELECT
        user_id,
        username,
        qc_id,
        batch_name,
        initial_assessment,
        JSON_AGG(
            JSON_BUILD_OBJECT(
                'course_id', course_id,
                'course_name', course_name,
                'enrollment_status', enrollment_status,
                'completion_status', completion_status,
                'certificate_id', certificate_id,
                'validity', validity,
                'updated_date', updated_date
            )
        ) AS courses
    FROM 
        user_course_data
    GROUP BY
        user_id, username, qc_id, batch_name, initial_assessment
),
batches_data AS (
    SELECT 
        uc.qc_id,
        uc.batch_name,
        JSON_AGG(
            JSON_BUILD_OBJECT(
                'user_id', uc.user_id, -- Include user_id here
                'username', uc.username,
                'initial_assessment', uc.initial_assessment,
                'courses', uc.courses
            )
        ) AS users_json
    FROM 
        user_courses uc
    GROUP BY 
        uc.qc_id, uc.batch_name
)
SELECT 
    JSON_BUILD_OBJECT(
        'status', 'success',
        'data', JSON_BUILD_OBJECT(
            'total_batches', (SELECT COUNT(*) FROM lms.qcbatch),
            'batches', 
            COALESCE(
                (SELECT JSON_AGG(
                    JSON_BUILD_OBJECT(
                        'qc_id', qc_id,
                        'batch_name', batch_name,
                        'users', users_json
                    )
                ) FROM batches_data),
                '[]'::json
            )
        )
    )::text AS result;
        """)
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]  # Return the JSON string directly
        return '{"total_batches": 0, "batches": []}'  # Return empty JSON string
    except Exception as e:
        print(f"Error in get_detailed_qc_analytics: {str(e)}")  # Add logging
        raise e 