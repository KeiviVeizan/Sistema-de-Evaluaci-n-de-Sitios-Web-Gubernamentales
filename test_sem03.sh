#!/bin/bash

# Script de prueba automatizado para validador SEM-03
# Ejecuta: chmod +x test_sem03.sh && ./test_sem03.sh

set -e

BASE_URL="http://localhost:8000"
API_PREFIX="/api/v1"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   🧪 PRUEBA AUTOMATIZADA - VALIDADOR SEM-03 MEJORADO         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar progreso
show_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 1. Health check
show_step "PASO 1: Verificando que el servicio está corriendo"
HEALTH=$(curl -s ${BASE_URL}/health)
STATUS=$(echo $HEALTH | jq -r .status)

if [ "$STATUS" == "healthy" ]; then
    echo -e "${GREEN}✅ Servicio operativo${NC}"
else
    echo -e "${RED}❌ Servicio no disponible${NC}"
    echo "Respuesta: $HEALTH"
    exit 1
fi

# 2. Crawlear sitio
show_step "PASO 2: Crawleando sitio web .gob.bo"
echo "Sitio: https://www.migracion.gob.bo"

CRAWL_RESPONSE=$(curl -s -X POST "${BASE_URL}${API_PREFIX}/crawler/crawl" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.migracion.gob.bo", "institution_name": "Dirección General de Migración"}')

WEBSITE_ID=$(echo $CRAWL_RESPONSE | jq -r .website_id)

if [ "$WEBSITE_ID" == "null" ] || [ -z "$WEBSITE_ID" ]; then
    echo -e "${RED}❌ Error en el crawling${NC}"
    echo "Respuesta: $CRAWL_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Crawling exitoso${NC}"
echo "Website ID: $WEBSITE_ID"
echo ""
echo "Resumen del crawling:"
echo $CRAWL_RESPONSE | jq '.summary.semantic_elements, .summary.structure'

# 3. Ver estructura extraída
show_step "PASO 3: Analizando estructura semántica extraída"
CONTENT=$(curl -s "${BASE_URL}${API_PREFIX}/crawler/websites/${WEBSITE_ID}")

echo "📊 Análisis de estructura HTML:"
STRUCTURE_ANALYSIS=$(echo $CONTENT | jq '.structure.document_hierarchy.structure_analysis')
echo "$STRUCTURE_ANALYSIS" | jq .

# Extraer valores clave
MAIN_COUNT=$(echo $STRUCTURE_ANALYSIS | jq -r .main_count)
MAIN_INSIDE_SECTION=$(echo $STRUCTURE_ANALYSIS | jq -r .main_inside_section)
DIV_RATIO=$(echo $STRUCTURE_ANALYSIS | jq -r .div_ratio)
HAS_DIVITIS=$(echo $STRUCTURE_ANALYSIS | jq -r .has_divitis)
NAVS_FLOATING=$(echo $STRUCTURE_ANALYSIS | jq -r .navs_floating)

echo ""
echo "📝 Indicadores clave:"
echo "  • Elementos <main>: $MAIN_COUNT"
echo "  • <main> dentro de <section>: $MAIN_INSIDE_SECTION"
echo "  • Ratio de <div>: $DIV_RATIO"
echo "  • Tiene div-itis: $HAS_DIVITIS"
echo "  • <nav> flotantes: $NAVS_FLOATING"

# 4. Ejecutar evaluación
show_step "PASO 4: Ejecutando evaluación completa"
EVAL_RESPONSE=$(curl -s -X POST "${BASE_URL}${API_PREFIX}/evaluation/evaluate/${WEBSITE_ID}")
EVAL_ID=$(echo $EVAL_RESPONSE | jq -r .evaluation_id)

if [ "$EVAL_ID" == "null" ] || [ -z "$EVAL_ID" ]; then
    echo -e "${RED}❌ Error en la evaluación${NC}"
    echo "Respuesta: $EVAL_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✅ Evaluación completada${NC}"
echo "Evaluation ID: $EVAL_ID"
echo ""
echo "Puntajes generales:"
echo $EVAL_RESPONSE | jq '.scores'

# 5. Obtener resultados de SEM-03
show_step "PASO 5: Resultados del criterio SEM-03"
DIMENSION_RESULTS=$(curl -s "${BASE_URL}${API_PREFIX}/evaluation/results/${EVAL_ID}/dimension/semantica")
SEM03_RESULT=$(echo $DIMENSION_RESULTS | jq '.criteria[] | select(.criteria_id == "SEM-03")')

# Extraer datos de SEM-03
SEM03_STATUS=$(echo $SEM03_RESULT | jq -r .status)
SEM03_SCORE=$(echo $SEM03_RESULT | jq -r .score)
SEM03_MAX_SCORE=$(echo $SEM03_RESULT | jq -r .max_score)
SEM03_PERCENTAGE=$(echo $SEM03_RESULT | jq -r .percentage)

echo "Criterio: SEM-03 - Estructura semántica HTML5"
echo "Lineamiento: HTML5 / W3C"
echo ""

# Mostrar status con color
case $SEM03_STATUS in
    "pass")
        echo -e "Estado: ${GREEN}✅ PASS${NC}"
        ;;
    "partial")
        echo -e "Estado: ${YELLOW}⚠️  PARTIAL${NC}"
        ;;
    "fail")
        echo -e "Estado: ${RED}❌ FAIL${NC}"
        ;;
    *)
        echo "Estado: $SEM03_STATUS"
        ;;
esac

echo "Puntaje: $SEM03_SCORE / $SEM03_MAX_SCORE ($SEM03_PERCENTAGE%)"
echo ""

# Mostrar issues
ISSUES=$(echo $SEM03_RESULT | jq -r '.details.issues[]' 2>/dev/null)
if [ ! -z "$ISSUES" ]; then
    echo -e "${RED}🔍 Problemas detectados:${NC}"
    echo "$ISSUES" | while read -r issue; do
        echo "  ❌ $issue"
    done
    echo ""
fi

# Mostrar recomendaciones
RECOMMENDATIONS=$(echo $SEM03_RESULT | jq -r '.details.recommendations[]' 2>/dev/null)
if [ ! -z "$RECOMMENDATIONS" ]; then
    echo -e "${YELLOW}💡 Recomendaciones:${NC}"
    echo "$RECOMMENDATIONS" | while read -r rec; do
        echo "  → $rec"
    done
    echo ""
fi

# 6. Desglose detallado
show_step "PASO 6: Desglose detallado de la evaluación"
echo "$SEM03_RESULT" | jq '{
    "Evaluación General": {
        status,
        score,
        max_score,
        percentage
    },
    "Análisis de Estructura": .details.structure_analysis,
    "Elementos Presentes": .details.elements_present,
    "Estructura Correcta": .details.structure_correct,
    "Sin Anti-patrones": .details.no_antipatterns
}'

# 7. Comparar con otros criterios de semántica
show_step "PASO 7: Comparación con otros criterios de semántica"
echo $DIMENSION_RESULTS | jq -r '.criteria[] |
    "[\(.criteria_id)] \(.criteria_name): \(.score)/\(.max_score) (\(.percentage)%) - \(.status)"'

# 8. Resumen final
show_step "📊 RESUMEN FINAL DE LA PRUEBA"

echo -e "${BLUE}Website evaluado:${NC}"
echo "  • ID: $WEBSITE_ID"
echo "  • URL: https://www.migracion.gob.bo"
echo ""

echo -e "${BLUE}SEM-03 - Estructura semántica HTML5:${NC}"
echo "  • Puntaje: $SEM03_SCORE / $SEM03_MAX_SCORE ($SEM03_PERCENTAGE%)"
echo "  • Estado: $SEM03_STATUS"
echo "  • Problemas encontrados: $(echo $SEM03_RESULT | jq '.details.issues | length')"
echo ""

echo -e "${BLUE}Indicadores técnicos:${NC}"
echo "  • <main> dentro de <section>: $MAIN_INSIDE_SECTION"
echo "  • Ratio de divs: $DIV_RATIO"
echo "  • Div-itis: $HAS_DIVITIS"
echo "  • Nav flotantes: $NAVS_FLOATING"
echo ""

# Determinar si la prueba fue exitosa
if [ "$SEM03_STATUS" == "pass" ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✅ PRUEBA EXITOSA - Estructura semántica correcta          ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
elif [ "$SEM03_STATUS" == "partial" ]; then
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║   ⚠️  PRUEBA PARCIAL - Estructura mejorable                   ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ❌ PRUEBA FALLIDA - Problemas estructurales detectados      ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
fi

echo ""
echo "🔗 Para ver más detalles:"
echo "   • Contenido extraído: ${BASE_URL}${API_PREFIX}/crawler/websites/${WEBSITE_ID}"
echo "   • Resultados completos: ${BASE_URL}${API_PREFIX}/evaluation/results/${EVAL_ID}"
echo "   • Documentación API: ${BASE_URL}/docs"
echo ""
