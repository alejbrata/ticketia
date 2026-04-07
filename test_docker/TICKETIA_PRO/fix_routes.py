import os
import re

def fix_routes_file():
    filepath = os.path.join(os.path.dirname(__file__), 'routes', 'web.py')
    pattern = re.compile(r"url_for\(['\"]([^'\"]+)['\"]")
    
    def replacer(match):
        endpoint = match.group(1)
        if endpoint == 'static' or endpoint.startswith('web.'):
            return match.group(0) # Keep as is
        else:
            delimiter = match.group(0)[8] # The quote character used
            return f"url_for({delimiter}web.{endpoint}{delimiter}"
            
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_content = pattern.sub(replacer, content)
    
    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")
    else:
        print("No changes needed.")
        
if __name__ == "__main__":
    fix_routes_file()
