# Локальный кластер PostgreSQL для разработки, без Docker.
#
# Примеры:
#   powershell -ExecutionPolicy Bypass -File scripts/dev_db.ps1 init
#   powershell -ExecutionPolicy Bypass -File scripts/dev_db.ps1 start
#   powershell -ExecutionPolicy Bypass -File scripts/dev_db.ps1 stop
param(
    [Parameter(Position = 0)]
    [ValidateSet("init", "start", "stop", "status")]
    [string]$Action = "start",
    [int]$Port = 5433,
    [string]$DataDir = "$env:TEMP\auction-of-words-pg",
    [string]$PgBin = "C:\Program Files\PostgreSQL\13\bin"
)

$ErrorActionPreference = "Stop"

switch ($Action) {
    "init" {
        if (-not (Test-Path "$DataDir\PG_VERSION")) {
            & "$PgBin\initdb.exe" -D $DataDir -U postgres -A trust -E UTF8 --locale=C
        }
        & "$PgBin\pg_ctl.exe" -D $DataDir -o "-p $Port" -l "$DataDir\server.log" -w start
        & "$PgBin\createdb.exe" -h localhost -p $Port -U postgres wordauction 2>$null
        & "$PgBin\createdb.exe" -h localhost -p $Port -U postgres wordauction_test 2>$null
        Write-Host "PostgreSQL запущен на localhost:$Port (БД: wordauction, wordauction_test)"
    }
    "start" {
        & "$PgBin\pg_ctl.exe" -D $DataDir -o "-p $Port" -l "$DataDir\server.log" -w start
    }
    "stop" {
        & "$PgBin\pg_ctl.exe" -D $DataDir -m fast stop
    }
    "status" {
        & "$PgBin\pg_ctl.exe" -D $DataDir status
    }
}
