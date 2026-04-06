# kn5-converter

Herramienta en Python para convertir modelos **KN5** (Assetto Corsa) a **OBJ/MTL** y, de forma opcional, a **GLB** (glTF 2.0 binario). El núcleo de lectura del formato y la exportación OBJ provienen del conversor usado en el panel web de [AssettoServer](https://github.com/tempestgf/assettoserver) (atribución original: *Chipicao*).

## Requisitos

- Python 3.10 o superior
- `numpy` y **Pillow** (texturas DDS → PNG y lectura DDS en general)
- `trimesh` solo si quieres salida **GLB** (`pip install 'kn5-converter[glb]'`)

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
kn5-convert modelo.kn5 -o ./salida --dds-to-png    # + PNG junto a cada .dds en salida/texture
```

**DDS ↔ PNG** (misma lógica que `web-panel/src/scripts/dds2png.py` del panel, solo CLI; sin GUI):

```bash
dds-convert --source ./carpeta_con_dds --output ./misma_o_otra_carpeta --skip-existing
dds-convert ./una_sola_carpeta   # conversión in-place (origen = destino)
dds-convert --mode png2dds --source ./pngs --output ./dds_salida
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
from kn5_converter import convert_kn5, convert_dds_to_png

result = convert_kn5("mi_coche.kn5", export_format="both", dds_to_png=True)
print(result.get("dds_png"))  # converted / skipped / errors

convert_dds_to_png("ruta/texture", "ruta/texture", skip_existing=True)
```

## Limitaciones

- Los shaders de Assetto Corsa no se replican al 100%; la conversión apunta a visualización general (diffuse/detail, normales, transparencia aproximada en MTL/GLB).
- Mallas animadas (tipo nodo 3) se leen, pero no se exporta rigging ni animación.
- Para GLB, los materiales PBR son una aproximación (metálico/roughness fijos razonables).

## Licencia

MIT (ver `LICENSE`).
