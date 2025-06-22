# Content Generation with Database Integration

This document describes the enhanced content generation functionality that now stores generated content in the database.

## Overview

The content generation system has been updated to:
1. Store generated content in the `lms.course_content_transaction` table
2. Track generation progress in the `lms.course_content_progress` table
3. Implement proper ID sequencing for master titles and subtitles
4. Provide background processing with progress tracking

## Database Tables

### course_content_transaction Table
```sql
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
```

### course_content_progress Table
```sql
CREATE TABLE IF NOT EXISTS lms.course_content_progress
(
    course_id integer NOT NULL,
    task_id character varying(100) NOT NULL,
    status character varying(50) NOT NULL,
    updated_date timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Note**: The `task_id` is stored as a string (varchar) to accommodate the generated task IDs like "task_1750566835_14132".

## ID Sequencing

The system implements the following ID sequencing:
- **course_mastertitle_breakdown_id**: Starts from 1 for each course and increments sequentially
- **course_subtitle_id**: Starts from 1 for each master title and increments sequentially

Example:
```
course_id | course_mastertitle_breakdown_id | course_mastertitle_breakdown | course_subtitle_id | course_subtitle
1         | 1                               | "Introduction to Python"     | 1                  | "What is Python?"
1         | 1                               | "Introduction to Python"     | 2                  | "Python Installation"
1         | 2                               | "Python Basics"              | 1                  | "Variables and Data Types"
```

## API Endpoints

### 1. Generate Detailed Content
**POST** `/api/content-generate/detailed-content`

Request body:
```json
{
    "course_id": 1,
    "course_name": "Python Programming",
    "course_data": {
        "course_mastertitle_breakdown": [
            {
                "master_title": "Introduction to Python",
                "subtitles": [
                    "What is Python?",
                    "Python Installation"
                ]
            }
        ]
    }
}
```

Response:
```json
{
    "task_id": "task_1234567890_12345",
    "message": "Content generation started in background",
    "status": "processing",
    "course_id": 1
}
```

### 2. Check Generation Progress
**GET** `/api/content-generate/progress/{course_id}`

Response:
```json
{
    "course_id": 1,
    "task_id": "task_1234567890_12345",
    "status": "processing_50%",
    "updated_date": "2024-01-15T10:30:00"
}
```

### 3. Get Generated Content
**GET** `/api/content-generate/content/{course_id}`

Response:
```json
{
    "course_id": 1,
    "content_count": 6,
    "data": [
        {
            "course_mastertitle_breakdown_id": 1,
            "course_mastertitle_breakdown": "Introduction to Python",
            "course_subtitle_id": 1,
            "course_subtitle": "What is Python?",
            "subtitle_content": "Python is a high-level programming language...",
            "subtitle_code": "",
            "subtitle_help_text": "Python is known for its simplicity...",
            "helpfull_links": "https://python.org,https://docs.python.org"
        }
    ]
}
```

### 4. Get Task Status (Legacy)
**GET** `/api/content-generate/detailed-content/status/{task_id}`

### 5. Get Task Result (Legacy)
**GET** `/api/content-generate/detailed-content/result/{task_id}`

### 6. Get Pending Approval Courses
**GET** `/api/content-generate/pending-approval`

Returns all courses that are in completed or processing state for approval.

Response:
```json
{
    "message": "Pending approval courses retrieved successfully",
    "total_courses": 3,
    "data": [
        {
            "course_id": 1,
            "course_name": "Python Programming",
            "course_short_description": "Learn Python from scratch",
            "course_duration_hours": 20,
            "course_duration_minutes": 0,
            "language": "English",
            "rating": 4.5,
            "course_profile_image": "python.jpg",
            "latest_status": "completed",
            "latest_task_id": "task_1234567890_12345",
            "latest_updated_date": "2024-01-15T10:30:00",
            "all_statuses": [
                {
                    "status": "processing",
                    "task_id": "task_1234567890_12345",
                    "updated_date": "2024-01-15T10:25:00"
                },
                {
                    "status": "completed",
                    "task_id": "task_1234567890_12345",
                    "updated_date": "2024-01-15T10:30:00"
                }
            ]
        }
    ]
}
```

### 7. Approve or Reject Course
**POST** `/api/content-generate/approve-course`

Request body:
```json
{
    "course_id": 1,
    "task_id": "task_1234567890_12345",
    "action": "approve",
    "comments": "Content looks good, approved for production"
}
```

Response:
```json
{
    "message": "Course approved successfully",
    "course_id": 1,
    "task_id": "task_1234567890_12345",
    "status": "approved: Content looks good, approved for production"
}
```

**Note**: `action` can be either "approve" or "reject". `comments` is optional.

## Background Processing

The content generation runs in the background using threading:

1. **Initialization**: Creates a unique task ID and initializes progress tracking
2. **Table Creation**: Ensures database tables exist with correct structure
3. **Processing**: Generates content for each subtitle using Gemini AI
4. **Database Storage**: Stores each generated content item in the database
5. **Progress Updates**: Updates progress in both memory and database
6. **Completion**: Marks the task as completed when all content is generated

## Error Handling

- Database connection failures are handled gracefully
- Table creation is automatic if tables don't exist
- Individual subtitle generation failures don't stop the entire process
- Error status is stored in the database for monitoring
- Failed content items are marked with error messages
- Transaction rollback on database errors

## Testing

Use the provided test script to verify the functionality:

```bash
python test_content_generation.py
```

Make sure to:
1. Update the `BASE_URL` in the test script
2. Use an existing `course_id` in your database
3. The system will automatically create tables if they don't exist

## Dependencies

- Flask
- psycopg2
- google-generativeai
- python-dotenv

## Environment Variables

Make sure to set:
- `GEMINI_API_KEY`: Your Google Gemini API key
- Database connection details in `app/config/database.py`

## Troubleshooting

### Common Issues:

1. **Database Connection Errors**: Check your database configuration in `app/config/database.py`
2. **Table Structure Issues**: The system automatically creates tables with the correct structure
3. **Task ID Type Errors**: Fixed - task_id is now stored as varchar(100) instead of integer
4. **Transaction Errors**: The system includes proper error handling and rollback mechanisms

## Database Schema Notes

- **Content Storage**: Generated content is stored in `lms.course_content_transaction` table
- **Progress Tracking**: Status updates are stored in `lms.course_content_progress` table
- **ID Sequencing**: Proper sequential IDs are maintained for both master titles and subtitles
- **Transaction Safety**: All database operations include proper transaction handling 