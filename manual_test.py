from llm_manager import LLMHandler
from wp_manager import WordPressHandler
import sys
import traceback

# Provided Credentials (TEMPORARY)
API_KEY = "AIzaSyCDERQtL2Ho-wBgjMJRaUEpY6HgEPq3vJE"
WP_URL = "https://deepskyblue-penguin-198436.hostingersite.com/"
WP_USER = "test" 
WP_PASS = "Test@123"
TOPIC = "Business"

def test_workflow():
    print("--------------------------------------------------", flush=True)
    print("STARTING MANUAL VERIFICATION", flush=True)
    print("--------------------------------------------------", flush=True)

    # 1. Test LLM Generation with Gemini
    print(f"\n[1/2] Testing Google Gemini Generation (Topic: {TOPIC})...", flush=True)
    try:
        llm = LLMHandler("Google Gemini", API_KEY)
        blog_data = llm.generate_blog(TOPIC, 300)
        
        if "error" in blog_data:
            print(f"❌ LLM GENERATION FAILED: {blog_data['error']}", flush=True)
            # Proceed anyway to test WP if possible, but usually we stop.
        else:
            title = blog_data.get("title", "No Title")
            content = blog_data.get("content", "")
            print(f"✅ Generated Title: {title}", flush=True)
            print(f"✅ Generated Content Length: {len(content)} chars", flush=True)
            
            # 2. Test WordPress Publishing
            print(f"\n[2/2] Testing WordPress Publishing to {WP_URL}...", flush=True)
            try:
                wp = WordPressHandler(WP_URL, WP_USER, WP_PASS)
                result = wp.publish_post(title, content, status="draft")
                
                if "id" in result:
                     print(f"✅ SUCCESS! Post Created. ID: {result['id']}", flush=True)
                     print(f"   Link: {result.get('link', 'N/A')}", flush=True)
                     print(f"   Status: {result.get('status')}", flush=True)
                else:
                     print(f"❌ WORDPRESS PUBLISH FAILED: {result}", flush=True)
                     
            except Exception as e:
                print(f"❌ CRITICAL WORDPRESS ERROR: {e}", flush=True)
                traceback.print_exc()

    except Exception as e:
        print(f"❌ CRITICAL LLM ERROR: {e}", flush=True)
        traceback.print_exc()

    print("--------------------------------------------------", flush=True)
    print("VERIFICATION COMPLETE", flush=True)
    print("--------------------------------------------------", flush=True)

if __name__ == "__main__":
    test_workflow()
