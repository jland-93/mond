"""
🌙 pytest 부트스트랩 — backend/를 sys.path에 보장해 'app.models' 같은 절대 import가 동작하게.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))
