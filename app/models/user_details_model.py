from psycopg2.extras import RealDictCursor

def get_user_details_with_badges_and_courses(conn, user_id):
    query = """
SELECT 
    u.user_id,
    -- User details aggregated as a single JSON object
    jsonb_build_object(
        'user_id', u.user_id,
        'user_name', u.user_name,
        'age', u.age,
        'mobile_number', u.mobile_number,
        'mail_id', u.mail_id,
        'city', u.city,
        'area_of_interest', u.area_of_interest,
        'highest_qualification', u.highest_qualification,
        'year_of_passedout', u.year_of_passedout,
        'designation', u.designation,
        'ambition', u.ambition,
        'current_organization', u.current_organization,
        'job_title', u.job_title,
        'work_experience', u.work_experience,
        'linkedin_profile', u.linkedin_profile,
        'github_profile', u.github_profile,
        'portfolio_website', u.portfolio_website,
        'profile_picture_url', u.profile_picture_url
    ) AS user_details,
	
jsonb_build_object(
    'Technical Skill', CASE 
                          WHEN iar.tech_skill = 50 THEN 'average'
                          WHEN iar.tech_skill = 80 THEN 'good'
                          WHEN iar.tech_skill = 100 THEN 'awesome'
                          ELSE 'not rated'
                       END,
    'Psychology', CASE 
                     WHEN iar.psychology = 50 THEN 'average'
                     WHEN iar.psychology = 80 THEN 'good'
                     WHEN iar.psychology = 100 THEN 'awesome'
                     ELSE 'not rated'
                  END,
    'Learning Style', CASE 
                         WHEN iar.learning_style = 50 THEN 'average'
                         WHEN iar.learning_style = 80 THEN 'good'
                         WHEN iar.learning_style = 100 THEN 'awesome'
                         ELSE 'not rated'
                      END
) AS our_interpretation,

    -- Badge information as a JSON array
    CASE WHEN COUNT(DISTINCT bm.badge_id) > 0 THEN
        json_agg(
            DISTINCT jsonb_build_object(
                'badge_id', bm.badge_id,
                'badge_name', bm.badge_name,
                'badge_level', bm.badge_level,
                'badge_type', ub.badge_type,
                'earned_date', ub.last_updated
            )
        )
        ELSE NULL
    END AS user_badges,
    
    -- Course information as JSON array
    CASE WHEN COUNT(DISTINCT m.course_id) > 0 THEN
        json_agg(
            DISTINCT jsonb_build_object(
                'course_id', m.course_id,
                'course_name', m.course_name,
                'course_short_description', m.course_short_description,
                'course_type', m.course_type,
                'course_duration_hours', m.course_duration_hours,
                'course_duration_minutes', m.course_duration_minutes,
                'language', m.language
            )
        )
        ELSE NULL
    END AS enrolled_courses,
    
    -- Certification information as JSON array
    CASE WHEN COUNT(DISTINCT cm.certificate_id) > 0 THEN
        json_agg(
            DISTINCT jsonb_build_object(
                'certificate_id', cm.certificate_id,
                'certificate_name', cm.certificate_name,
                'certification_level', cm.certification_level,
                'enrollment_date', uce2.last_update
            )
        )
        ELSE NULL
    END AS user_certifications
FROM 
    lms.user_details AS u
LEFT JOIN 
    lms.user_course_enrollment AS uce ON uce.user_id = u.user_id
LEFT JOIN 
    lms.course_master AS m ON uce.course_id = m.course_id
LEFT JOIN 
    lms.user_badge_enrollment AS ub ON u.user_id = ub.user_id
LEFT JOIN 
    lms.badge_master AS bm ON ub.badge_id = bm.badge_id
LEFT JOIN 
    lms.user_certicate_enrollment AS uce2 ON uce2.user_id = u.user_id
LEFT JOIN 
    lms.certificate_master AS cm ON uce2.certificate_id = cm.certificate_id
left join 
	lms.initial_assessment_results as iar on iar.user_id = u.user_id
WHERE 
    u.user_id = 8
GROUP BY 
    u.user_id, 
    u.user_name, 
    u.age, 
    u.mobile_number, 
    u.mail_id, 
    u.city, 
    u.area_of_interest, 
    u.highest_qualification, 
    u.year_of_passedout, 
    u.designation, 
    u.ambition, 
    u.current_organization, 
    u.job_title, 
    u.work_experience, 
    u.linkedin_profile, 
    u.github_profile, 
    u.portfolio_website, 
    u.profile_picture_url,
	iar.tech_skill,
	iar.psychology,
	iar.learning_style;
 """
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, (user_id,))
        return cursor.fetchone()





def update_user_details(conn, data):
    query = """
    UPDATE lms.user_details
    SET 
        user_name = %(user_name)s,
        age = %(age)s,
        mobile_number = %(mobile_number)s,
        mail_id = %(mail_id)s,
        city = %(city)s,
        area_of_interest = %(area_of_interest)s,
        highest_qualification = %(highest_qualification)s,
        year_of_passedout = %(year_of_passedout)s,
        designation = %(designation)s,
        ambition = %(ambition)s,
        current_organization = %(current_organization)s,
        job_title = %(job_title)s,
        work_experience = %(work_experience)s,
        linkedin_profile = %(linkedin_profile)s,
        github_profile = %(github_profile)s,
        portfolio_website = %(portfolio_website)s,
        profile_picture_url = %(profile_picture_url)s
    WHERE user_id = %(user_id)s
    """
    with conn.cursor() as cursor:
        cursor.execute(query, data)
        conn.commit()
        return cursor.rowcount > 0
