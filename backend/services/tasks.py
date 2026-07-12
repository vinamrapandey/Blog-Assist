from backend.services.llm_manager import LLMHandler
from backend.services.wp_manager import WordPressHandler
from backend.core.scheduler import log_message
from backend.core.database import SessionLocal
from backend.models.models import PostRecord

def run_generation_cycle(provider, key, topic, count, url, user, password, status="draft"):
    try:
        # 1. Generate Content
        log_message(f"Generating content for topic: {topic}...")
        llm = LLMHandler(provider, key)
        blog_data = llm.generate_blog(topic, count)
        
        if "error" in blog_data:
            log_message(f"LLM Error: {blog_data['error']}")
            return

        title = blog_data.get("title", "No Title")
        content = blog_data.get("content", "")
        log_message(f"Generated: {title}")

        # 2. Publish to WordPress
        log_message("Publishing to WordPress...")
        wp = WordPressHandler(url, user, password)
        result = wp.publish_post(title, content, status=status)
        
        if "id" in result:
             log_message(f"Success! Post ID: {result['id']} (Status: {result.get('status')})")
             # Save to DB
             db = SessionLocal()
             try:
                 new_post = PostRecord(title=title, topic=topic, status=result.get('status', status))
                 db.add(new_post)
                 db.commit()
             finally:
                 db.close()
        else:
             log_message(f"WordPress Error: {result}")

    except Exception as e:
        log_message(f"Critical Error: {str(e)}")
