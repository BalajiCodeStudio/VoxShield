"""Train with XLS-R 300M backbone (XLSR-SLS family).

Usage:
    python ml/training/train_xlsr.py [--config ml/configs/config.yaml]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKBONE = "facebook/wav2vec2-xls-r-300m"


def main():
    config = sys.argv[sys.argv.index("--config") + 1] if "--config" in sys.argv else "ml/configs/config.yaml"
    script = str(Path(__file__).parent / "train.py")
    subprocess.run([sys.executable, script, "--config", config, "--backbone", BACKBONE], check=True)


if __name__ == "__main__":
    main()
