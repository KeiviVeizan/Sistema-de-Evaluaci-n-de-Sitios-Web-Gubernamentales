#!/bin/bash
# ============================================================================
# Script para ejecutar migración NLP Analysis en Docker
# ============================================================================
# Proyecto: GOB.BO Evaluator
# Descripción: Ejecuta la migración SQL dentro del contenedor PostgreSQL
# Uso: ./run_migration_docker.sh
# ============================================================================

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sin color

# Configuración
CONTAINER_NAME="gob-bo-evaluator-postgres"  # Ajustar según docker-compose.yml
DB_NAME="${POSTGRES_DB:-gob_bo_evaluator}"
DB_USER="${POSTGRES_USER:-postgres}"
MIGRATION_FILE="migrations/001_create_nlp_analysis.sql"

echo -e "${YELLOW}============================================${NC}"
echo -e "${YELLOW}  Migración NLP Analysis - Docker${NC}"
echo -e "${YELLOW}============================================${NC}"

# ============================================================================
# PASO 1: Verificar que Docker está corriendo
# ============================================================================
echo -e "\n${YELLOW}[1/4] Verificando Docker...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker no está instalado${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Docker daemon no está corriendo${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker está corriendo${NC}"

# ============================================================================
# PASO 2: Verificar que el contenedor PostgreSQL está corriendo
# ============================================================================
echo -e "\n${YELLOW}[2/4] Verificando contenedor PostgreSQL...${NC}"

# Intentar encontrar el contenedor por nombre parcial
FOUND_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E "postgres|db" | head -1)

if [ -z "$FOUND_CONTAINER" ]; then
    echo -e "${RED}Error: No se encontró contenedor PostgreSQL corriendo${NC}"
    echo -e "${YELLOW}Contenedores disponibles:${NC}"
    docker ps --format '{{.Names}}'
    echo -e "\n${YELLOW}Sugerencia: Ejecutar 'docker-compose up -d' primero${NC}"
    exit 1
fi

CONTAINER_NAME=$FOUND_CONTAINER
echo -e "${GREEN}✓ Contenedor encontrado: ${CONTAINER_NAME}${NC}"

# ============================================================================
# PASO 3: Verificar que el archivo de migración existe
# ============================================================================
echo -e "\n${YELLOW}[3/4] Verificando archivo de migración...${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
MIGRATION_PATH="${BACKEND_DIR}/${MIGRATION_FILE}"

if [ ! -f "$MIGRATION_PATH" ]; then
    echo -e "${RED}Error: Archivo de migración no encontrado${NC}"
    echo -e "${RED}Buscado en: ${MIGRATION_PATH}${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Archivo de migración encontrado${NC}"

# ============================================================================
# PASO 4: Ejecutar migración
# ============================================================================
echo -e "\n${YELLOW}[4/4] Ejecutando migración...${NC}"

# Copiar archivo al contenedor
echo "  - Copiando archivo al contenedor..."
docker cp "$MIGRATION_PATH" "${CONTAINER_NAME}:/tmp/001_create_nlp_analysis.sql"

# Ejecutar migración
echo "  - Ejecutando SQL..."
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -f /tmp/001_create_nlp_analysis.sql

# Limpiar
docker exec "$CONTAINER_NAME" rm -f /tmp/001_create_nlp_analysis.sql

# ============================================================================
# VERIFICACIÓN FINAL
# ============================================================================
echo -e "\n${YELLOW}============================================${NC}"
echo -e "${YELLOW}  Verificación Final${NC}"
echo -e "${YELLOW}============================================${NC}"

# Verificar que la tabla existe
echo -e "\n${YELLOW}Verificando tabla nlp_analysis...${NC}"
TABLE_EXISTS=$(docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'nlp_analysis');")

if [ "$TABLE_EXISTS" = "t" ]; then
    echo -e "${GREEN}✓ Tabla nlp_analysis creada exitosamente${NC}"
else
    echo -e "${RED}✗ Error: Tabla nlp_analysis no encontrada${NC}"
    exit 1
fi

# Mostrar estructura de la tabla
echo -e "\n${YELLOW}Estructura de la tabla:${NC}"
docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "\d nlp_analysis"

# Contar índices
INDEX_COUNT=$(docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -tAc \
    "SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'nlp_analysis';")

echo -e "\n${GREEN}✓ ${INDEX_COUNT} índices creados${NC}"

# ============================================================================
# RESUMEN
# ============================================================================
echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}  MIGRACIÓN COMPLETADA EXITOSAMENTE${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "
Tabla: nlp_analysis
Índices: ${INDEX_COUNT}
Contenedor: ${CONTAINER_NAME}
Base de datos: ${DB_NAME}
"
