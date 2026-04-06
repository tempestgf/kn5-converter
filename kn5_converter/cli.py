"""Interfaz de línea de comandos."""

from __future__ import annotations

import argparse
import os
import sys

from kn5_converter.convert import convert_kn5


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convierte modelos KN5 (Assetto Corsa) a OBJ/MTL y opcionalmente GLB.",
    )
    parser.add_argument(
        "path",
        help="Archivo .kn5 o carpeta que contenga uno o más .kn5 (se convierten todos los candidatos, "
        "excluyendo collider, LOD y variantes _B/_C/_D).",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_dir",
        default=None,
        help="Directorio de salida (por defecto: <carpeta>/output junto al .kn5 o bajo la ruta dada).",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("obj", "glb", "both"),
        default="obj",
        help="Formato de salida (por defecto: obj). 'both' genera OBJ y GLB.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Muestra información detallada al leer el KN5.",
    )
    parser.add_argument(
        "--include-ac-nodes",
        action="store_true",
        help="Incluye mallas cuyo nombre empieza por AC_ (por defecto se omiten).",
    )
    parser.add_argument(
        "--dds-to-png",
        action="store_true",
        help="Tras extraer texturas, convierte .dds a .png en output/texture (mismo directorio).",
    )
    args = parser.parse_args()

    target = os.path.abspath(args.path)

    if os.path.isfile(target):
        if not target.lower().endswith(".kn5"):
            print("El archivo debe tener extensión .kn5", file=sys.stderr)
            sys.exit(1)
        convert_kn5(
            target,
            args.output_dir,
            export_format=args.format,
            verbose=args.verbose,
            skip_ac_nodes=not args.include_ac_nodes,
            dds_to_png=args.dds_to_png,
        )
        return

    if not os.path.isdir(target):
        print(f"No existe la ruta: {target}", file=sys.stderr)
        sys.exit(1)

    extension = ".kn5"
    files = [
        os.path.join(target, f)
        for f in os.listdir(target)
        if f.endswith(extension)
        and "collider" not in f.lower()
        and "_lod" not in f.lower()
        and not f.lower().endswith(("_b.kn5", "_c.kn5", "_d.kn5"))
    ]

    if not files:
        print(
            "No se encontraron archivos .kn5 válidos (se excluyen collider, LOD y variantes).",
            file=sys.stderr,
        )
        sys.exit(1)

    out_base = args.output_dir or os.path.join(target, "output")
    for fp in sorted(files):
        sub = os.path.join(out_base, os.path.splitext(os.path.basename(fp))[0])
        os.makedirs(sub, exist_ok=True)
        print(f"=== {fp} -> {sub} ===")
        convert_kn5(
            fp,
            sub,
            export_format=args.format,
            verbose=args.verbose,
            skip_ac_nodes=not args.include_ac_nodes,
            dds_to_png=args.dds_to_png,
        )


if __name__ == "__main__":
    main()
