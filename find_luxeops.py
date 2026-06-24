import os

def find_luxeops():
    target_dir = r"C:\Users\meet0\.gemini\antigravity\scratch\hotel-ops-task-system"
    extensions = ('.py', '.html', '.js', '.css')
    
    for root, dirs, files in os.walk(target_dir):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith(extensions):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'luxeops' in content.lower():
                            print(f"Match found in: {filepath}")
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

if __name__ == '__main__':
    find_luxeops()
