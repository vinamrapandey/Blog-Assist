import requests
import base64
import json

class WordPressHandler:
    def __init__(self, url, username, password):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.auth_header = self._get_auth_header()

    def _get_auth_header(self):
        credentials = f"{self.username}:{self.password}"
        token = base64.b64encode(credentials.encode()).decode('utf-8')
        return {'Authorization': f'Basic {token}'}

    def validate_connection(self):
        """
        Validates the WordPress connection and credentials by fetching the current user profile.
        """
        endpoint = f"{self.url}/wp-json/wp/v2/users/me"
        try:
            response = requests.get(endpoint, headers=self.auth_header, timeout=10)
            response.raise_for_status()
            return {"status": "success", "user": response.json().get('name')}
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if response is not None:
                try:
                    error_msg = response.json().get('message', error_msg)
                except:
                    error_msg = response.text or error_msg
            return {"status": "error", "message": f"WordPress connection failed: {error_msg}"}

    def publish_post(self, title, content, status="draft", categories=None, tags=None):
        """
        Publishes a post to WordPress.
        """
        endpoint = f"{self.url}/wp-json/wp/v2/posts"
        
        data = {
            'title': title,
            'content': content,
            'status': status
        }
        
        if categories:
            # Note: Categories need to be IDs, not names. 
            # Ideally we'd look them up, but for MVP we might skip or assume existing IDs.
            # For this version, we'll omit category lookup implementation to keep it simple,
            # or we could try to create/find. Let's keep it simple for now.
            pass

        try:
            response = requests.post(endpoint, headers=self.auth_header, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "details": response.text if response else "No response"}
