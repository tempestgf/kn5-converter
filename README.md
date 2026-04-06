# kn5-converter

Herramienta en Python para convertir modelos **KN5** (Assetto Corsa) a **OBJ/MTL** y, de forma opcional, a **GLB** (glTF 2.0 binario). El núcleo de lectura del formato y la exportación OBJ provienen del conversor usado en el panel web de [AssettoServer](https://github.com/tempestgf/assettoserver) (atribución original: *Chipicao*).

## Requisitos

- Python 3.10 o superior
- `numpy` (siempre)
- `trimesh` y `Pillow` solo si quieres salida **GLB** (`pip install 'kn5-converter[glb]'`)

## Instalación

```bash
pip install .
# o con soporte GLB:
pip install '.[glb]'
```

Desde el código fuente del repositorio:

```bash
git clone <url-del-repo> kn5-converter
cd kn5-converter
pip install '.[glb]'
```

## Uso rápido

**Un solo archivo `.kn5`:**

```bash
kn5-convert ruta/al/modelo.kn5 -o ./salida -f obj
kn5-convert ruta/al/modelo.kn5 -o ./salida -f glb    # requiere [glb]
kn5-convert ruta/al/modelo.kn5 -f both              # OBJ + GLB
```

**Carpeta de coche** (convierte todos los `.kn5` candidatos, excluyendo `collider`, LOD y variantes `_B`/`_C`/`_D`):

```bash
kn5-convert /ruta/a/content/cars/mi_coche -f obj
```

Las texturas incrustadas se escriben en `<salida>/texture/`. Por defecto la salida es `<directorio_del_kn5>/output` si no pasas `-o`.

**Modo verbose** (útil para depurar KN5 dañados):

```bash
kn5-convert modelo.kn5 -v
```

**API en Python**

```python
from kn5_converter import convert_kn5

result = convert_kn5("mi_coche.kn5", export_format="both", verbose=False)
print(result["output_dir"], result.get("obj"), result.get("glb"))
```

## Limitaciones

- Los shaders de Assetto Corsa no se replican al 100%; la conversión apunta a visualización general (diffuse/detail, normales, transparencia aproximada en MTL/GLB).
- Mallas animadas (tipo nodo 3) se leen, pero no se exporta rigging ni animación.
- Para GLB, los materiales PBR son una aproximación (metálico/roughness fijos razonables).

## Licencia

MIT (ver `LICENSE`).
