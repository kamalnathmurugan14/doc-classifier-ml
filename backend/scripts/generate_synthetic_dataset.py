"""Generate the synthetic dataset into DOCS_ROOT/_synthetic (files only; use POST /datasets/synthetic to also label them).

python scripts/generate_synthetic_dataset.py --per-class 20
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import get_settings  # noqa: E402
from app.ml import synth  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--per-class", type=int, default=20)
ap.add_argument("--noise", type=float, default=0.1)
args = ap.parse_args()
s = get_settings()
made = synth.generate(s.docs_root, args.per_class, s.random_seed, args.noise)
print(f"wrote {len(made)} files under {s.docs_root / '_synthetic'}")
