
import json
from pathlib import Path
OUT_DIR = Path('samples/example_output')
OUT_DIR.mkdir(parents=True, exist_ok=True)
def save_ap(ap_model, filename='ap_model.json'):
    p = OUT_DIR / filename
    with p.open('w', encoding='utf-8') as f:
        json.dump(ap_model.to_json(), f, ensure_ascii=False, indent=2)
    return str(p)
def save_text(text, filename='sf_story.txt'):
    p = OUT_DIR / filename
    with p.open('w', encoding='utf-8') as f:
        f.write(text)
    return str(p)
