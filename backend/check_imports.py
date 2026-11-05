import ast
import os
import sys
from pathlib import Path

stdlib = sys.stdlib_module_names
imports = set()

def process_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except Exception as e:
        pass

for root, dirs, files in os.walk(sys.argv[1]):
    if 'venv' in root or '.venv' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            process_file(os.path.join(root, file))

external = sorted([i for i in imports if i not in stdlib and i not in ['app', 'tests', 'tts_inference_engine'] and not i.startswith('.')])
print(", ".join(external))
