from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
import uuid

def create_batch(batch_name):
    """
    Create a new batch and return the batch_id
    """
    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO lms.batch (batch_name) VALUES (%s) RETURNING batch_id",
            (batch_name,)
        )
        batch_id = cursor.fetchone()[0]
        conn.commit()
        return batch_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def associate_course_with_batch(batch_id, course_id, validity):
    """
    Associate a course with a batch and set its validity period
    """
    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO lms.batch_course (batch_id, course_id, validity) VALUES (%s, %s, %s) RETURNING bc_id",
            (batch_id, course_id, validity)
        )
        bc_id = cursor.fetchone()[0]
        conn.commit()
        return bc_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def create_login_key(batch_id):
    """
    Create a new login key associated with a batch
    """
    conn = get_db_connection(DB_CONFIG)
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO lms.new_login (code, used, batch_id) VALUES (%s, %s, %s) RETURNING code",
            (str(uuid.uuid4()), "no", batch_id)
        )
        key_id = cursor.fetchone()[0]
        conn.commit()
        return key_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close() 