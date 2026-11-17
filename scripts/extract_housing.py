# Retain direct `python scripts/...` execution as well as module imports.
if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nyc_sf_pipeline.housing import extract_housing


if __name__ == "__main__":
    extract_housing()
