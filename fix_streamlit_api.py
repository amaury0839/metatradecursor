#!/usr/bin/env python
"""Fix Streamlit API deprecations"""
import re
import os

files_to_fix = [
    'app/ui/pages_database_analytics.py',
    'app/ui/pages_history.py'
]

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        print(f'⚠️ {filepath} not found')
        continue
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Replace width='stretch' with use_container_width=True
    content = re.sub(r'width\s*=\s*["\']stretch["\']', 'use_container_width=True', content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        # Count changes
        changes = len(re.findall(r'use_container_width=True', content))
        print(f'✅ Fixed {filepath} - {changes} changes')
    else:
        print(f'⚠️ {filepath} had no changes')
