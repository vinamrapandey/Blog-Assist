from backend.services.llm_manager import LLMHandler
from backend.services.wp_manager import WordPressHandler
from backend.core.scheduler import log_message
from backend.core.database import SessionLocal
from backend.models.models import PostRecord

def run_generation_cycle(provider, key, topic, count, url, user, password, status="draft", user_id: int = None):
    try:
        log_message(f"Starting auto-generation cycle for topic: {topic}", user_id=user_id)
        
        # 1. Generate Content
        llm = LLMHandler(provider, key)
        generated_data = llm.generate_post(topic, count)
        if "error" in generated_data:
            raise Exception(generated_data["error"])
        
        title = generated_data.get("title", "Draft Title")
        content = generated_data.get("content", "Draft Content")
        log_message("Content generated successfully.", user_id=user_id)
        
        # 2. Publish to WordPress
        wp = WordPressHandler(url, user, password)
        result = wp.publish_post(title, content, status)
        
        if "id" in result:
             log_message(f"Success! Post ID: {result['id']} (Status: {result.get('status')})", user_id=user_id)
             # Save to DB
             db = SessionLocal()
             try:
                 new_post = PostRecord(title=title, topic=topic, status=result.get('status', status), user_id=user_id)
                 db.add(new_post)
                 db.commit()
             finally:
                 db.close()
        else:
             log_message(f"WordPress Error: {result}", user_id=user_id)

    except Exception as e:
        log_message(f"Error in cycle: {str(e)}", user_id=user_id)
