import google.generativeai as genai
from openai import OpenAI
import json
import re

class LLMHandler:
    def __init__(self, provider, api_key, model_name=None):
        self.provider = provider
        self.api_key = api_key
        # Set default models if not provided
        if provider == "Gemini" or provider == "Google Gemini":
            self.model_name = model_name or "gemini-flash-latest"
            genai.configure(api_key=self.api_key)




        elif provider == "OpenAI":
            self.model_name = model_name or "gpt-4o-mini"
            self.client = OpenAI(api_key=self.api_key)
        elif provider == "Simulated":
            self.model_name = "simulated"


    def test_connection(self):
        if self.provider == "Simulated":
            return {"status": "success"}
            
        try:
            if self.provider == "Gemini" or self.provider == "Google Gemini":
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content("Say OK")
                if response.text:
                    return {"status": "success"}
            elif self.provider == "OpenAI":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": "Say OK"}],
                    max_tokens=5
                )
                if response.choices:
                    return {"status": "success"}
            return {"status": "error", "message": "Unknown error validating API key."}
        except Exception as e:
            return {"status": "error", "message": f"AI API Key Validation Failed: {str(e)}"}

    def generate_post(self, topic, word_count, tone="Professional", guidelines=None):
        """
        Generates a blog post and returns a JSON object with 'title' and 'content'.
        """
        guidelines_text = ""
        if guidelines:
            guidelines_text = "\\n**CRITICAL STYLE GUIDELINES (LEARNED FROM USER PREFERENCES):**\\n"
            for g in guidelines:
                guidelines_text += f"- {g}\\n"
                
        prompt = f"""
        You are an expert blog writer. Write a comprehensive, engaging blog post.
        
        **Configuration:**
        - **Topic/Niche:** {topic}
        - **Approximate Word Count:** {word_count} words
        - **Tone:** {tone}
        {guidelines_text}
        
        **Requirements:**
        1. Write a catchy, SEO-friendly title.
        2. Write the full blog content in HTML format (use <h2>, <p>, <ul>, <li>, etc., but NO <html>, <head>, or <body> tags).
        3. Ensure the content is well-structured with headings and paragraphs.
        
        **Output Format:**
        You must strictly output ONLY a valid JSON object in the following format, with no markdown code fences or other text:
        {{
            "title": "Your Web-Optimized Title Here",
            "content": "<h2>Introduction</h2><p>Your HTML content here...</p>"
        }}
        """

        try:
            if self.provider == "Gemini" or self.provider == "Google Gemini":
                return self._generate_gemini(prompt)

            elif self.provider == "OpenAI":
                return self._generate_openai(prompt)
            elif self.provider == "Simulated":
                return self._generate_simulated(prompt, topic)

            else:
                raise ValueError("Invalid LLM Provider")
        except Exception as e:
            return {"error": str(e)}

    def process_feedback_and_rewrite(self, title, content, feedback, tone="Professional", guidelines=None):
        guidelines_text = ""
        if guidelines:
            guidelines_text = "\\n**Existing Style Guidelines:**\\n"
            for g in guidelines:
                guidelines_text += f"- {g}\\n"
                
        prompt = f"""
        You are an expert blog writer. The user has provided feedback on a drafted blog post.
        
        **Original Draft:**
        Title: {title}
        Content: {content}
        
        **User Feedback:** {feedback}
        {guidelines_text}
        
        **Task 1: Rewrite the Post**
        Rewrite the draft strictly adhering to the user's feedback and any existing guidelines. 
        Format content as HTML (no <html> or <body> tags).
        
        **Task 2: Extract a RAG Rule**
        Extract a single, generalized style rule from the user's feedback that can be applied to ALL future posts (e.g. "Do not use the word 'delve'", "Always use a humorous tone", "Keep sentences short"). Keep it under 15 words.
        
        **Output Format:**
        You must output ONLY a valid JSON object:
        {{
            "title": "Rewritten Title",
            "content": "Rewritten HTML content...",
            "new_rule": "The extracted generalized rule"
        }}
        """
        try:
            if self.provider == "Gemini" or self.provider == "Google Gemini":
                return self._generate_gemini(prompt)
            elif self.provider == "OpenAI":
                return self._generate_openai(prompt)
            elif self.provider == "Simulated":
                return {
                    "title": f"Rewritten: {title}", 
                    "content": f"<p>Simulated rewrite incorporating: {feedback}</p>{content}",
                    "new_rule": f"Simulated rule from: {feedback}"
                }
            else:
                raise ValueError("Invalid LLM Provider")
        except Exception as e:
            return {"error": str(e)}

    def _generate_gemini(self, prompt):
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt)
        return self._clean_and_parse_json(response.text)

    def _generate_openai(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return self._clean_and_parse_json(response.choices[0].message.content)


    def _generate_simulated(self, prompt, topic):
        # Simulate a delay
        import time
        time.sleep(2)
        return {
            "title": f"Simulated Blog Post: {topic}",
            "content": f"<h2>Introduction to {topic}</h2><p>This is a simulated blog post generated without an API key. In a real scenario, this would be comprehensive content about {topic}.</p><h3>Key Concepts</h3><ul><li>Point 1</li><li>Point 2</li></ul><p>Conclusion: This is just a test.</p>"
        }


    def _clean_and_parse_json(self, text):
        # Remove markdown code fences if present
        text = re.sub(r"```json", "", text)
        text = re.sub(r"```", "", text)
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: Try to find JSON structure
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end])
                except:
                    pass
            return {"error": "Failed to parse JSON response", "raw_text": text}
