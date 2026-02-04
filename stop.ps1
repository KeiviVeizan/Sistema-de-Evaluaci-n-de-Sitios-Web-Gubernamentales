# Script para detener servicios

Write-Host "Deteniendo servicios..." -ForegroundColor Yellow
docker-compose down
Write-Host "OK: Servicios detenidos" -ForegroundColor Green
