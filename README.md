# sort_drive

Herramientas para organizar archivos localmente y sincronizarlos con Google
Drive usando `rclone`. El flujo tipico es: traer desde Drive, ordenar/renombrar
carpetas, y subir los cambios.

## Que incluye

- `drive_sorter.py`: mueve archivos desde carpetas con fecha a una carpeta
  unica y renombra cada archivo con el nombre de la carpeta origen.
- `pre_pull_from_drive.sh`: descarga desde Drive a una carpeta local.
- `post_push_to_drive.sh`: sube desde la carpeta local a Drive (copia o
  sincroniza).

## Requisitos

- Python 3 (para `drive_sorter.py`).
- `rclone` y `flock` (para los scripts `.sh`).
- Un remote de `rclone` configurado (por ejemplo, `gdrive`).
- Archivo de configuracion `sort_drive.conf` en la raiz del proyecto.

## Uso rapido (flujo completo)

1) Ajusta las variables de configuracion en `sort_drive.conf`.
2) Trae el contenido de Drive:

```bash
./pre_pull_from_drive.sh --dry-run
./pre_pull_from_drive.sh
```

3) Organiza archivos con el sorter:

```bash
python3 drive_sorter.py /ruta/a/20250901_vs\ Campamento /ruta/a/20250909_@\ Fuenlabrada
```

4) Sube los cambios a Drive:

```bash
./post_push_to_drive.sh --dry-run
./post_push_to_drive.sh
```

Si necesitas reflejar borrados en Drive, usa `--mirror` en el paso 4.

## drive_sorter.py

### Que hace

Mueve archivos desde carpetas origen a una carpeta unica (por defecto
`20251200_Fútbol`) y los renombra usando el nombre de la carpeta origen mas un
indice. Mantiene la extension original del archivo.

Ejemplo:

- Carpeta origen: `20250901_vs Campamento`
  - `IMG_001.jpg` -> `20250901_vs Campamento_1.jpg`
  - `VID_002.mp4` -> `20250901_vs Campamento_2.mp4`
- Carpeta origen: `20250909_@ Fuenlabrada`
  - `PIC_01.jpg` -> `20250909_@ Fuenlabrada_1.jpg`

### Como funciona

- Usa como prefijo el nombre de la carpeta origen.
- Enumera archivos de cada carpeta desde 1 en adelante.
- Si el nombre destino ya existe, agrega un sufijo (`_2`, `_3`, etc.).
- No toca archivos sueltos en la raiz, solo archivos dentro de subcarpetas.

### Uso

```bash
python3 drive_sorter.py /ruta/a/carpeta1 /ruta/a/carpeta2
```

Tomar todas las subcarpetas de una raiz y copiar (sin modificar el origen):

```bash
python3 drive_sorter.py --source-root "/ruta/a/original_files" --dest "/ruta/a/new_files" --copy
```

Para previsualizar sin mover archivos:

```bash
python3 drive_sorter.py /ruta/a/carpeta1 /ruta/a/carpeta2 --dry-run
```

Cambiar la carpeta destino:

```bash
python3 drive_sorter.py /ruta/a/carpeta1 --dest "20251200_Fútbol"
```

Usar un archivo de configuracion alternativo:

```bash
python3 drive_sorter.py --config /ruta/a/sort_drive.conf /ruta/a/carpeta1
```

### Parametros

- `source_folders`: una o mas carpetas origen.
- `--source-root`: carpeta raiz de la que se toman subcarpetas.
- `--dest`: carpeta destino (ruta absoluta o relativa al directorio actual).
- `--copy`: copia archivos en lugar de moverlos.
- `--dry-run`: muestra las acciones sin mover archivos.
- `--config`: ruta del archivo de configuracion.

Valores por defecto en `sort_drive.conf`:

- `DRIVE_SORTER_DEST`
- `DRIVE_SORTER_SOURCE_ROOT`
- `DRIVE_SORTER_COPY`

## pre_pull_from_drive.sh

### Que hace

Copia desde Drive hacia local (no borra nada en Drive).

### Uso

```bash
./pre_pull_from_drive.sh [--dry-run] [--verbose] [--yes]
```

Usar un archivo de configuracion alternativo:

```bash
CONFIG_FILE=/ruta/a/sort_drive.conf ./pre_pull_from_drive.sh
```

Filtrar solo carpetas que coincidan con un patron (ejemplo):

```bash
# En sort_drive.conf:
# DRIVE_PULL_PATTERN=2025*_vs*
./pre_pull_from_drive.sh --dry-run --yes
```

### Configuracion

Variables editables en `sort_drive.conf` (o con `CONFIG_FILE`):

- `REMOTE_NAME`: nombre del remote en `rclone`.
- `REMOTE_FOLDER`: carpeta remota en Drive.
- `LOCAL_FOLDER`: carpeta local destino.
- `EXCLUDES_FILE`: archivo de exclusiones de `rclone` (opcional).
- `TRANSFERS`, `CHECKERS`: parametros de rendimiento.
- `DRIVE_PULL_PATTERN`: patron de carpeta dentro de `REMOTE_FOLDER` (opcional).

## post_push_to_drive.sh

### Que hace

Sube desde local hacia Drive. En modo `--mirror` usa `rclone sync`, que refleja
los borrados en Drive.

### Uso

```bash
./post_push_to_drive.sh [--dry-run] [--verbose] [--yes] [--mirror]
```

Usar un archivo de configuracion alternativo:

```bash
CONFIG_FILE=/ruta/a/sort_drive.conf ./post_push_to_drive.sh
```

### Configuracion

Variables editables: las mismas que en `pre_pull_from_drive.sh`.

## Notas

- Todo opera sobre el sistema de archivos local; Drive se sincroniza via
  `rclone`.
- El orden de renombrado en `drive_sorter.py` depende del orden alfabetico de
  archivos dentro de cada carpeta origen.
