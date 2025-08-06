import json
import os
import shutil

with open('backend/data/export.json') as f:
    metadata = json.load(f)

output_folder = 'renamed_output'
os.makedirs(output_folder, exist_ok=True)

for entry in metadata:
    if entry['validated'] and entry['page_number']:
        new_name = f"Page_{str(entry['page_number']).zfill(3)}.jpg"
        shutil.copy(entry['path'], os.path.join(output_folder, new_name))
