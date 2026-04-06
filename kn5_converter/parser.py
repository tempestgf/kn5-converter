"""Lectura del formato binario KN5 (Assetto Corsa)."""

from __future__ import annotations

import math
import os
import re
import struct
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    pass


def read_string(file, length: int) -> str:
    string_data = file.read(length)
    return string_data.decode("utf-8")


def sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename)
    sanitized = sanitized.strip(". ")
    if not sanitized:
        sanitized = "texture_unnamed"
    return sanitized


def matrix_mult(ma, mb):
    return np.matmul(np.array(ma, copy=True), np.array(mb, copy=True))


def matrix_to_euler(transf):
    heading = 0
    attitude = 0
    bank = 0

    if transf[0][1] > 0.998:
        heading = np.arctan2(-transf[1][0], transf[1][1])
        attitude = -math.pi / 2
        bank = 0.0
    elif transf[0][1] < -0.998:
        heading = np.arctan2(-transf[1][0], transf[1][1])
        attitude = math.pi / 2
        bank = 0.0
    else:
        heading = np.arctan2(transf[0][1], transf[0][0])
        bank = np.arctan2(transf[1][2], transf[2][2])
        attitude = np.arcsin(-transf[0][2])

    attitude *= 180 / math.pi
    heading *= 180 / math.pi
    bank *= 180 / math.pi

    return [bank, attitude, heading]


def scale_from_matrix(transf):
    scaleX = math.sqrt(
        transf[0][0] * transf[0][0]
        + transf[1][0] * transf[1][0]
        + transf[2][0] * transf[2][0]
    )
    scaleY = math.sqrt(
        transf[0][1] * transf[0][1]
        + transf[1][1] * transf[1][1]
        + transf[2][1] * transf[2][1]
    )
    scaleZ = math.sqrt(
        transf[0][2] * transf[0][2]
        + transf[1][2] * transf[1][2]
        + transf[2][2] * transf[2][2]
    )
    return [float(scaleX), float(scaleY), float(scaleZ)]


class kn5Material:
    def __init__(self):
        self.name = ""
        self.shader = ""
        self.ksAmbient = 0.6
        self.ksDiffuse = 0.6
        self.ksSpecular = 0.9
        self.ksSpecularEXP = 1.0
        self.diffuseMult = 1.0
        self.normalMult = 1.0
        self.useDetail = 0.0
        self.detailUVMultiplier = 1.0
        self.txDiffuse = ""
        self.txNormal = ""
        self.txDetail = ""

        self.txDetailR = ""
        self.txDetailG = ""
        self.txDetailB = ""
        self.txDetailA = ""
        self.txDetailNM = ""

        self.txMask = ""
        self.shader_props = ""
        self.ksEmissive = 0.0
        self.ksAlphaRef = 1.0


class kn5Node:
    def __init__(self):
        self.name = "Default"
        self.parent = None
        self.tmatrix = np.identity(4)
        self.hmatrix = np.identity(4)
        self.meshIndex = -1
        self.type = 1
        self.materialID = -1

        self.translation = np.identity(3)
        self.rotation = np.identity(3)
        self.scaling = np.identity(3)

        self.vertexCount = 0
        self.indices = []

        self.position = []
        self.normal = []
        self.texture0 = []


def read_nodes(file, node_list, parent_id):
    new_node = kn5Node()
    new_node.parent = parent_id

    new_node.type, = struct.unpack("<i", file.read(4))
    new_node.name = read_string(file, struct.unpack("<i", file.read(4))[0])
    children_count, = struct.unpack("<i", file.read(4))
    file.read(1)

    if new_node.type == 1:
        new_node.tmatrix = [[0] * 4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                new_node.tmatrix[i][j], = struct.unpack("<f", file.read(4))

        new_node.translation = [
            new_node.tmatrix[3][0],
            new_node.tmatrix[3][1],
            new_node.tmatrix[3][2],
        ]

        new_node.rotation = matrix_to_euler(new_node.tmatrix)
        new_node.scaling = scale_from_matrix(new_node.tmatrix)

    elif new_node.type == 2:
        file.read(3)

        new_node.vertexCount, = struct.unpack("<i", file.read(4))
        new_node.position = []
        new_node.normal = []
        new_node.texture0 = []

        for _ in range(new_node.vertexCount):
            new_node.position.extend(struct.unpack("<fff", file.read(12)))
            new_node.normal.extend(struct.unpack("<fff", file.read(12)))
            tex = struct.unpack("<ff", file.read(8))
            tex = (tex[0], 1.0 - tex[1])
            new_node.texture0.extend(tex)
            file.read(12)

        index_count, = struct.unpack("<i", file.read(4))
        new_node.indices = struct.unpack("<%dH" % index_count, file.read(index_count * 2))
        new_node.materialID, = struct.unpack("<i", file.read(4))
        file.read(29)

    elif new_node.type == 3:
        file.read(3)

        bone_count, = struct.unpack("<i", file.read(4))
        for _ in range(bone_count):
            read_string(file, struct.unpack("<i", file.read(4))[0])
            file.read(64)

        new_node.vertexCount, = struct.unpack("<i", file.read(4))
        new_node.position = []
        new_node.normal = []
        new_node.texture0 = []
        for _ in range(new_node.vertexCount):
            new_node.position.extend(struct.unpack("<fff", file.read(12)))
            new_node.normal.extend(struct.unpack("<fff", file.read(12)))
            tex = struct.unpack("<ff", file.read(8))
            tex = (tex[0], 1.0 - tex[1])
            new_node.texture0.extend(tex)
            file.read(44)

        index_count, = struct.unpack("<i", file.read(4))
        new_node.indices = struct.unpack("<%dH" % index_count, file.read(index_count * 2))
        new_node.materialID, = struct.unpack("<i", file.read(4))
        file.read(12)

    if parent_id < 0:
        new_node.hmatrix = new_node.tmatrix
    else:
        new_node.hmatrix = matrix_mult(new_node.tmatrix, node_list[parent_id].hmatrix)

    node_list.append(new_node)
    current_id = len(node_list) - 1

    for _ in range(children_count):
        node_list = read_nodes(file, node_list, current_id)

    return node_list


def read_kn5(file_path: str, output_dir: str, verbose: bool = False) -> tuple[list[str], list[kn5Material], list[kn5Node]]:
    texture_names: list[str] = []
    materials: list[kn5Material] = []
    meshes: list[kn5Node] = []

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    with open(file_path, "rb") as file:
        header = file.read(10)
        magic, version = struct.unpack("<6s1I", header)

        log(f"KN5 Magic: {magic}")
        log(f"KN5 Version: {version}")

        if version > 5:
            extra_bytes = file.read(4)
            log(f"Version {version} detected, extra 4 bytes: {extra_bytes.hex() if extra_bytes else 'EMPTY'}")

        tex_count_data = file.read(4)
        if len(tex_count_data) < 4:
            raise ValueError(
                "KN5 file is corrupted: Expected 4 bytes for texture count. File might be incomplete."
            )

        tex_count = struct.unpack("<i", tex_count_data)[0]
        log(f"Texture count: {tex_count}")

        for t in range(tex_count):
            log(f"Reading texture {t+1}/{tex_count} at position {file.tell()}")
            tex_type_data = file.read(4)
            if len(tex_type_data) < 4:
                raise ValueError(
                    f"KN5 file is corrupted at texture {t+1}/{tex_count}: File ends prematurely."
                )
            struct.unpack("<i", tex_type_data)[0]

            name_len_data = file.read(4)
            if len(name_len_data) < 4:
                raise ValueError(
                    f"KN5 file is corrupted at texture {t+1}/{tex_count}: Cannot read texture name length."
                )
            name_len = struct.unpack("<i", name_len_data)[0]

            tex_name_raw = read_string(file, name_len)
            tex_name = sanitize_filename(tex_name_raw)

            tex_size_data = file.read(4)
            if len(tex_size_data) < 4:
                raise ValueError(
                    f"KN5 file is corrupted at texture {t+1}/{tex_count} ({tex_name}): Cannot read texture size."
                )
            tex_size = struct.unpack("<i", tex_size_data)[0]

            texture_names.append(tex_name)

            tex_path = os.path.join(output_dir, "texture", tex_name)
            if os.path.exists(tex_path):
                log(f"  Skipping existing texture, seeking {tex_size} bytes")
                file.seek(tex_size, os.SEEK_CUR)
            else:
                if not os.path.exists(os.path.dirname(tex_path)):
                    os.mkdir(os.path.dirname(tex_path))

                texture_data = file.read(tex_size)
                if len(texture_data) < tex_size:
                    raise ValueError(
                        f"Failed to read texture data for {tex_name}: Expected {tex_size} bytes, got {len(texture_data)}"
                    )

                with open(tex_path, "wb") as tex_file:
                    tex_file.write(texture_data)

        mat_count = struct.unpack("<i", file.read(4))[0]

        for _ in range(mat_count):
            new_material = kn5Material()

            new_material.name = read_string(file, struct.unpack("<i", file.read(4))[0])
            new_material.shader = read_string(file, struct.unpack("<i", file.read(4))[0])
            struct.unpack("<h", file.read(2))[0]
            if version > 4:
                struct.unpack("<i", file.read(4))[0]

            prop_count = struct.unpack("<i", file.read(4))[0]
            for _p in range(prop_count):
                prop_name = read_string(file, struct.unpack("<i", file.read(4))[0])
                prop_value = struct.unpack("<f", file.read(4))[0]
                new_material.shader_props += prop_name + " = " + str(prop_value) + "&cr;&lf;"

                if prop_name == "ksAmbient":
                    new_material.ksAmbient = prop_value
                elif prop_name == "ksDiffuse":
                    new_material.ksDiffuse = prop_value
                elif prop_name == "ksSpecular":
                    new_material.ksSpecular = prop_value
                elif prop_name == "ksSpecularEXP":
                    new_material.ksSpecularEXP = prop_value
                elif prop_name == "diffuseMult":
                    new_material.diffuseMult = prop_value
                elif prop_name == "normalMult":
                    new_material.normalMult = prop_value
                elif prop_name == "useDetail":
                    new_material.useDetail = prop_value
                elif prop_name == "detailUVMultiplier":
                    new_material.detailUVMultiplier = prop_value
                elif prop_name == "ksEmissive":
                    new_material.ksEmissive = prop_value
                elif prop_name == "ksAlphaRef":
                    new_material.ksAlphaRef = prop_value

                file.seek(36, os.SEEK_CUR)

            tex_slot_count = struct.unpack("<i", file.read(4))[0]
            for _t in range(tex_slot_count):
                sample_name = read_string(file, struct.unpack("<i", file.read(4))[0])
                struct.unpack("<i", file.read(4))[0]
                tex_name_raw = read_string(file, struct.unpack("<i", file.read(4))[0])
                tex_name = sanitize_filename(tex_name_raw)

                new_material.shader_props += sample_name + " = " + tex_name + "&cr;&lf;"

                if sample_name == "txDiffuse":
                    new_material.txDiffuse = tex_name
                elif sample_name == "txNormal":
                    new_material.txNormal = tex_name
                elif sample_name == "txDetail":
                    new_material.txDetail = tex_name
                elif sample_name == "txDetailR":
                    new_material.txDetailR = tex_name
                elif sample_name == "txDetailG":
                    new_material.txDetailG = tex_name
                elif sample_name == "txDetailB":
                    new_material.txDetailB = tex_name
                elif sample_name == "txDetailA":
                    new_material.txDetailA = tex_name
                elif sample_name == "txDetailNM":
                    new_material.txDetailNM = tex_name
                elif sample_name == "txMask":
                    new_material.txMask = tex_name

            materials.append(new_material)

        meshes = read_nodes(file, meshes, -1)

    return texture_names, materials, meshes
