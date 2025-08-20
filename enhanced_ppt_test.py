#!/usr/bin/env python3
"""
Enhanced PPT generation test with richer content
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.models.ppt_generation_model import generate_ppt_for_course
    print("✅ Successfully imported enhanced PPT generation function")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def check_aws_credentials():
    """Check if AWS credentials are loaded"""
    print("🔍 Checking AWS credentials...")
    
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION')
    aws_bucket = os.getenv('AWS_S3_BUCKET_NAME')
    
    print(f"   AWS_ACCESS_KEY_ID: {'✅ Found' if aws_access_key else '❌ Not found'}")
    print(f"   AWS_SECRET_ACCESS_KEY: {'✅ Found' if aws_secret_key else '❌ Not found'}")
    print(f"   AWS_REGION: {aws_region if aws_region else '❌ Not found (will use default: us-east-1)'}")
    print(f"   AWS_S3_BUCKET_NAME: {aws_bucket if aws_bucket else '❌ Not found'}")
    
    if aws_access_key and aws_secret_key and aws_bucket:
        print("✅ All required AWS credentials found!")
        return True
    else:
        print("❌ Missing required AWS credentials")
        return False

def main():
    print("🚀 Enhanced PPT Generation Test")
    print("=" * 45)
    
    # Check AWS credentials first
    check_aws_credentials()
    print("-" * 45)
    
    # Test configuration
    course_id = 1
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"enhanced_course_{course_id}_presentation_{timestamp}.pptx"
    
    # Create output directory
    os.makedirs("generated_presentations", exist_ok=True)
    output_path = os.path.join("generated_presentations", output_file)
    
    print(f"📋 Course ID: {course_id}")
    print(f"📄 Output file: {output_path}")
    print(f"📁 Template: Using professional LMS template")
    print(f"📊 Max slides: 30 (enhanced from 20)")
    print("-" * 45)
    
    try:
        print("🚀 Starting enhanced PPT generation...")
        
        # Call the enhanced function with S3 upload
        result = generate_ppt_for_course(
            course_id=course_id,
            filename=f"enhanced_course_{course_id}_presentation_{timestamp}",
            template_path=None,  # Use default template
            max_slides=30,  # Increased slide count
            upload_to_cloud=True  # Enable S3 upload
        )
        
        print("✅ Enhanced PPT generation completed!")
        print(f"📄 Generated file: {result['filename']}")
        
        # Check results
        local_path = result['local_path']
        
        # Show S3 URL if uploaded
        if result['cloud_url']:
            print(f"☁️  S3 URL: {result['cloud_url']}")
            print("🌐 PPT is now publicly accessible via the S3 URL!")
            
            if local_path is None:
                print("💾 Local file: Cleaned up after S3 upload")
            else:
                print(f"💾 Local path: {local_path}")
                if os.path.exists(local_path):
                    file_size = os.path.getsize(local_path)
                    print(f"📊 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        else:
            print("⚠️  S3 upload was skipped or failed")
            if local_path and os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                print(f"📊 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                print(f"💾 Local path: {local_path}")
            else:
                print("❌ No file was created!")
                return
        
        print("\n🎉 SUCCESS! Enhanced PowerPoint with richer content generated!")
        print("\n📋 Enhanced features include:")
        print("   • Course overview slide")
        print("   • Module header slides with learning objectives")
        print("   • Detailed content with emojis and formatting")
        print("   • Code examples and tips")
        print("   • Resource links")
        print("   • Professional styling")
        print("   • AWS S3 cloud storage integration")
        print("   • Automatic database update with PPT URL")
            
    except Exception as e:
        print(f"❌ Error during enhanced PPT generation:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        
        # Show traceback for debugging
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
