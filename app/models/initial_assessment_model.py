from psycopg2.extras import RealDictCursor

def get_user_initial_assessment_details(conn, user_id):
    query = """
    BEGIN;
    WITH raw_scores AS (
        SELECT 
            SUM(CASE WHEN r.question_id IN (12,13,14,21,22,23,24,25) THEN o.score_value ELSE 0 END) AS v_tech_raw,
            SUM(CASE WHEN r.question_id IN (2,5,10,15,16,17,18,19,20) THEN o.score_value ELSE 0 END) AS v_psych_raw,
            SUM(CASE WHEN r.question_id IN (4,6,7,9,21) THEN o.score_value ELSE 0 END) AS v_interest_raw,
            SUM(CASE WHEN r.question_id IN (1,3,11) THEN o.score_value ELSE 0 END) AS v_learn_raw,
            SUM(CASE WHEN r.question_id IN (8,9,10,19) THEN o.score_value ELSE 0 END) AS v_career_raw
        FROM lms.initial_assessment_responses r
        JOIN lms.initial_assessment_options o 
            ON r.selected_option_id = o.option_id
        WHERE r.user_id = %s\n    ),\n    bounds AS (\n        SELECT\n            8 AS v_tech_min, 32 AS v_tech_max,\n            9 AS v_psych_min, 36 AS v_psych_max,\n            5 AS v_interest_min, 20 AS v_interest_max,\n            3 AS v_learn_min, 12 AS v_learn_max,\n            4 AS v_career_min, 16 AS v_career_max\n    ),\n    calculated_scores AS (\n        SELECT\n            GREATEST(50, LEAST(100, 50 + ((raw_scores.v_tech_raw - bounds.v_tech_min) * 50)::NUMERIC / (bounds.v_tech_max - bounds.v_tech_min))) AS tech_skill,\n            GREATEST(50, LEAST(100, 50 + ((raw_scores.v_psych_raw - bounds.v_psych_min) * 50)::NUMERIC / (bounds.v_psych_max - bounds.v_psych_min))) AS psychology,\n            GREATEST(50, LEAST(100, 50 + ((raw_scores.v_interest_raw - bounds.v_interest_min) * 50)::NUMERIC / (bounds.v_interest_max - bounds.v_interest_min))) AS interests,\n            GREATEST(50, LEAST(100, 50 + ((raw_scores.v_learn_raw - bounds.v_learn_min) * 50)::NUMERIC / (bounds.v_learn_max - bounds.v_learn_min))) AS learning_style,\n            GREATEST(50, LEAST(100, 50 + ((raw_scores.v_career_raw - bounds.v_career_min) * 50)::NUMERIC / (bounds.v_career_max - bounds.v_career_min))) AS career_preference\n        FROM raw_scores, bounds\n    )\n    INSERT INTO lms.initial_assessment_results (\n        user_id, tech_skill, psychology, interests, learning_style, career_preference\n    )\n    SELECT\n        %s AS user_id,\n        tech_skill, psychology, interests, learning_style, career_preference\n    FROM calculated_scores\n    ON CONFLICT (user_id)\n    DO UPDATE SET\n        tech_skill = EXCLUDED.tech_skill,\n        psychology = EXCLUDED.psychology,\n        interests = EXCLUDED.interests,\n        learning_style = EXCLUDED.learning_style,\n        career_preference = EXCLUDED.career_preference,\n        assessment_timestamp = CURRENT_TIMESTAMP;\n\n    UPDATE lms.users\n    SET initial_assessment = 'completed'\n    WHERE user_id = %s;\n\n    COMMIT;\n    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (user_id, user_id, user_id))
        return True
    except Exception as e:
        print(f"Error during assessment results update: {e}")
        return False
