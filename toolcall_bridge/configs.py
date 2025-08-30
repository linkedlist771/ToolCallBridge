import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
ROOT = Path(__file__).parent.parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True, parents=True)
OPENAI_COMPATIBLE_BASEURL = os.environ.get("OPENAI_COMPATIBLE_BASEURL", "")
assert OPENAI_COMPATIBLE_BASEURL, "OPENAI_COMPATIBLE_BASEURL is not set"
