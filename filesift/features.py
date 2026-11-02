"""Per-image feature extraction: size, EXIF, perceptual hash, blur."""
from __future__ import annotations

from datetime import datetime

import numpy as np
from PIL import Image

from .models import FileInfo


def _parse_exif_date(value) -> float | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip()[:19], "%Y:%m:%d %H:%M:%S").timestamp()
    except ValueError:
        return None


def analyze_image(path: str) -> dict:
    """Return a JSON-serialisable feature dict. Never raises."""
    out: dict = {"width": 0, "height": 0, "fmt": "", "camera": False, "gps": False,
                 "taken": None, "dhash": None, "blur": None}
    try:
        with Image.open(path) as im:
            out["width"], out["height"] = im.size
            out["fmt"] = im.format or ""
            try:
                exif = im.getexif()
            except Exception:
                exif = None
            if exif:
                out["camera"] = bool(exif.get(271) or exif.get(272))
                dto = None
                try:
                    dto = exif.get_ifd(0x8769).get(36867)
                except Exception:
                    pass
                out["taken"] = _parse_exif_date(dto or exif.get(306))
                try:
                    out["gps"] = bool(exif.get_ifd(0x8825))
                except Exception:
                    pass
            try:
                im.draft("L", (256, 256))  # fast JPEG downscale while decoding
            except Exception:
                pass
            g = im.convert("L")
            small = np.asarray(g.resize((9, 8), Image.Resampling.LANCZOS), dtype=np.int16)
            bits = (small[:, :-1] > small[:, 1:]).flatten()
            out["dhash"] = int("".join("1" if b else "0" for b in bits), 2)
            g.thumbnail((256, 256))
            a = np.asarray(g, dtype=np.float32)
            if a.shape[0] > 3 and a.shape[1] > 3:
                lap = (-4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1]
                       + a[1:-1, :-2] + a[1:-1, 2:])
                out["blur"] = float(lap.var())
    except Exception:
        pass
    return out


def apply_features(fi: FileInfo, feat: dict) -> None:
    fi.width = feat.get("width", 0)
    fi.height = feat.get("height", 0)
    fi.fmt = feat.get("fmt", "")
    fi.camera = feat.get("camera", False)
    fi.gps = feat.get("gps", False)
    fi.taken = feat.get("taken")
    fi.dhash = feat.get("dhash")
    fi.blur = feat.get("blur")
