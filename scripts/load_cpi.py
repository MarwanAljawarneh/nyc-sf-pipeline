# Retain direct `python scripts/...` execution as well as module imports.
if __name__ == "__main__" and __package__ is None:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nyc_sf_pipeline.cpi import extract_cpi, load_cpi


if __name__ == "__main__":
    load_cpi(extract_cpi())
