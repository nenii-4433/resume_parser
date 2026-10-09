from pathlib import Path

import nltk
from nltk.corpus import wordnet as wn


data_dir = Path(__file__).resolve().parent / "nltk_data"
nltk.data.path.insert(0, str(data_dir))

try:
    wn.morphy("developers")
except LookupError:
    if not nltk.download("wordnet", download_dir=str(data_dir), quiet=True):
        raise RuntimeError("Could not download the NLTK WordNet corpus.")
    wn.morphy("developers")
