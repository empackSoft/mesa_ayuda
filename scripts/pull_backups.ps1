# Copia a esta PC (OneDrive) los respaldos más recientes que backup.sh deja en el VPS.
# Así hay una copia fuera del servidor si el VPS se pierde (como el 15/nov).
#
# Requiere el alias "vps-mesa" en ~/.ssh/config (llave id_ed25519_vps_mesa, sin contraseña).
# Se corre desde el Programador de tareas de Windows todos los días (ver CONTEXTO_PROYECTO.md).

$ErrorActionPreference = 'Stop'
# Se usa el ssh de Git: ESET bloquea el de Windows (System32\OpenSSH) y da "Connection timed out".
$Ssh      = 'C:\Program Files\Git\usr\bin\ssh.exe'
$Scp      = 'C:\Program Files\Git\usr\bin\scp.exe'
$Remote   = '/opt/mesa_ayuda/backups'
$Dest     = Join-Path $PSScriptRoot '..\..\respaldos_vps'
$KeepDays = 30
$Log      = Join-Path $Dest 'pull_backups.log'

New-Item -ItemType Directory -Force $Dest | Out-Null
function Write-Log($msg) { "[{0:yyyy-MM-dd HH:mm:ss}] $msg" -f (Get-Date) | Tee-Object -FilePath $Log -Append }

try {
    # El respaldo más nuevo de cada tipo
    $files = & $Ssh -o BatchMode=yes vps-mesa "ls -1t $Remote/mesa_db_*.sql.gz | head -1; ls -1t $Remote/uploads_*.tar.gz | head -1"
    if ($LASTEXITCODE -ne 0 -or -not $files) { throw "No se pudo listar los respaldos del VPS" }

    foreach ($f in $files) {
        $name = Split-Path $f -Leaf
        $local = Join-Path $Dest $name
        if (Test-Path $local) { Write-Log "Ya estaba: $name"; continue }
        & $Scp -q -o BatchMode=yes "vps-mesa:$f" "$local.tmp"
        if ($LASTEXITCODE -ne 0) { throw "Falló la copia de $name" }
        Move-Item -Force "$local.tmp" $local
        Write-Log ("Copiado: {0} ({1:N1} MB)" -f $name, ((Get-Item $local).Length / 1MB))
    }

    Get-ChildItem $Dest -File | Where-Object {
        $_.Name -match '^(mesa_db_.*\.sql\.gz|uploads_.*\.tar\.gz)$' -and $_.LastWriteTime -lt (Get-Date).AddDays(-$KeepDays)
    } | ForEach-Object { Remove-Item $_.FullName; Write-Log "Borrado (viejo): $($_.Name)" }
}
catch {
    Write-Log "ERROR: $_"
    exit 1
}
