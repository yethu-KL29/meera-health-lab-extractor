"""Required entry point: python extract.py <PDF/JPG/PNG>."""
import json
import sys
from pathlib import Path

from lab_extractor.pipeline import extract


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    try:
        print(json.dumps(extract(Path(sys.argv[1])), ensure_ascii=False, allow_nan=False))
    except (RuntimeError, OSError) as error:
        sys.exit(str(error))
