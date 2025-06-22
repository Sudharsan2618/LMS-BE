#!/usr/bin/env python3
"""
Test script for content generation API with database integration
"""

import requests
import json
import time

# API base URL - adjust as needed
BASE_URL = "http://localhost:5000"

def test_content_generation():
    """Test the complete content generation flow"""
    
    # Test data
    test_course_data = {
        "course_id": 1,  # Use an existing course ID
        "course_name": "Python Programming",
        "course_data": {
            "course_mastertitle_breakdown": [
                {
                    "master_title": "Introduction to Python",
                    "subtitles": [
                        "What is Python?",
                        "Python Installation",
                        "First Python Program"
                    ]
                },
                {
                    "master_title": "Python Basics",
                    "subtitles": [
                        "Variables and Data Types",
                        "Operators",
                        "Control Structures"
                    ]
                }
            ]
        }
    }
    
    print("1. Starting content generation...")
    
    # Start content generation
    response = requests.post(
        f"{BASE_URL}/api/content-generate/detailed-content",
        json=test_course_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code != 200:
        print(f"Error starting content generation: {response.text}")
        return
    
    result = response.json()
    task_id = result.get('task_id')
    course_id = result.get('course_id')
    
    print(f"Task ID: {task_id}")
    print(f"Course ID: {course_id}")
    print("Content generation started in background...")
    
    # Monitor progress
    print("\n2. Monitoring progress...")
    max_attempts = 30  # 5 minutes max
    attempt = 0
    
    while attempt < max_attempts:
        # Check progress from database
        progress_response = requests.get(f"{BASE_URL}/api/content-generate/progress/{course_id}")
        
        if progress_response.status_code == 200:
            progress_data = progress_response.json()
            status = progress_data.get('status', 'unknown')
            print(f"Progress: {status}")
            
            if 'completed' in status:
                print("Content generation completed!")
                break
            elif 'error' in status:
                print(f"Error occurred: {status}")
                break
        
        time.sleep(10)  # Wait 10 seconds before next check
        attempt += 1
    
    if attempt >= max_attempts:
        print("Timeout waiting for completion")
        return
    
    # Get generated content
    print("\n3. Retrieving generated content...")
    content_response = requests.get(f"{BASE_URL}/api/content-generate/content/{course_id}")
    
    if content_response.status_code == 200:
        content_data = content_response.json()
        print(f"Generated {content_data.get('content_count', 0)} content items")
        
        # Display some sample content
        for item in content_data.get('data', [])[:3]:  # Show first 3 items
            print(f"\nMaster Title {item['course_mastertitle_breakdown_id']}: {item['course_mastertitle_breakdown']}")
            print(f"Subtitle {item['course_subtitle_id']}: {item['course_subtitle']}")
            print(f"Content preview: {item['subtitle_content'][:100]}...")
    else:
        print(f"Error retrieving content: {content_response.text}")

if __name__ == "__main__":
    test_content_generation() 