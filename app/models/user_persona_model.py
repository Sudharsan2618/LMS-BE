from psycopg2.extras import RealDictCursor

def get_user_persona(conn, user_id):
    query = """
    SELECT
        iar.user_id,
        COALESCE(ts.label, 'No Label') AS tech_skill_label,
        COALESCE(ps.label, 'No Label') AS psychology_label,
        COALESCE(ints.label, 'No Label') AS interests_label,
        COALESCE(ls.label, 'No Label') AS learning_style_label,
        COALESCE(cp.label, 'No Label') AS career_preference_label
    FROM
        lms.initial_assessment_results iar
    LEFT JOIN lms.assessment_score_ranges ts
        ON ts.category = 'tech_skill'
        AND iar.tech_skill BETWEEN ts.min_score AND ts.max_score
    LEFT JOIN lms.assessment_score_ranges ps
        ON ps.category = 'psychology'
        AND iar.psychology BETWEEN ps.min_score AND ps.max_score
    LEFT JOIN lms.assessment_score_ranges ints
        ON ints.category = 'interests'
        AND iar.interests BETWEEN ints.min_score AND ints.max_score
    LEFT JOIN lms.assessment_score_ranges ls
        ON ls.category = 'learning_style'
        AND iar.learning_style BETWEEN ls.min_score AND ls.max_score
    LEFT JOIN lms.assessment_score_ranges cp
        ON cp.category = 'career_preference'
        AND iar.career_preference BETWEEN cp.min_score AND cp.max_score
    WHERE iar.user_id = %s
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (user_id,))
        return cursor.fetchone()
