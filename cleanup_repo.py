
import os
import shutil
from pathlib import Path

root = Path(r"c:\Users\shaur\OneDrive\Desktop\Scrapper")
misc = root / "misc"
misc.mkdir(exist_ok=True)

to_move = [
    "Data Scraping Assignment.pdf",
    "LEARNING.md",
    "PROJECT_EXPLAINER.md",
    "debug_scraping.py",
    "learning.ipynb",
    "run.bat",
    "test_connectivity.py",
    "utils.py",
    "test_nltk.py"
]

for f in to_move:
    src = root / f
    if src.exists():
        try:
            shutil.move(str(src), str(misc / f))
            print(f"Moved: {f}")
        except Exception as e:
            print(f"Error moving {f}: {e}")

# Move parsers dir
parsers_src = root / "parsers"
if parsers_src.is_dir():
    try:
        shutil.move(str(parsers_src), str(misc / "parsers"))
        print("Moved: parsers directory")
    except Exception as e:
        print(f"Error moving parsers: {e}")
