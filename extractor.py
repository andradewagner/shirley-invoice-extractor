import argparse
import json
from pathlib import Path

from app.core.engine import extract


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path, nargs="+")
    args = parser.parse_args()

    for pdf in args.pdf:
        try:
            print(json.dumps(
                {"file": pdf.name, **extract(pdf)},
                ensure_ascii=False,
                indent=2
            ))
        except Exception as error:
            print(json.dumps({
                "file": pdf.name,
                "error": str(error)
            }, ensure_ascii=False))
