#!/usr/bin/env python3
"""Fix require_role decorator usage across all API files"""

import re
from pathlib import Path

def fix_file(filepath):
    """Fix require_role usage in a single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Pattern 1: @require_role([...]) decorator above function
    # Replace with Depends(require_role(...)) in function signature
    
    # Find all occurrences
    pattern = r'@require_role\(\[(.*?)\]\)\s*\n\s*def\s+(\w+)\s*\((.*?current_user:\s*User\s*=\s*Depends\(get_current_user\))'
    
    def replacer(match):
        roles = match.group(1)
        func_name = match.group(2)
        params_before = match.group(3)
        
        # Convert ["Role1", "Role2"] to "Role1", "Role2"
        roles_clean = roles.replace('"', '').replace("'", "")
        roles_args = ', '.join([f'"{r.strip()}"' for r in roles_clean.split(',')])
        
        # Replace get_current_user with require_role
        new_params = params_before.replace(
            'current_user: User = Depends(get_current_user)',
            f'current_user: User = Depends(require_role({roles_args}))'
        )
        
        return f'def {func_name}({new_params}current_user: User = Depends(require_role({roles_args}))'
    
    # Simpler approach: just remove the decorator line and fix the Depends
    lines = content.split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a require_role decorator line
        if '@require_role([' in line:
            # Extract roles
            roles_match = re.search(r'@require_role\(\[(.*?)\]\)', line)
            if roles_match:
                roles_str = roles_match.group(1)
                # Convert ["Role1", "Role2"] to "Role1", "Role2"
                roles_clean = roles_str.replace('"', '').replace("'", "")
                roles_args = ', '.join([f'"{r.strip()}"' for r in roles_clean.split(',')])
                
                # Skip this decorator line
                i += 1
                
                # Find the function definition and fix it
                while i < len(lines):
                    if 'def ' in lines[i]:
                        # Found function, now find current_user parameter
                        func_lines = [lines[i]]
                        i += 1
                        
                        # Collect function signature lines
                        while i < len(lines) and '):' not in lines[i-1]:
                            func_lines.append(lines[i])
                            i += 1
                        
                        # Join and fix
                        func_sig = '\n'.join(func_lines)
                        func_sig = func_sig.replace(
                            'current_user: User = Depends(get_current_user)',
                            f'current_user: User = Depends(require_role({roles_args}))'
                        )
                        
                        new_lines.extend(func_sig.split('\n'))
                        break
                    else:
                        new_lines.append(lines[i])
                        i += 1
            else:
                new_lines.append(line)
                i += 1
        else:
            new_lines.append(line)
            i += 1
    
    content = '\n'.join(new_lines)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    return False

# Fix all files
files_to_fix = [
    'Backend/app/api/scenarios.py',
    'Backend/app/api/costing.py',
    'Backend/app/api/integrations.py',
    'Backend/app/api/financials.py',
    'Backend/app/api/audit.py',
]

for filepath in files_to_fix:
    if Path(filepath).exists():
        fix_file(filepath)
    else:
        print(f"Not found: {filepath}")
