"""CLI para conversión DDS ↔ PNG (sin GUI)."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional, Sequence

from kn5_converter.dds import (
    _parse_include,
    _parse_resize,
    convert_dds_to_png,
    convert_png_to_dds,
)


def run_cli_conversion(args: argparse.Namespace) -> None:
    resize = _parse_resize(args.resize_width, args.resize_height)
    include = _parse_include(args.include, args.mode)

    if args.mode == "dds2png":
        stats = convert_dds_to_png(
            dds_directory=args.source,
            png_directory=args.output,
            compression_type="lossy" if args.lossy else "lossless",
            keep_alpha=not args.drop_alpha,
            resize=resize,
            brightness=args.brightness,
            contrast=args.contrast,
            saturation=args.saturation,
            sharpening=args.sharpen,
            blurring=args.blur,
            only_filenames=include,
            skip_existing=args.skip_existing,
        )
        print(
            f"Conversion complete: {stats['converted']} converted, "
            f"{stats['skipped']} skipped, {stats['errors']} errors"
        )
    else:
        n = convert_png_to_dds(
            png_directory=args.source,
            dds_directory=args.output,
            keep_alpha=not args.drop_alpha,
            only_filenames=include,
        )
        print(f"Conversion complete: {n} files")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convierte texturas DDS a PNG o PNG a DDS (mismo flujo que el panel AssettoServer).",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        help="Carpeta a convertir (modo in-place: --source y --output serán esta carpeta).",
    )
    parser.add_argument(
        "--mode",
        choices=["dds2png", "png2dds"],
        default="dds2png",
        help="Dirección de conversión (por defecto: dds2png).",
    )
    parser.add_argument("--source", help="Carpeta origen con texturas.")
    parser.add_argument("--output", help="Carpeta destino.")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="No regenerar PNG si ya existe.",
    )
    parser.add_argument(
        "--lossy",
        action="store_true",
        help="PNG con compresión más agresiva (compress_level 6).",
    )
    parser.add_argument(
        "--drop-alpha",
        action="store_true",
        help="Quitar canal alpha al convertir.",
    )
    parser.add_argument(
        "--resize-width",
        type=int,
        default=0,
        help="Ancho de redimensionado (requiere alto > 0).",
    )
    parser.add_argument(
        "--resize-height",
        type=int,
        default=0,
        help="Alto de redimensionado (requiere ancho > 0).",
    )
    parser.add_argument(
        "--brightness",
        type=int,
        default=0,
        help="Brillo (-100 a 100).",
    )
    parser.add_argument(
        "--contrast",
        type=int,
        default=0,
        help="Contraste (-100 a 100).",
    )
    parser.add_argument(
        "--saturation",
        type=int,
        default=1,
        help="Saturación (1 = sin cambio; p. ej. 100 = valor típico).",
    )
    parser.add_argument("--sharpen", action="store_true", help="Enfocar.")
    parser.add_argument("--blur", action="store_true", help="Desenfocar.")
    parser.add_argument(
        "--include",
        nargs="*",
        help="Solo estos nombres de archivo (sin distinguir mayúsculas).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.directory and not args.source and not args.output:
        args.source = args.directory
        args.output = args.directory

    if args.source is None or args.output is None:
        parser.error("Indica --source y --output, o una carpeta posicional para conversión in-place.")

    args.source = os.path.abspath(args.source)
    args.output = os.path.abspath(args.output)
    if not os.path.isdir(args.source):
        print(f"No es un directorio: {args.source}", file=sys.stderr)
        return 1

    run_cli_conversion(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
