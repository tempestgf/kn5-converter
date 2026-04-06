"""Exportación a GLB (glTF 2.0 binario) mediante trimesh."""

from __future__ import annotations

import os

import numpy as np

from kn5_converter.export_obj import transparant_shader
from kn5_converter.parser import kn5Material, kn5Node


def _texture_for_material(mat: kn5Material, output_dir: str) -> str | None:
    """Misma heurística que OBJ: detail map vs diffuse."""
    if mat.useDetail == 1.0 and mat.txDetail:
        path = os.path.join(output_dir, "texture", mat.txDetail)
        if os.path.isfile(path):
            return path
    if mat.txDiffuse:
        path = os.path.join(output_dir, "texture", mat.txDiffuse)
        if os.path.isfile(path):
            return path
    return None


def export_glb(
    model_name: str,
    output_dir: str,
    materials: list[kn5Material],
    nodes: list[kn5Node],
    output_path: str | None = None,
    skip_ac_nodes: bool = True,
) -> str:
    try:
        import trimesh
        from PIL import Image
    except ImportError as e:
        raise ImportError(
            "Para exportar GLB instala las dependencias opcionales: pip install 'kn5-converter[glb]'"
        ) from e

    scene = trimesh.Scene()
    geom_idx = 0

    for srcNode in nodes:
        if skip_ac_nodes and srcNode.name.startswith("AC_"):
            continue
        if srcNode.type == 1:
            continue
        if srcNode.type not in (2, 3):
            continue

        vc = srcNode.vertexCount
        verts = np.zeros((vc, 3), dtype=np.float64)
        norms = np.zeros((vc, 3), dtype=np.float64)
        uvs = np.zeros((vc, 2), dtype=np.float64)

        hm = srcNode.hmatrix
        for v in range(vc):
            x = srcNode.position[v * 3]
            y = srcNode.position[v * 3 + 1]
            z = srcNode.position[v * 3 + 2]
            verts[v, 0] = hm[0][0] * x + hm[1][0] * y + hm[2][0] * z + hm[3][0]
            verts[v, 1] = hm[0][1] * x + hm[1][1] * y + hm[2][1] * z + hm[3][1]
            verts[v, 2] = hm[0][2] * x + hm[1][2] * y + hm[2][2] * z + hm[3][2]

            nx = srcNode.normal[v * 3]
            ny = srcNode.normal[v * 3 + 1]
            nz = srcNode.normal[v * 3 + 2]
            norms[v, 0] = hm[0][0] * nx + hm[1][0] * ny + hm[2][0] * nz
            norms[v, 1] = hm[0][1] * nx + hm[1][1] * ny + hm[2][1] * nz
            norms[v, 2] = hm[0][2] * nx + hm[1][2] * ny + hm[2][2] * nz

        UVmult = 1.0
        if srcNode.materialID >= 0:
            if materials[srcNode.materialID].useDetail == 0.0:
                UVmult = materials[srcNode.materialID].diffuseMult
            else:
                UVmult = materials[srcNode.materialID].detailUVMultiplier

        for v in range(vc):
            uvs[v, 0] = srcNode.texture0[v * 2] * UVmult
            uvs[v, 1] = srcNode.texture0[v * 2 + 1] * UVmult

        faces = np.array(srcNode.indices, dtype=np.int64).reshape(-1, 3)

        mat = None
        if srcNode.materialID >= 0:
            mat = materials[srcNode.materialID]

        tex_path = _texture_for_material(mat, output_dir) if mat else None
        is_transparent = mat is not None and transparant_shader(mat.shader)

        if tex_path:
            img = Image.open(tex_path)
            material = trimesh.visual.material.PBRMaterial(
                baseColorTexture=img,
                metallicFactor=0.0,
                roughnessFactor=0.85,
                alphaMode="BLEND" if is_transparent else "OPAQUE",
            )
            visual = trimesh.visual.TextureVisuals(uv=uvs, material=material)
        elif mat:
            kd = float(mat.ksDiffuse)
            material = trimesh.visual.material.PBRMaterial(
                baseColorFactor=[kd, kd, kd, 1.0],
                metallicFactor=0.0,
                roughnessFactor=0.85,
                alphaMode="BLEND" if is_transparent else "OPAQUE",
            )
            visual = trimesh.visual.TextureVisuals(uv=uvs, material=material)
        else:
            visual = None

        tm = trimesh.Trimesh(
            vertices=verts,
            faces=faces,
            vertex_normals=norms,
            visual=visual,
            process=False,
        )
        safe_name = srcNode.name.replace(" ", "_") or f"mesh_{geom_idx}"
        scene.add_geometry(tm, geom_name=f"{safe_name}_{geom_idx}")
        geom_idx += 1

    out = output_path or os.path.join(output_dir, model_name + ".glb")
    scene.export(out)
    print(f"Exporting {out}")
    return out
