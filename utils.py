import json
import re

def parse_json_response(response_content: str) -> dict:
    """
    Parses JSON from a string that might contain Markdown code blocks.
    """
    try:
        # Strip code blocks like ```json ... ```
        if "```json" in response_content:
            response_content = response_content.split("```json")[1].split("```")[0]
        elif "```" in response_content:
            response_content = response_content.split("```")[1].split("```")[0]
        
        return json.loads(response_content.strip())
    except json.JSONDecodeError:
        print(f"JSON Decode Error. Raw content: {response_content}")
        return {}
    except Exception as e:
        print(f"Parse Error: {e}")
        return {}