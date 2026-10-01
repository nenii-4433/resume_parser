import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NLP_SERVICE = ROOT / "nlp-service"
if str(NLP_SERVICE) not in sys.path:
    sys.path.insert(0, str(NLP_SERVICE))
