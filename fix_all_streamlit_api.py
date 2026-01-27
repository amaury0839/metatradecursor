#!/usr/bin/env python
"""Fix all Streamlit API deprecations in UI files"""
import re
import os
from pathlib import Path

def fix_streamlit_api_in_file(filepath):
    """Fix Streamlit API issues in a single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Replace use_container_width=True with width='stretch'
    content = re.sub(
        r'use_container_width\s*=\s*True',
        'width="stretch"',
        content
    )
    
    # Replace use_container_width=False with width='content'
    content = re.sub(
        r'use_container_width\s*=\s*False',
        'width="content"',
        content
    )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Find all Python files in app/ui
ui_dir = Path('app/ui')
fixed_count = 0

for py_file in ui_dir.glob('*.py'):
    if fix_streamlit_api_in_file(str(py_file)):
        print(f'✅ Fixed {py_file.name}')
        fixed_count += 1
    else:
        print(f'⚠️  {py_file.name} - no changes needed')

print(f'\n✅ Total files fixed: {fixed_count}')
