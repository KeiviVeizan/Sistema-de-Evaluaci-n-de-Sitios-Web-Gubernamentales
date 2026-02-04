# Script de inicializacion para desarrollo local

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  ADSIB GOB.BO EVALUATOR - INICIALIZACION" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Paso 1: Verificar Docker
Write-Host "[1/5] Verificando Docker..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker no esta corriendo. Inicia Docker Desktop primero." -ForegroundColor Red
    exit 1
}
Write-Host "OK: Docker esta corriendo" -ForegroundColor Green

# Paso 2: Levantar servicios con Docker Compose
Write-Host ""
Write-Host "[2/5] Levantando PostgreSQL + Redis..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Error al levantar servicios" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Servicios levantados" -ForegroundColor Green

# Paso 3: Esperar a que servicios esten listos
Write-Host ""
Write-Host "[3/5] Esperando que servicios esten listos..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar PostgreSQL
$pgReady = docker exec gob_evaluator_db pg_isready -U gob_admin 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARN: PostgreSQL aun no esta listo, esperando..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}
Write-Host "OK: PostgreSQL listo" -ForegroundColor Green

# Verificar Redis
$redisReady = docker exec gob_evaluator_cache redis-cli ping 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARN: Redis aun no esta listo, esperando..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}
Write-Host "OK: Redis listo" -ForegroundColor Green

# Paso 4: Instalar dependencias Python
Write-Host ""
Write-Host "[4/5] Instalando dependencias Python..." -ForegroundColor Yellow
Set-Location backend
pip install -r requirements.txt -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Error al instalar dependencias" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Dependencias instaladas" -ForegroundColor Green

# Paso 5: Iniciar servidor FastAPI
Write-Host ""
Write-Host "[5/5] Iniciando servidor FastAPI..." -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  SERVIDOR LISTO" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Swagger UI:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "Health:      http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
Write-Host ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
