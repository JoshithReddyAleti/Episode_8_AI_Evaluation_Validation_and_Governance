"""helpers.py — Shared utilities."""
import hashlib, json
def hash_content(text):
    """Hash content for audit logging without exposing raw data."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]
def safe_json_parse(text):
    try: return json.loads(text.replace("```json","").replace("```","").strip())
    except: return None
