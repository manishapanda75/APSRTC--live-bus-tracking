"""
Script to remove all db.close() calls from backend.py
These calls break thread-local connection pooling
"""

import re

# Read the file
with open('backend.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count occurrences before
before_count = content.count('db.close()')
print(f"Found {before_count} instances of db.close()")

# Remove all standalone db.close() lines (with optional whitespace)
# This regex matches lines that only contain whitespace and db.close()
content = re.sub(r'^\s*db\.close\(\)\s*$', '', content, flags=re.MULTILINE)

# Count after
after_count = content.count('db.close()')
print(f"Remaining instances: {after_count}")
print(f"Removed: {before_count - after_count}")

# Write back
with open('backend.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDone! All db.close() calls removed.")
print("Thread-local connections will now persist across requests.")
