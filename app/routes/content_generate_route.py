from flask import Blueprint, request, Response, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import threading
import time
from app.utils.db_utils import get_db_connection
from app.config.database import DB_CONFIG
from psycopg2.extras import RealDictCursor
import re

load_dotenv()

content_generate_bp = Blueprint('content_generate', __name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Global variable to store background task results
background_tasks = {}

def insert_course_content(conn, course_content_data):
    """
    Insert course content into the database
    """
    insert_query = """
    INSERT INTO lms.course_content_transaction(
        course_id, course_mastertitle_breakdown_id, course_mastertitle_breakdown,
        course_subtitle_id, course_subtitle, subtitle_content,
        subtitle_code, subtitle_help_text, helpfull_links)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING course_content_id
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        try:
            cursor.execute(insert_query, (
                course_content_data['course_id'],
                course_content_data['course_mastertitle_breakdown_id'],
                course_content_data['course_mastertitle_breakdown'],
                course_content_data['course_subtitle_id'],
                course_content_data['course_subtitle'],
                course_content_data['subtitle_content'],
                course_content_data.get('subtitle_code', ''),
                course_content_data['subtitle_help_text'],
                course_content_data['helpful_links']
            ))
            result = cursor.fetchone()
            conn.commit()
            return result['course_content_id']
        except Exception as e:
            conn.rollback()
            print(f"Database error in insert_course_content: {str(e)}")
            # Try to create the table with correct structure if it doesn't exist
            try:
                create_table_query = """
                CREATE TABLE IF NOT EXISTS lms.course_content_transaction
                (
                    course_content_id SERIAL PRIMARY KEY,
                    course_id integer NOT NULL,
                    course_mastertitle_breakdown_id integer NOT NULL,
                    course_mastertitle_breakdown character varying(100),
                    course_subtitle_id integer NOT NULL,
                    course_subtitle character varying(100),
                    subtitle_content text,
                    subtitle_code text,
                    subtitle_help_text text,
                    helpfull_links text
                );
                """
                cursor.execute(create_table_query)
                conn.commit()
                
                # Retry the insert
                cursor.execute(insert_query, (
                    course_content_data['course_id'],
                    course_content_data['course_mastertitle_breakdown_id'],
                    course_content_data['course_mastertitle_breakdown'],
                    course_content_data['course_subtitle_id'],
                    course_content_data['course_subtitle'],
                    course_content_data['subtitle_content'],
                    course_content_data.get('subtitle_code', ''),
                    course_content_data['subtitle_help_text'],
                    course_content_data['helpful_links']
                ))
                result = cursor.fetchone()
                conn.commit()
                return result['course_content_id']
            except Exception as create_error:
                print(f"Failed to create course_content table: {str(create_error)}")
                raise

def update_content_progress(conn, course_id, task_id, status, q_status=None):
    """
    Update or insert content generation progress, including q_status
    """
    # First try to update existing record
    if q_status is not None:
        update_query = """
        UPDATE lms.course_content_progress 
        SET status = %s, q_status = %s, updated_date = CURRENT_TIMESTAMP
        WHERE course_id = %s AND task_id = %s
        """
    else:
        update_query = """
        UPDATE lms.course_content_progress 
        SET status = %s, updated_date = CURRENT_TIMESTAMP
        WHERE course_id = %s AND task_id = %s
        """
    
    with conn.cursor() as cursor:
        try:
            if q_status is not None:
                cursor.execute(update_query, (status, q_status, course_id, task_id))
            else:
                cursor.execute(update_query, (status, course_id, task_id))
            
            # If no rows were updated, insert new record
            if cursor.rowcount == 0:
                if q_status is not None:
                    insert_query = """
                    INSERT INTO lms.course_content_progress(course_id, task_id, status, q_status, updated_date)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """
                    cursor.execute(insert_query, (course_id, task_id, status, q_status))
                else:
                    insert_query = """
                    INSERT INTO lms.course_content_progress(course_id, task_id, status, updated_date)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    """
                    cursor.execute(insert_query, (course_id, task_id, status))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Database error in update_content_progress: {str(e)}")
            # Try to create the table with correct structure if it doesn't exist
            try:
                create_table_query = """
                CREATE TABLE IF NOT EXISTS lms.course_content_progress
                (
                    course_id integer NOT NULL,
                    task_id character varying(100) NOT NULL,
                    status character varying(50) NOT NULL,
                    q_status character varying(50),
                    updated_date timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
                cursor.execute(create_table_query)
                conn.commit()
                
                # Retry the insert
                if q_status is not None:
                    insert_query = """
                    INSERT INTO lms.course_content_progress(course_id, task_id, status, q_status, updated_date)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """
                    cursor.execute(insert_query, (course_id, task_id, status, q_status))
                else:
                    insert_query = """
                    INSERT INTO lms.course_content_progress(course_id, task_id, status, updated_date)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    """
                    cursor.execute(insert_query, (course_id, task_id, status))
                conn.commit()
            except Exception as create_error:
                print(f"Failed to create table: {str(create_error)}")
                raise

def stream_gemini_response(response):
    collected_chunks = []
    try:
        for chunk in response:
            if hasattr(chunk, 'text') and chunk.text:
                content = chunk.text
                collected_chunks.append(content)
                # Print each chunk to the console
                print("Streaming chunk:", content)
                yield f"data: {json.dumps({'content': content})}\n\n"
        complete_response = "".join(collected_chunks)
        try:
            clean_response = complete_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            parsed_json = json.loads(clean_response)
            print("Streaming complete JSON:", parsed_json)
            yield f"data: {json.dumps({'complete': parsed_json})}\n\n"
        except json.JSONDecodeError as e:
            print("JSON decode error:", str(e))
            yield f"data: {json.dumps({'error': f'Invalid JSON response: {str(e)}'})}\n\n"
    except Exception as e:
        print("Streaming error:", str(e))
        yield f"data: {json.dumps({'error': f'Streaming error: {str(e)}'})}\n\n"

def clean_json_response(response_text):
    """
    Clean and fix common JSON response issues from AI models, robustly handle arrays and code block markers
    """
    if not response_text:
        return None
    
    # Remove markdown code blocks
    text = response_text.strip()
    if text.startswith('```json'):
        text = text[7:]
    elif text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    text = text.strip()
    
    # Try to find a JSON array in the text
    array_start = text.find('[')
    array_end = text.rfind(']')
    if array_start != -1 and array_end != -1 and array_end > array_start:
        array_str = text[array_start:array_end+1]
        try:
            return json.loads(array_str)
        except Exception as e:
            print(f"Failed to parse JSON array: {e}")
            print(f"Array string: {array_str[:500]}...")
    
    # If not an array, try to find a JSON object
    obj_start = text.find('{')
    obj_end = text.rfind('}')
    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        obj_str = text[obj_start:obj_end+1]
        try:
            return json.loads(obj_str)
        except Exception as e:
            print(f"Failed to parse JSON object: {e}")
            print(f"Object string: {obj_str[:500]}...")
    
    # Last resort: try to remove newlines and parse
    try:
        return json.loads(text.replace('\n', ' ').replace('\r', ' '))
    except Exception as e:
        print(f"All JSON parsing attempts failed: {e}")
        print(f"Original text: {response_text[:500]}...")
        return None

def generate_subtitle_content_fallback(master_title, subtitle, course_name=None):
    """
    Fallback content generation without JSON parsing
    """
    try:
        safe_subtitle = subtitle.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
        safe_master_title = master_title.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
        
        prompt = f"""Generate educational content for "{safe_subtitle}" under "{safe_master_title}".

Provide the content in this exact format (no JSON, no markdown):

Content: [Detailed educational content here]

Help Text: [Helpful guidance and tips here]

Links: [Comma-separated URLs here]"""

        generation_config = genai.types.GenerationConfig(
            temperature=0.4,
            top_p=0.8,
            top_k=40,
            max_output_tokens=2000,
        )

        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt, generation_config=generation_config)
        
        text = response.text.strip()
        
        # Parse the structured text response
        content = ""
        help_text = ""
        links = ""
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Content:'):
                content = line[8:].strip()
            elif line.startswith('Help Text:'):
                help_text = line[11:].strip()
            elif line.startswith('Links:'):
                links = line[7:].strip()
        
        return {
            "subtitle_content": content or f"Content for {subtitle}",
            "subtitle_help_text": help_text or f"Help text for {subtitle}",
            "helpful_links": links or ""
        }
        
    except Exception as e:
        print(f"Fallback generation failed for subtitle '{subtitle}': {str(e)}")
        return {
            "subtitle_content": f"Content for {subtitle}",
            "subtitle_help_text": f"Help text for {subtitle}",
            "helpful_links": ""
        }

def generate_subtitle_content(master_title, subtitle, course_name=None):
    """
    Generate detailed content for a specific subtitle
    """
    try:
        # Sanitize inputs to prevent JSON injection
        safe_subtitle = subtitle.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
        safe_master_title = master_title.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
        
        prompt = f"""Generate comprehensive educational content for the subtitle "{safe_subtitle}" under the master topic "{safe_master_title}".

Course Context: {course_name if course_name else 'General Course'}

Requirements:
1. Generate detailed "subtitle_content" that covers the topic comprehensively
2. Create helpful "subtitle_help_text" that provides guidance and tips
3. Provide relevant "helpful_links" for further learning

The response should be in this exact JSON format:
{{
    "subtitle_content": "Comprehensive educational content covering the topic in detail...",
    "subtitle_help_text": "Helpful guidance and tips for understanding this topic...",
    "helpful_links": "https://example1.com,https://example2.com,https://example3.com"
}}

Guidelines for content generation:
- subtitle_content: Should be detailed, educational, and cover the topic comprehensively
- subtitle_help_text: Should provide practical tips, best practices, and guidance
- helpful_links: Should include 3-5 relevant, high-quality resources for further learning
- Make content practical and industry-relevant
- Include examples and real-world applications where appropriate
- Focus on making the content engaging and easy to understand
- Avoid using backslashes or special characters that could break JSON parsing
- Use proper JSON escaping for any quotes or special characters
- Keep the response as clean JSON without markdown formatting
- Do not include any escape sequences or special characters in the JSON values"""

        generation_config = genai.types.GenerationConfig(
            temperature=0.4,
            top_p=0.8,
            top_k=40,
            max_output_tokens=2000,
        )

        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt, generation_config=generation_config)
        
        print(f"Raw response for subtitle '{subtitle}': {response.text[:200]}...")
        
        # Use the robust JSON cleaning function
        parsed_json = clean_json_response(response.text)
        
        if parsed_json is None:
            print(f"JSON parsing failed for subtitle: {subtitle}")
            print("Attempting fallback content generation...")
            # Try fallback method
            return generate_subtitle_content_fallback(master_title, subtitle, course_name)
        
        print(f"Successfully parsed JSON for subtitle: {subtitle}")
        return parsed_json
        
    except Exception as e:
        print(f"Error generating content for subtitle '{subtitle}': {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print("Attempting fallback content generation...")
        # Try fallback method
        return generate_subtitle_content_fallback(master_title, subtitle, course_name)

def call_insert_course_assessment(conn, course_id, question, answer, answer_id, question_sequenceid, options):
    """
    Call the insert_course_assessment stored procedure with question_sequenceid
    """
    with conn.cursor() as cursor:
        cursor.execute(
            "CALL insert_course_assessment(%s, %s, %s, %s, %s, %s)",
            (course_id, question, answer, answer_id, question_sequenceid, options)
        )
        conn.commit()

def generate_questions_for_content(content_list, course_name):
    """
    Generate 10 contextual and 10 company questions with 4 options each
    Returns a list of dicts: {question, answer, answer_id, options}
    """
    questions = []
    # 10 contextual questions
    context = '\n'.join([item.get('subtitle_content', '') for item in content_list if item.get('subtitle_content')])
    prompt_contextual = f"""Based on the following course content for '{course_name}', generate 10 high-standard multiple-choice questions. Each question should have 4 options, and specify the correct answer and its index (1-based). Return as JSON array with fields: question, options (array), answer, answer_id (1-4).\n\nContent:\n{context}\n\nFormat:\n[{{'question': '...', 'options': ['A', 'B', 'C', 'D'], 'answer': '...', 'answer_id': 2}}, ...]"""
    
    # 10 company questions
    prompt_company = f"""Generate 10 high-standard multiple-choice questions that are most commonly asked by companies for '{course_name}'. Each question should have 4 options, and specify the correct answer and its index (1-based). Return as JSON array with fields: question, options (array), answer, answer_id (1-4).\n\nFormat:\n[{{'question': '...', 'options': ['A', 'B', 'C', 'D'], 'answer': '...', 'answer_id': 2}}, ...]"""
    
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    # Contextual questions
    resp1 = model.generate_content(prompt_contextual)
    try:
        q1 = clean_json_response(resp1.text)
        if isinstance(q1, list):
            questions.extend(q1)
    except Exception as e:
        print(f"Error parsing contextual questions: {e}")
    # Company questions
    resp2 = model.generate_content(prompt_company)
    try:
        q2 = clean_json_response(resp2.text)
        if isinstance(q2, list):
            questions.extend(q2)
    except Exception as e:
        print(f"Error parsing company questions: {e}")
    return questions[:20]  # Ensure max 20

def process_course_content_background(task_id, course_data, course_name=None, course_id=None):
    """
    Background function to process course content generation and store in database
    """
    conn = None
    try:
        # Initialize database connection
        conn = get_db_connection(DB_CONFIG)
        if not conn:
            raise Exception("Database connection failed")
        
        # Ensure tables exist with correct structure
        ensure_tables_exist(conn)
        
        result = {
            "status": "processing",
            "progress": 0,
            "total_items": 0,
            "completed_items": 0,
            "data": []
        }
        
        # Calculate total items
        total_items = 0
        for master_topic in course_data.get('course_mastertitle_breakdown', []):
            total_items += len(master_topic.get('subtitles', []))
        
        result["total_items"] = total_items
        
        # Update initial status in database
        update_content_progress(conn, course_id, task_id, "processing")
        
        # Process each master topic and subtitle with proper ID sequencing
        master_title_id = 1
        for master_topic in course_data.get('course_mastertitle_breakdown', []):
            master_title = master_topic.get('master_title', '')
            subtitles = master_topic.get('subtitles', [])
            
            subtitle_id = 1  # Reset subtitle ID for each master title
            for subtitle in subtitles:
                try:
                    # Generate content for this subtitle
                    content_data = generate_subtitle_content(master_title, subtitle, course_name)
                    
                    # Create the result structure for API response
                    subtitle_result = {
                        "course_mastertitle_breakdown": master_title,
                        "course_subtitle": subtitle,
                        "subtitle_content": content_data.get("subtitle_content", ""),
                        "subtitle_help_text": content_data.get("subtitle_help_text", ""),
                        "helpful_links": content_data.get("helpful_links", "")
                    }
                    
                    # Prepare data for database insertion
                    db_content_data = {
                        "course_id": course_id,
                        "course_mastertitle_breakdown_id": master_title_id,
                        "course_mastertitle_breakdown": master_title,
                        "course_subtitle_id": subtitle_id,
                        "course_subtitle": subtitle,
                        "subtitle_content": content_data.get("subtitle_content", ""),
                        "subtitle_code": "",  # Can be populated later if needed
                        "subtitle_help_text": content_data.get("subtitle_help_text", ""),
                        "helpful_links": content_data.get("helpful_links", "")
                    }
                    
                    # Insert into database
                    content_id = insert_course_content(conn, db_content_data)
                    
                    # Add content_id to result for reference
                    subtitle_result["content_id"] = content_id
                    
                    result["data"].append(subtitle_result)
                    result["completed_items"] += 1
                    result["progress"] = int((result["completed_items"] / total_items) * 100)
                    
                    # Update the global task status
                    background_tasks[task_id] = result
                    
                    # Update progress in database
                    update_content_progress(conn, course_id, task_id, f"processing_{result['progress']}%")
                    
                    subtitle_id += 1  # Increment subtitle ID
                    
                    # Small delay to prevent overwhelming the API
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error processing subtitle '{subtitle}': {str(e)}")
                    # Add error entry
                    subtitle_result = {
                        "course_mastertitle_breakdown": master_title,
                        "course_subtitle": subtitle,
                        "subtitle_content": f"Error: {str(e)}",
                        "subtitle_help_text": "Content generation failed",
                        "helpful_links": ""
                    }
                    result["data"].append(subtitle_result)
                    result["completed_items"] += 1
                    result["progress"] = int((result["completed_items"] / total_items) * 100)
                    background_tasks[task_id] = result
                    subtitle_id += 1
            
            master_title_id += 1  # Increment master title ID
        
        # Mark as completed for content
        result["status"] = "completed"
        background_tasks[task_id] = result
        
        # Update final status in database
        update_content_progress(conn, course_id, task_id, "completed")
        
        # --- Question Generation ---
        # Set q_status to processing
        update_content_progress(conn, course_id, task_id, "completed", q_status="processing")
        
        # Generate questions
        questions = generate_questions_for_content(result["data"], course_name)
        print(f"Generated {len(questions)} questions for course_id {course_id}")
        
        # Store questions using the stored procedure
        for idx, q in enumerate(questions, start=1):
            try:
                call_insert_course_assessment(
                    conn,
                    course_id,
                    q.get('question'),
                    q.get('answer'),
                    q.get('answer_id'),
                    idx,  # question_sequenceid (1-20)
                    q.get('options')
                )
            except Exception as e:
                print(f"Error storing question: {q.get('question')}, error: {e}")
        
        # Set q_status to completed
        update_content_progress(conn, course_id, task_id, "completed", q_status="completed")
        
    except Exception as e:
        result = {
            "status": "error",
            "error": str(e),
            "data": []
        }
        background_tasks[task_id] = result
        
        # Update error status in database
        if conn:
            try:
                update_content_progress(conn, course_id, task_id, f"error: {str(e)}")
            except Exception as db_error:
                print(f"Failed to update error status in database: {str(db_error)}")
    
    finally:
        if conn:
            conn.close()

@content_generate_bp.route('/api/content-generate', methods=['POST'])
def generate_course_syllabus():
    try:
        data = request.get_json()
        course_name = data.get('course_name')
        content_type = data.get('content_type')
        duration_hours = int(data.get('duration_hours', 0))
        duration_minutes = int(data.get('duration_minutes', 0))
        preferences = data.get('preferences', None)

        total_minutes = (duration_hours * 60) + duration_minutes
        total_hours_display = f"{duration_hours}h {duration_minutes}m" if duration_minutes > 0 else f"{duration_hours}h"

        if content_type.lower() == "beginner":
            complexity_guidance = "Focus on fundamental concepts, basic definitions, and practical applications. Keep topics simple and build foundation knowledge."
            estimated_master_topics = max(3, min(6, total_minutes // 120))
        elif content_type.lower() == "intermediate":
            complexity_guidance = "Include deeper theoretical understanding, practical applications, and some advanced concepts. Balance theory with hands-on learning."
            estimated_master_topics = max(4, min(8, total_minutes // 90))
        else:  # expert
            complexity_guidance = "Cover advanced concepts, cutting-edge research, industry best practices, and complex problem-solving. Assume strong foundational knowledge."
            estimated_master_topics = max(5, min(10, total_minutes // 60))

        subtopics_per_master = max(3, min(7, total_minutes // (estimated_master_topics * 15)))

        prompt = f"""Generate a comprehensive, industry-ready course syllabus for "{course_name}" designed to make students job-ready in today's market.

Course Details:
- Course Name: {course_name}
- Level: {content_type.title()}
- Duration: {total_hours_display} ({total_minutes} minutes total)
- Target: Industry-ready professionals

Requirements:
1. Create approximately {estimated_master_topics} master titles (major topics/modules)
2. Each master title should have {subtopics_per_master} subtitles (subtopics)
3. {complexity_guidance}
4. Focus on current industry standards and practices for {course_name}
5. Include practical, hands-on topics that employers value
6. Ensure topics are relevant to 2024-2025 industry requirements
7. Make the curriculum progressive - from basic to advanced within the level
{f'8. Consider these additional preferences: {preferences}' if preferences else ''}

Industry Focus Areas to Consider:
- Current market trends and technologies
- Industry-standard tools and frameworks
- Best practices and methodologies
- Practical application and project-based learning
- Professional skills and career readiness
- Real-world problem solving

The response should be in this exact JSON format (no markdown formatting):
{{
    "course_mastertitle_breakdown": [
        {{
            "master_title": "Master Topic Name",
            "subtitles": [
                "First subtopic that covers fundamental concepts",
                "Second subtopic about practical applications",
                "Third subtopic covering tools and techniques",
                "Fourth subtopic about industry standards",
                "Fifth subtopic on advanced concepts"
            ]
        }}
    ]
}}

Guidelines:
1. Master titles should represent major learning modules/chapters
2. Subtitles should be specific, actionable learning topics
3. Ensure logical progression from basic to advanced concepts within each master title
4. Include both theoretical knowledge and practical skills
5. Make topics relevant to current job market demands
6. Focus on skills that make students immediately employable
7. Consider certification preparation if relevant to the field
8. Include project-based learning opportunities in topic names
9. Return ONLY valid JSON without any markdown formatting or code blocks
10. Ensure the syllabus can realistically be covered in {total_hours_display}

Example for reference (but adapt to your specific course):
If course is "Data Science":
- Master Title: "Data Analysis Fundamentals" 
- Subtitles: ["Introduction to Data Types and Structures", "Statistical Analysis Basics", "Data Cleaning Techniques", "Exploratory Data Analysis", "Data Visualization Principles"]"""

        generation_config = genai.types.GenerationConfig(
            temperature=0.3,
            top_p=0.8,
            top_k=40,
            max_output_tokens=3000,
        )

        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            stream=True
        )

        return Response(stream_gemini_response(response), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@content_generate_bp.route('/api/content-generate/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@content_generate_bp.route('/api/content-generate/test', methods=['POST'])
def test_course_syllabus():
    try:
        data = request.get_json()
        course_name = data.get('course_name')
        content_type = data.get('content_type')
        duration_hours = int(data.get('duration_hours', 0))
        duration_minutes = int(data.get('duration_minutes', 0))

        total_minutes = (duration_hours * 60) + duration_minutes

        prompt = f"""Generate a course syllabus for {course_name} ({content_type} level, {total_minutes} minutes).

Return JSON format:
{{
    "course_mastertitle_breakdown": [
        {{
            "master_title": "Topic Name",
            "subtitles": ["Subtopic 1", "Subtopic 2", "Subtopic 3"]
        }}
    ]
}}"""

        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt)

        clean_response = response.text.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:]
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()

        return jsonify(json.loads(clean_response))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@content_generate_bp.route('/api/content-generate/detailed-content', methods=['POST'])
def generate_detailed_content():
    """
    Generate detailed content for each subtitle in the course syllabus
    """
    try:
        data = request.get_json()
        course_data = data.get('course_data')
        course_name = data.get('course_name', 'General Course')
        course_id = data.get('course_id')
        
        if not course_data or 'course_mastertitle_breakdown' not in course_data:
            return jsonify({'error': 'Invalid course data format'}), 400
        
        if not course_id:
            return jsonify({'error': 'course_id is required'}), 400
        
        # Generate a unique task ID
        task_id = f"task_{int(time.time())}_{threading.get_ident()}"
        
        # Initialize the task
        background_tasks[task_id] = {
            "status": "starting",
            "progress": 0,
            "total_items": 0,
            "completed_items": 0,
            "data": []
        }
        
        # Start background processing with course_id
        thread = threading.Thread(
            target=process_course_content_background,
            args=(task_id, course_data, course_name, course_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'message': 'Content generation started in background',
            'status': 'processing',
            'course_id': course_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@content_generate_bp.route('/api/content-generate/detailed-content/status/<task_id>', methods=['GET'])
def get_content_generation_status(task_id):
    """
    Get the status of content generation task
    """
    try:
        if task_id not in background_tasks:
            return jsonify({'error': 'Task not found'}), 404
        
        task_status = background_tasks[task_id]
        return jsonify(task_status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@content_generate_bp.route('/api/content-generate/detailed-content/result/<task_id>', methods=['GET'])
def get_content_generation_result(task_id):
    """
    Get the final result of content generation task
    """
    try:
        if task_id not in background_tasks:
            return jsonify({'error': 'Task not found'}), 404
        
        task_status = background_tasks[task_id]
        
        if task_status.get('status') == 'completed':
            # Return the structured data
            return jsonify({
                'status': 'completed',
                'data': task_status.get('data', []),
                'total_items': task_status.get('total_items', 0),
                'completed_items': task_status.get('completed_items', 0)
            })
        elif task_status.get('status') == 'error':
            return jsonify({
                'status': 'error',
                'error': task_status.get('error', 'Unknown error')
            }), 500
        else:
            return jsonify({
                'status': 'processing',
                'progress': task_status.get('progress', 0),
                'total_items': task_status.get('total_items', 0),
                'completed_items': task_status.get('completed_items', 0)
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@content_generate_bp.route('/api/content-generate/progress/<course_id>', methods=['GET'])
def get_course_content_progress(course_id):
    """
    Get content generation progress from database for a specific course
    """
    try:
        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        query = """
        SELECT task_id, status, updated_date 
        FROM lms.course_content_progress 
        WHERE course_id = %s 
        ORDER BY updated_date DESC 
        LIMIT 1
        """
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (course_id,))
            result = cursor.fetchone()
            
        conn.close()
        
        if result:
            return jsonify({
                'course_id': course_id,
                'task_id': result['task_id'],
                'status': result['status'],
                'updated_date': str(result['updated_date'])
            })
        else:
            return jsonify({
                'course_id': course_id,
                'status': 'no_progress_found'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@content_generate_bp.route('/api/content-generate/content/<course_id>', methods=['GET'])
def get_generated_course_content(course_id):
    """
    Get generated course content from database for a specific course
    """
    try:
        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        query = """
        SELECT 
            course_mastertitle_breakdown_id,
            course_mastertitle_breakdown,
            course_subtitle_id,
            course_subtitle,
            subtitle_content,
            subtitle_code,
            subtitle_help_text,
            helpfull_links
        FROM lms.course_content_transaction 
        WHERE course_id = %s 
        ORDER BY course_mastertitle_breakdown_id, course_subtitle_id
        """
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (course_id,))
            results = cursor.fetchall()
            
        conn.close()
        
        if results:
            return jsonify({
                'course_id': course_id,
                'content_count': len(results),
                'data': results
            })
        else:
            return jsonify({
                'course_id': course_id,
                'content_count': 0,
                'data': []
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@content_generate_bp.route('/api/content-generate/pending-approval', methods=['GET'])
def get_pending_approval_courses():
    """
    Get all generated courses that are in completed or processing state for approval
    """
    try:
        conn = get_db_connection(DB_CONFIG)
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        query = """
        SELECT 
            ccp.course_id,
            ccp.status,
            ccp.task_id,
            ccp.updated_date,
            cm.course_name,
            cm.course_short_description,
            cm.course_duration_hours,
            cm.course_duration_minutes,
            cm.language,
            cm.rating,
            cm.course_profile_image
        FROM lms.course_content_progress as ccp
        LEFT JOIN lms.course_master as cm ON cm.course_id = ccp.course_id
        WHERE ccp.status = 'completed' OR ccp.status LIKE 'processing%'
        ORDER BY ccp.updated_date DESC
        """
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
        conn.close()
        
        # Group results by course_id to avoid duplicates
        courses = {}
        for row in results:
            course_id = row['course_id']
            if course_id not in courses:
                courses[course_id] = {
                    'course_id': course_id,
                    'course_name': row['course_name'],
                    'course_short_description': row['course_short_description'],
                    'course_duration_hours': row['course_duration_hours'],
                    'course_duration_minutes': row['course_duration_minutes'],
                    'language': row['language'],
                    'rating': row['rating'],
                    'course_profile_image': row['course_profile_image'],
                    'latest_status': row['status'],
                    'latest_task_id': row['task_id'],
                    'latest_updated_date': str(row['updated_date']),
                    'all_statuses': []
                }
            
            # Add status to the list if not already present
            status_info = {
                'status': row['status'],
                'task_id': row['task_id'],
                'updated_date': str(row['updated_date'])
            }
            if status_info not in courses[course_id]['all_statuses']:
                courses[course_id]['all_statuses'].append(status_info)
        
        # Convert to list and sort by latest updated date
        course_list = list(courses.values())
        course_list.sort(key=lambda x: x['latest_updated_date'], reverse=True)
        
        return jsonify({
            'message': 'Pending approval courses retrieved successfully',
            'total_courses': len(course_list),
            'data': course_list
        })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def ensure_tables_exist(conn):
    """
    Ensure both course_content_transaction and course_content_progress tables exist with correct structure
    """
    try:
        with conn.cursor() as cursor:
            # Create course_content_transaction table
            course_content_table = """
            CREATE TABLE IF NOT EXISTS lms.course_content_transaction
            (
                course_content_id SERIAL PRIMARY KEY,
                course_id integer NOT NULL,
                course_mastertitle_breakdown_id integer NOT NULL,
                course_mastertitle_breakdown character varying(100),
                course_subtitle_id integer NOT NULL,
                course_subtitle character varying(100),
                subtitle_content text,
                subtitle_code text,
                subtitle_help_text text,
                helpfull_links text
            );
            """
            cursor.execute(course_content_table)
            
            # Create course_content_progress table
            progress_table = """
            CREATE TABLE IF NOT EXISTS lms.course_content_progress
            (
                course_id integer NOT NULL,
                task_id character varying(100) NOT NULL,
                status character varying(50) NOT NULL,
                updated_date timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(progress_table)
            
            conn.commit()
            print("Database tables ensured to exist")
    except Exception as e:
        conn.rollback()
        print(f"Error ensuring tables exist: {str(e)}")
        raise