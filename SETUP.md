# Guia de Instalacion - ADSIB GOB.BO Evaluator

## Prerrequisitos

- Python 3.10+
- Docker Desktop
- Git

## Instalacion Rapida

### 1. Levantar servicios (PostgreSQL + Redis)
```powershell
docker-compose up -d
```

### 2. Instalar dependencias Python
```bash
cd backend
pip install -r requirements.txt
```

### 3. Iniciar servidor
```bash
uvicorn app.main:app --reload
```

### 4. Verificar
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs

## Uso con Scripts

```powershell
# Iniciar todo
.\start.ps1

# Detener servicios
.\stop.ps1
```

## Verificar Servicios

```bash
# Ver contenedores corriendo
docker-compose ps

# Ver logs de PostgreSQL
docker logs gob_evaluator_db

# Ver logs de Redis
docker logs gob_evaluator_cache
```

## Health Check

El endpoint `/health` retorna:

- **healthy**: Todo funciona correctamente
- **degraded**: PostgreSQL OK, Redis no disponible (sistema sigue funcionando)
- **critical**: PostgreSQL no disponible

Ejemplo respuesta healthy:
```json
{
  "status": "healthy",
  "components": {
    "database": {
      "status": "connected",
      "healthy": true,
      "critical": true
    },
    "redis": {
      "status": "connected",
      "healthy": true,
      "critical": false,
      "stats": {
        "used_memory": "2.5M",
        "total_keys": 0
      }
    }
  },
  "message": "Sistema operativo"
}
```

## Troubleshooting

### Redis no conecta
```bash
docker logs gob_evaluator_cache
docker restart gob_evaluator_cache
```

### PostgreSQL no conecta
```bash
docker logs gob_evaluator_db
docker restart gob_evaluator_db
```

### Reiniciar todo
```bash
docker-compose down
docker-compose up -d
```

### Limpiar volumes (BORRA DATOS)
```bash
docker-compose down -v
docker-compose up -d
```

## Puertos

| Servicio   | Puerto |
|------------|--------|
| FastAPI    | 8000   |
| PostgreSQL | 5432   |
| Redis      | 6379   |

## Variables de Entorno

Ver archivo `backend/.env` para configuracion completa.

Principales:
- `DATABASE_URL`: Conexion PostgreSQL
- `REDIS_URL`: Conexion Redis
- `DEBUG`: Modo debug (true/false)
