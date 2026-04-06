"""Exportación a Wavefront OBJ/MTL."""

from __future__ import annotations

import datetime
import os

from kn5_converter.parser import kn5Material, kn5Node


def transparant_shader(shader: str) -> bool:
    if shader.startswith("ksPerPixelAT"):
        return True
    if shader == "ksPerPixelAlpha":
        return True
    if shader == "ksSkidMark":
        return True
    if shader == "ksTree":
        return True
    if shader == "ksGrass":
        return True
    if shader == "ksFlags":
        return True
    return False


def export_obj(
    model_name: str,
    output_dir: str,
    materials: list[kn5Material],
    nodes: list[kn5Node],
    skip_ac_nodes: bool = True,
) -> None:
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    print("Exporting {}.obj".format(model_name))

    with open(os.path.join(output_dir, model_name + ".mtl"), "w") as mtl_writer:
        mtl_str = ""

        for src_mat in materials:
            mtl_str += "newmtl {}\r\n".format(src_mat.name.replace(" ", "_"))
            mtl_str += "Ka {} {} {}\r\n".format(
                src_mat.ksAmbient, src_mat.ksAmbient, src_mat.ksAmbient
            )
            mtl_str += "Kd {} {} {}\r\n".format(
                src_mat.ksDiffuse, src_mat.ksDiffuse, src_mat.ksDiffuse
            )
            mtl_str += "Ks {} {} {}\r\n".format(
                src_mat.ksSpecular, src_mat.ksSpecular, src_mat.ksSpecular
            )
            mtl_str += "Ns {}\r\n".format(src_mat.ksSpecularEXP)
            mtl_str += "illum 2\r\n"

            is_transparant = transparant_shader(src_mat.shader)

            if is_transparant:
                mtl_str += "d 0.9999\r\n"

            if src_mat.useDetail == 1.0 and src_mat.txDetail:
                mtl_str += "map_Kd texture\\{}\r\n".format(src_mat.txDetail)

                if src_mat.txDiffuse:
                    mtl_str += "map_Ks texture\\{}\r\n".format(src_mat.txDiffuse)

                if is_transparant:
                    mtl_str += "map_d texture\\{}\r\n".format(src_mat.txDetailA)

            elif src_mat.txDiffuse:
                mtl_str += "map_Kd texture\\{}\r\n".format(src_mat.txDiffuse)

                if is_transparant:
                    mtl_str += "map_d texture\\{}\r\n".format(src_mat.txDiffuse)

            if src_mat.txNormal:
                mtl_str += "bump texture\\{}\r\n".format(src_mat.txNormal)

            mtl_str += "\r\n"

        mtl_writer.write(mtl_str)

    with open(os.path.join(output_dir, model_name + ".obj"), "w") as OBJwriter:
        sb = "# Assetto Corsa model\n"
        sb += f"# Exported with kn5-converter (Chipicao) on {datetime.datetime.now()}\n"
        sb += f"\nmtllib {model_name}.mtl\n"

        vertexPad = 1

        for srcNode in nodes:
            if skip_ac_nodes and srcNode.name.startswith("AC_"):
                continue

            if srcNode.type == 1:
                continue
            elif srcNode.type in [2, 3]:
                sb += f"\n g {srcNode.name.replace(' ', '_')}\n"

                for v in range(srcNode.vertexCount):
                    x = srcNode.position[v * 3]
                    y = srcNode.position[v * 3 + 1]
                    z = srcNode.position[v * 3 + 2]

                    vx = (
                        srcNode.hmatrix[0][0] * x
                        + srcNode.hmatrix[1][0] * y
                        + srcNode.hmatrix[2][0] * z
                        + srcNode.hmatrix[3][0]
                    )
                    vy = (
                        srcNode.hmatrix[0][1] * x
                        + srcNode.hmatrix[1][1] * y
                        + srcNode.hmatrix[2][1] * z
                        + srcNode.hmatrix[3][1]
                    )
                    vz = (
                        srcNode.hmatrix[0][2] * x
                        + srcNode.hmatrix[1][2] * y
                        + srcNode.hmatrix[2][2] * z
                        + srcNode.hmatrix[3][2]
                    )

                    sb += f"v {vx} {vy} {vz}\n"

                OBJwriter.write(sb)
                sb = ""

                for v in range(srcNode.vertexCount):
                    x = srcNode.normal[v * 3]
                    y = srcNode.normal[v * 3 + 1]
                    z = srcNode.normal[v * 3 + 2]

                    nx = (
                        srcNode.hmatrix[0][0] * x
                        + srcNode.hmatrix[1][0] * y
                        + srcNode.hmatrix[2][0] * z
                    )
                    ny = (
                        srcNode.hmatrix[0][1] * x
                        + srcNode.hmatrix[1][1] * y
                        + srcNode.hmatrix[2][1] * z
                    )
                    nz = (
                        srcNode.hmatrix[0][2] * x
                        + srcNode.hmatrix[1][2] * y
                        + srcNode.hmatrix[2][2] * z
                    )

                    sb += f"vn {nx} {ny} {nz}\n"

                OBJwriter.write(sb)
                sb = ""

                UVmult = 1.0
                if srcNode.materialID >= 0:
                    if materials[srcNode.materialID].useDetail == 0.0:
                        UVmult = materials[srcNode.materialID].diffuseMult
                    else:
                        UVmult = materials[srcNode.materialID].detailUVMultiplier

                for v in range(srcNode.vertexCount):
                    tx = srcNode.texture0[v * 2] * UVmult
                    ty = srcNode.texture0[v * 2 + 1] * UVmult

                    sb += f"vt {tx} {ty}\n"

                OBJwriter.write(sb)
                sb = []

                if srcNode.materialID >= 0:
                    sb.append(
                        "\r\nusemtl {}\r\n".format(
                            materials[srcNode.materialID].name.replace(" ", "_")
                        )
                    )
                else:
                    sb.append("\r\nusemtl Default\r\n")

                for i in range(0, len(srcNode.indices) // 3):
                    i1 = srcNode.indices[i * 3] + vertexPad
                    i2 = srcNode.indices[i * 3 + 1] + vertexPad
                    i3 = srcNode.indices[i * 3 + 2] + vertexPad

                    sb.append(
                        "f {}/{}/{} {}/{}/{} {}/{}/{}\r\n".format(
                            i1, i1, i1, i2, i2, i2, i3, i3, i3
                        )
                    )

                sb = "".join(sb)
                OBJwriter.write(sb)

                vertexPad += srcNode.vertexCount
                continue
