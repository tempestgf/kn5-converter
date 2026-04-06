"""API principal de conversión."""

from __future__ import annotations

import os
from typing import Literal

from kn5_converter.export_glb import export_glb
from kn5_converter.export_obj import export_obj
from kn5_converter.parser import read_kn5

ExportFormat = Literal["obj", "glb", "both"]


def convert_kn5(
    kn5_path: str,
    output_dir: str | None = None,
    *,
    export_format: ExportFormat = "obj",
    verbose: bool = False,
    skip_ac_nodes: bool = True,
) -> dict[str, str | list[str]]:
    """
    Convierte un archivo .kn5 extrayendo texturas y generando OBJ/MTL y/o GLB.

    Parameters
    ----------
    kn5_path
        Ruta absoluta o relativa al archivo .kn5.
    output_dir
        Carpeta de salida (por defecto: ``<directorio_del_kn5>/output``).
    export_format
        ``obj`` (por defecto), ``glb`` o ``both``.
    verbose
        Si True, imprime progreso de lectura del KN5.
    skip_ac_nodes
        Si True, omite geometría cuyo nombre empieza por ``AC_`` (comportamiento del panel web).

    Returns
    -------
    dict
        Claves ``output_dir``, ``obj`` (ruta .obj si aplica), ``glb`` (ruta .glb si aplica),
        ``textures`` (lista de nombres de texturas embebidas en el KN5).
    """
    kn5_path = os.path.abspath(kn5_path)
    if not os.path.isfile(kn5_path):
        raise FileNotFoundError(kn5_path)

    base = os.path.splitext(os.path.basename(kn5_path))[0]
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(kn5_path), "output")
    output_dir = os.path.abspath(output_dir)

    texture_names, materials, meshes = read_kn5(kn5_path, output_dir, verbose=verbose)

    result: dict[str, str | list[str]] = {
        "output_dir": output_dir,
        "textures": texture_names,
    }

    if export_format in ("obj", "both"):
        export_obj(base, output_dir, materials, meshes, skip_ac_nodes=skip_ac_nodes)
        result["obj"] = os.path.join(output_dir, base + ".obj")
        result["mtl"] = os.path.join(output_dir, base + ".mtl")

    if export_format in ("glb", "both"):
        glb_path = export_glb(
            base,
            output_dir,
            materials,
            meshes,
            skip_ac_nodes=skip_ac_nodes,
        )
        result["glb"] = glb_path

    return result
