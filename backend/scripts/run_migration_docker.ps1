# ============================================================================
# Script para ejecutar migración NLP Analysis en Docker (Windows PowerShell)
# ============================================================================
# Proyecto: GOB.BO Evaluator
# Descripción: Ejecuta la migración SQL dentro del contenedor PostgreSQL
# Uso: .\run_migration_docker.ps1
# ============================================================================

$ErrorActionPreference = "Stop"

# Configuración
$CONTAINER_NAME = "gob-bo-evaluator-postgres"
$DB_NAME = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "gob_bo_evaluator" }
$DB_USER = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "postgres" }

Write-Host "============================================" -ForegroundColor Yellow
Write-Host "  Migración NLP Analysis - Docker" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Yellow

# ============================================================================
# PASO 1: Verificar que Docker está corriendo
# ============================================================================
Write-Host "`n[1/4] Verificando Docker..." -ForegroundColor Yellow

try {
    docker info 2>&1 | Out-Null
    Write-Host "OK - Docker está corriendo" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker no está corriendo" -ForegroundColor Red
    exit 1
}

# ============================================================================
# PASO 2: Buscar contenedor PostgreSQL
# ============================================================================
Write-Host "`n[2/4] Buscando contenedor PostgreSQL..." -ForegroundColor Yellow

$containers = docker ps --format '{{.Names}}' | Select-String -Pattern "postgres|db"
if ($containers) {
    $CONTAINER_NAME = $containers[0].Line
    Write-Host "OK - Contenedor encontrado: $CONTAINER_NAME" -ForegroundColor Green
} else {
    Write-Host "Error: No se encontró contenedor PostgreSQL" -ForegroundColor Red
    Write-Host "Contenedores disponibles:"
    docker ps --format '{{.Names}}'
    Write-Host "`nSugerencia: Ejecutar 'docker-compose up -d' primero" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# PASO 3: Verificar archivo de migración
# ============================================================================
Write-Host "`n[3/4] Verificando archivo de migración..." -ForegroundColor Yellow

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir
$MigrationPath = Join-Path $BackendDir "migrations\001_create_nlp_analysis.sql"

if (Test-Path $MigrationPath) {
    Write-Host "OK - Archivo de migración encontrado" -ForegroundColor Green
} else {
    Write-Host "Error: Archivo no encontrado en: $MigrationPath" -ForegroundColor Red
    exit 1
}

# ============================================================================
# PASO 4: Ejecutar migración
# ============================================================================
Write-Host "`n[4/4] Ejecutando migración..." -ForegroundColor Yellow

# Copiar archivo al contenedor
Write-Host "  - Copiando archivo al contenedor..."
docker cp $MigrationPath "${CONTAINER_NAME}:/tmp/001_create_nlp_analysis.sql"

# Ejecutar migración
Write-Host "  - Ejecutando SQL..."
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /tmp/001_create_nlp_analysis.sql

# Limpiar
docker exec $CONTAINER_NAME rm -f /tmp/001_create_nlp_analysis.sql

# ============================================================================
# VERIFICACIÓN FINAL
# ============================================================================
Write-Host "`n============================================" -ForegroundColor Yellow
Write-Host "  Verificación Final" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Yellow

# Verificar que la tabla existe
Write-Host "`nVerificando tabla nlp_analysis..." -ForegroundColor Yellow
$tableExists = docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -tAc "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'nlp_analysis');"

if ($tableExists.Trim() -eq "t") {
    Write-Host "OK - Tabla nlp_analysis creada exitosamente" -ForegroundColor Green
} else {
    Write-Host "Error: Tabla nlp_analysis no encontrada" -ForegroundColor Red
    exit 1
}

# Mostrar estructura
Write-Host "`nEstructura de la tabla:" -ForegroundColor Yellow
docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "\d nlp_analysis"

# Contar índices
$indexCount = docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -tAc "SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'nlp_analysis';"
Write-Host "`nOK - $($indexCount.Trim()) índices creados" -ForegroundColor Green

# ============================================================================
# RESUMEN
# ============================================================================
Write-Host "`n============================================" -ForegroundColor Green
Write-Host "  MIGRACIÓN COMPLETADA EXITOSAMENTE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host @"

Tabla: nlp_analysis
Índices: $($indexCount.Trim())
Contenedor: $CONTAINER_NAME
Base de datos: $DB_NAME

"@
