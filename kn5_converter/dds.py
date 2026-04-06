"""
Conversión DDS ↔ PNG (Pillow). Basado en web-panel/src/scripts/dds2png.py (AssettoServer).
"""

from __future__ import annotations

import os
from typing import Iterable, Optional, Sequence, Set, Tuple

from PIL import Image, ImageEnhance, ImageFilter
from PIL import UnidentifiedImageError


def apply_image_filters(image, brightness, contrast, saturation, sharpening, blurring):
    if sharpening:
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
    if blurring:
        image = image.filter(ImageFilter.BLUR)
    if brightness != 0:
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1 + brightness / 100.0)
    if contrast != 0:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1 + contrast / 100.0)
    if saturation != 1:
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(saturation / 100.0)
    return image


def _normalize_names(names: Optional[Iterable[str]]) -> Optional[Set[str]]:
    if not names:
        return None
    return {name.lower() for name in names}


def convert_dds_to_png(
    dds_directory: str,
    png_directory: str,
    compression_type: str = "lossless",
    keep_alpha: bool = True,
    resize: Optional[Tuple[int, int]] = None,
    brightness: int = 0,
    contrast: int = 0,
    saturation: int = 1,
    sharpening: bool = False,
    blurring: bool = False,
    only_filenames: Optional[Iterable[str]] = None,
    skip_existing: bool = False,
) -> dict[str, int]:
    """
    Convierte cada ``*.dds`` en ``dds_directory`` a ``*.png`` en ``png_directory``.

    Returns
    -------
    dict
        Claves ``converted``, ``skipped``, ``errors``.
    """
    if not os.path.exists(png_directory):
        os.makedirs(png_directory)

    include_set = _normalize_names(only_filenames)

    converted_count = 0
    skipped_count = 0
    error_count = 0

    for filename in os.listdir(dds_directory):
        if not filename.lower().endswith(".dds"):
            continue

        if include_set and filename.lower() not in include_set:
            continue

        dds_path = os.path.join(dds_directory, filename)
        png_filename = os.path.splitext(filename)[0] + ".png"
        png_path = os.path.join(png_directory, png_filename)

        if skip_existing and os.path.exists(png_path):
            skipped_count += 1
            continue

        try:
            image = Image.open(dds_path)
        except UnidentifiedImageError:
            error_count += 1
            continue
        except Exception:
            error_count += 1
            continue

        try:
            if not keep_alpha and image.mode == "RGBA":
                image = image.convert("RGB")
            if resize:
                image = image.resize(resize, Image.LANCZOS)
            image = apply_image_filters(
                image, brightness, contrast, saturation, sharpening, blurring
            )
            if compression_type == "lossy":
                image.save(png_path, format="PNG", compress_level=6)
            else:
                image.save(png_path, format="PNG", compress_level=0)
            converted_count += 1
        except Exception:
            error_count += 1
        finally:
            image.close()

    return {
        "converted": converted_count,
        "skipped": skipped_count,
        "errors": error_count,
    }


def convert_png_to_dds(
    png_directory: str,
    dds_directory: str,
    keep_alpha: bool = True,
    only_filenames: Optional[Iterable[str]] = None,
) -> int:
    """Convierte cada ``*.png`` en ``png_directory`` a ``*.dds`` en ``dds_directory``. Retorna cantidad convertida."""
    if not os.path.exists(dds_directory):
        os.makedirs(dds_directory)
    include_set = _normalize_names(only_filenames)
    n = 0
    for filename in os.listdir(png_directory):
        if not filename.lower().endswith(".png"):
            continue
        if include_set and filename.lower() not in include_set:
            continue
        png_path = os.path.join(png_directory, filename)
        dds_filename = os.path.splitext(filename)[0] + ".dds"
        dds_path = os.path.join(dds_directory, dds_filename)
        with Image.open(png_path) as image:
            if not keep_alpha and image.mode == "RGBA":
                image = image.convert("RGB")
            image.save(dds_path, format="DDS")
        n += 1
    return n


def _parse_resize(width: int, height: int) -> Optional[Tuple[int, int]]:
    if width > 0 and height > 0:
        return (width, height)
    return None


def _parse_include(names: Optional[Sequence[str]], mode: str) -> Optional[Iterable[str]]:
    if not names:
        return None

    normalized = []
    suffix = ".dds" if mode == "dds2png" else ".png"

    for name in names:
        lower = name.lower()
        if lower.endswith(".dds") or lower.endswith(".png"):
            normalized.append(name)
        else:
            normalized.append(f"{name}{suffix}")

    return normalized
