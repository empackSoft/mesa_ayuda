#!/usr/bin/env bash
# Respaldo diario de la Mesa de Ayuda: base de datos (pg_dump) + adjuntos.
# Se corre en el VPS (no dentro de Docker) desde cron, todos los días a las 12:00 am:
#
#   crontab -e
#   0 0 * * * bash /ruta/a/mesa_ayuda/scripts/backup.sh >> /var/log/mesa_ayuda_backup.log 2>&1
#
# Variables opcionales (en el crontab o al correrlo a mano):
#   BACKUP_DIR  carpeta destino            (por defecto: <proyecto>/backups, ignorada por git)
#   KEEP_DAYS   días que se conservan      (por defecto: 14)
#
# Restaurar la base (sobre una base vacía, con los contenedores arriba):
#   gunzip -c backups/mesa_db_AAAA-MM-DD_HHMM.sql.gz | docker compose exec -T postgres psql -U admin_mesa -d mesa_db
# Restaurar los adjuntos:
#   tar -xzf backups/uploads_AAAA-MM-DD_HHMM.tar.gz -C backend/app
#
# OJO: un respaldo en el mismo servidor no protege si se pierde el servidor.
# Conviene copiar la carpeta de respaldos a otro lado (otro servidor, OneDrive, etc.).

set -euo pipefail

# cron arranca con un PATH mínimo
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"
STAMP="$(date +%Y-%m-%d_%H%M)"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

cd "$PROJECT_DIR"
mkdir -p "$BACKUP_DIR"

# Evita que dos respaldos corran a la vez (si uno se tarda más de lo normal).
# flock viene en Linux (util-linux); si no existe (ej. Git Bash en Windows) se omite.
if command -v flock >/dev/null 2>&1; then
    exec 9>"$BACKUP_DIR/.backup.lock"
    if ! flock -n 9; then
        log "Ya hay un respaldo en curso; se omite este."
        exit 0
    fi
fi

log "Inicio del respaldo en $BACKUP_DIR"

# 1) Base de datos. Se escribe a un temporal y se renombra al final:
#    así nunca queda un respaldo a medias con nombre de bueno.
DB_FILE="$BACKUP_DIR/mesa_db_$STAMP.sql.gz"
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-privileges' \
    | gzip -9 > "$DB_FILE.tmp"
gzip -t "$DB_FILE.tmp"
mv "$DB_FILE.tmp" "$DB_FILE"
log "Base de datos: $DB_FILE ($(du -h "$DB_FILE" | cut -f1))"

# 2) Adjuntos de los tickets
UPLOADS_FILE="$BACKUP_DIR/uploads_$STAMP.tar.gz"
tar -czf "$UPLOADS_FILE.tmp" -C backend/app uploads
mv "$UPLOADS_FILE.tmp" "$UPLOADS_FILE"
log "Adjuntos: $UPLOADS_FILE ($(du -h "$UPLOADS_FILE" | cut -f1))"

# 3) Limpieza: se borran los respaldos con más de KEEP_DAYS días
find "$BACKUP_DIR" -maxdepth 1 -type f \( -name 'mesa_db_*.sql.gz' -o -name 'uploads_*.tar.gz' \) \
    -mtime +"$KEEP_DAYS" -print -delete | sed 's/^/Borrado (viejo): /'

log "Respaldo terminado"
