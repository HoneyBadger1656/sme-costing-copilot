import re

files = [
    'Backend/app/api/costing.py',
    'Backend/app/api/integrations.py', 
    'Backend/app/api/financials.py',
    'Backend/app/api/audit.py'
]

for filepath in files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Pattern 1: Accountant, Admin, Owner
        content = re.sub(
            r'@require_role\(\["Accountant", "Admin", "Owner"\]\)\s*\n(\s*)def (\w+)\((.*?)current_user: User = Depends\(get_current_user\)',
            r'\1def \2(\3current_user: User = Depends(require_role("Accountant", "Admin", "Owner"))',
            content,
            flags=re.DOTALL
        )
        
        # Pattern 2: Admin, Owner
        content = re.sub(
            r'@require_role\(\["Admin", "Owner"\]\)\s*\n(\s*)def (\w+)\((.*?)current_user: User = Depends\(get_current_user\)',
            r'\1def \2(\3current_user: User = Depends(require_role("Admin", "Owner"))',
            content,
            flags=re.DOTALL
        )
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Fixed: {filepath}')
        else:
            print(f'No changes: {filepath}')
    except Exception as e:
        print(f'Error in {filepath}: {e}')
