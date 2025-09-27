import json
import re


def fix_json_quotes(json_string):
    """
    General function to fix unescaped quotes in JSON string values.
    This works by finding JSON string patterns and escaping internal quotes.
    """
    # Pattern to match JSON string values: "key": "value with possible "quotes" inside"
    # This captures the key, colon, opening quote, content, and closing quote
    pattern = r'("[\w\d]+"\s*:\s*")([^"]*(?:"[^"]*"[^"]*)*?)("\s*[,}])'
    
    def escape_internal_quotes(match):
        prefix = match.group(1)  # "key": "
        content = match.group(2)  # the content that may have unescaped quotes
        suffix = match.group(3)   # " followed by , or }
        
        # Escape any quotes in the content
        escaped_content = content.replace('"', '\\"')
        
        return prefix + escaped_content + suffix
    
    # Apply the fix
    fixed_string = re.sub(pattern, escape_internal_quotes, json_string, flags=re.DOTALL)
    
    return fixed_string


def safe_json_loads(json_string):
    """
    Safely load JSON by attempting to fix common quote escaping issues.
    """
    try:
        # First try to load as-is
        return json.loads(json_string)
    except json.JSONDecodeError:
        # If it fails, try to fix quote issues
        try:
            fixed_string = fix_json_quotes(json_string)
            return json.loads(fixed_string)
        except json.JSONDecodeError as e:
            print(f"Could not parse JSON even after attempting fixes: {e}")
            print("Fixed string:")
            print(fixed_string)
            raise
