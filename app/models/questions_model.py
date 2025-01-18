from psycopg2.extras import RealDictCursor

def fetch_initial_assessment_questions_by_tab_id(conn, tab_id, user_id):
    query = """
    SELECT 
    q.question_id,
    q.question_text AS question,
    t.tab_name,  -- Tab name added
    JSON_AGG(
        JSON_BUILD_OBJECT(
            'option_id', o.option_id,
            'option_text', o.option_text
        ) ORDER BY o.option_id
    ) AS options,
    JSON_BUILD_OBJECT(
        'selected_option_id', MAX(COALESCE(r.selected_option_id, NULL))
    ) AS selected_option
FROM 
    lms.initial_assessment_questions q
JOIN 
    lms.initial_assessment_options o ON q.question_id = o.question_id
LEFT JOIN 
    lms.initial_assessment_responses r ON r.question_id = q.question_id
    AND r.user_id = %s
JOIN 
    lms.initial_assessment_tabs t ON t.tab_id = q.tab_id  -- Join to get tab_name
WHERE 
    q.tab_id = %s
GROUP BY 
    q.question_text, q.question_id, t.tab_name  -- Add t.tab_name to GROUP BY
ORDER BY 
    q.question_id;
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (user_id, tab_id))
        return cursor.fetchall()
