#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${CONFIG_FILE:-$SCRIPT_DIR/sort_drive.conf}"
if [[ -f "$CONFIG_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi

# --- Configuracion editable ---
REMOTE_NAME="${REMOTE_NAME:-gdrive}"
REMOTE_FOLDER="${REMOTE_FOLDER:-Trabajo/Proyectos}"
LOCAL_FOLDER="${LOCAL_FOLDER:-$HOME/DriveTrabajo}"
EXCLUDES_FILE="${EXCLUDES_FILE:-}"
TRANSFERS="${TRANSFERS:-4}"
CHECKERS="${CHECKERS:-8}"

# --- Variables internas ---
STATE_DIR="$HOME/.local/state/drive_sync"
LOG_DIR="$STATE_DIR/logs"
LOCK_FILE="$STATE_DIR/pre_pull.lock"
DRY_RUN=false
VERBOSE=false
ASSUME_YES=false

usage() {
  cat <<'EOF'
Uso: pre_pull_from_drive.sh [--dry-run] [--verbose] [--yes]
  --dry-run   Ejecuta rclone en modo simulacion
  --verbose   Aumenta el nivel de log
  --yes       No pedir confirmacion
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --verbose) VERBOSE=true; shift ;;
    --yes) ASSUME_YES=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Flag desconocido: $1" >&2; usage; exit 2 ;;
  esac
done

if ! command -v rclone >/dev/null 2>&1; then
  echo "Error: rclone no esta instalado." >&2
  exit 1
fi
if ! command -v flock >/dev/null 2>&1; then
  echo "Error: flock no esta disponible (util-linux)." >&2
  exit 1
fi
if [[ -z "${REMOTE_NAME}" || -z "${REMOTE_FOLDER}" || -z "${LOCAL_FOLDER}" ]]; then
  echo "Error: variables de configuracion vacias." >&2
  exit 1
fi

mkdir -p "$LOCAL_FOLDER"
mkdir -p "$LOG_DIR"

LOG_LEVEL="INFO"
if $VERBOSE; then
  LOG_LEVEL="DEBUG"
fi

LOG_FILE="$LOG_DIR/pre_pull_$(date +%Y%m%d_%H%M%S).log"

RCLONE_OPTS=(
  "--transfers" "$TRANSFERS"
  "--checkers" "$CHECKERS"
  "--log-file" "$LOG_FILE"
  "--log-level" "$LOG_LEVEL"
)

if [[ -n "$EXCLUDES_FILE" && -f "$EXCLUDES_FILE" ]]; then
  RCLONE_OPTS+=("--exclude-from" "$EXCLUDES_FILE")
fi

if $DRY_RUN; then
  RCLONE_OPTS+=("--dry-run")
fi

if [[ -t 1 ]]; then
  RCLONE_OPTS+=("--progress")
fi

OPERATION="copy"
SRC="${REMOTE_NAME}:${REMOTE_FOLDER}"
DST="${LOCAL_FOLDER}"

if ! $ASSUME_YES; then
  echo "Remote: $SRC"
  echo "Local:  $DST"
  echo "Operacion: $OPERATION"
  echo "Dry-run: $DRY_RUN"
  read -r -p "Continuar? [y/N] " reply
  case "$reply" in
    y|Y|yes|YES) ;;
    *) echo "Abortado."; exit 0 ;;
  esac
fi

(
  flock -n 9 || { echo "Otro proceso esta en ejecucion." >&2; exit 1; }
  rclone copy "$SRC" "$DST" "${RCLONE_OPTS[@]}"
) 9>"$LOCK_FILE"

EXIT_CODE=$?
echo "Finalizado con codigo: $EXIT_CODE"
echo "Log: $LOG_FILE"
exit "$EXIT_CODE"
