# 🧪 GUÍA DE PRUEBAS - VALIDADOR SEM-03 MEJORADO

Esta guía te ayudará a probar la implementación del validador SEM-03 que ahora evalúa la **estructura semántica HTML5 de forma profunda**.

## 📋 PRE-REQUISITOS

✅ Docker corriendo con el backend en `http://localhost:8000`
✅ Base de datos PostgreSQL activa

## 🔍 QUÉ SE IMPLEMENTÓ

El nuevo SEM-03 ahora valida:
1. **Presencia de elementos básicos** (30% = 4.5 puntos)
2. **Estructura jerárquica correcta** (40% = 6 puntos)
3. **Ausencia de anti-patrones** (30% = 4.5 puntos)

### Problemas que detecta:
- ❌ `<main>` dentro de `<section>` (incorrecto)
- ❌ `<nav>` flotantes fuera de `<header>` o `<footer>`
- ❌ Múltiples elementos `<main>` (debe ser único)
- ❌ "Div-itis": exceso de `<div>` (>70%)
- ❌ Falta de `<section>` y `<article>`

---

## 🚀 PRUEBAS PASO A PASO

### PASO 1: Verificar que el servicio está corriendo

```bash
curl http://localhost:8000/health
```

**Resultado esperado:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "...",
  "timestamp": "..."
}
```

---

### PASO 2: Ver documentación de la API

Abre en tu navegador:
```
http://localhost:8000/docs
```

---

### PASO 3: Crawlear un sitio .gob.bo

Elige una de estas opciones:

#### Opción A: Sitio con buena estructura (probablemente)
```bash
curl -X POST "http://localhost:8000/api/v1/crawler/crawl" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://www.migracion.gob.bo\", \"institution_name\": \"Dirección General de Migración\"}"
```

#### Opción B: Sitio del Ministerio de Comunicación
```bash
curl -X POST "http://localhost:8000/api/v1/crawler/crawl" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://www.comunicacion.gob.bo\", \"institution_name\": \"Ministerio de Comunicación\"}"
```

#### Opción C: Sitio de ADSIB
```bash
curl -X POST "http://localhost:8000/api/v1/crawler/crawl" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://adsib.gob.bo\", \"institution_name\": \"Agencia de Desarrollo de la Sociedad de la Información en Bolivia\"}"
```

**Guarda el `website_id` del resultado**, lo necesitarás para el siguiente paso.

**Ejemplo de respuesta:**
```json
{
  "website_id": 1,
  "url": "https://www.migracion.gob.bo",
  "institution_name": "Dirección General de Migración",
  "status": "completed",
  "message": "Crawling completado exitosamente",
  "crawled_at": "2024-01-19T...",
  "summary": {
    "structure": {
      "has_html5_doctype": true,
      "has_utf8_charset": true
    },
    "semantic_elements": {
      "types_used": 4,
      "has_basic_structure": true
    }
  }
}
```

---

### PASO 4: Ver el contenido extraído (incluyendo document_hierarchy)

Reemplaza `{website_id}` con el ID del paso anterior:

```bash
curl "http://localhost:8000/api/v1/crawler/websites/{website_id}" | jq .
```

**Busca en el resultado:**
- `structure.document_hierarchy.hierarchy` - Jerarquía de elementos semánticos
- `structure.document_hierarchy.structure_analysis` - Análisis detallado
  - `main_inside_section` - ¿El main está mal anidado?
  - `navs_floating` - ¿Cuántos nav están flotantes?
  - `div_ratio` - Ratio de divs (0.0 a 1.0)
  - `has_divitis` - ¿Tiene exceso de divs? (>0.7)

**Ejemplo de estructura extraída:**
```json
{
  "structure": {
    "document_hierarchy": {
      "hierarchy": [
        {
          "tag": "header",
          "depth": 0,
          "parent": "body",
          "children": [...]
        }
      ],
      "structure_analysis": {
        "header_count": 1,
        "main_count": 1,
        "footer_count": 1,
        "nav_count": 1,
        "navs_in_header": 1,
        "navs_floating": 0,
        "main_inside_section": false,
        "total_divs": 50,
        "total_semantic": 20,
        "div_ratio": 0.71,
        "has_divitis": true
      }
    }
  }
}
```

---

### PASO 5: Ejecutar la evaluación

Reemplaza `{website_id}` con el ID obtenido:

```bash
curl -X POST "http://localhost:8000/api/v1/evaluation/evaluate/{website_id}"
```

**Guarda el `evaluation_id` del resultado.**

**Ejemplo de respuesta:**
```json
{
  "evaluation_id": 1,
  "website_id": 1,
  "status": "completed",
  "scores": {
    "accesibilidad": 75.5,
    "usabilidad": 82.3,
    "semantica_web": 68.7,
    "soberania_digital": 45.2,
    "total": 71.2
  }
}
```

---

### PASO 6: Ver resultados de SEM-03 específicamente

Reemplaza `{evaluation_id}`:

```bash
curl "http://localhost:8000/api/v1/evaluation/results/{evaluation_id}/dimension/semantica" | jq '.criteria[] | select(.criteria_id == "SEM-03")'
```

**Esto mostrará:**
```json
{
  "criteria_id": "SEM-03",
  "criteria_name": "Estructura semántica HTML5",
  "lineamiento": "HTML5 / W3C",
  "status": "partial",
  "score": 11.5,
  "max_score": 15,
  "percentage": 76.67,
  "details": {
    "percentage": 76.67,
    "elements_present": 4,
    "structure_correct": true,
    "no_antipatterns": false,
    "issues": [
      "<main> está incorrectamente dentro de <section>",
      "Alto uso de <div> (71% del contenido)"
    ],
    "recommendations": [
      "Mover <main> fuera de <section>. Estructura correcta: <main> contiene <section>, no al revés",
      "Considerar usar más elementos semánticos HTML5"
    ],
    "structure_analysis": {
      "header_count": 1,
      "main_count": 1,
      "footer_count": 1,
      "nav_count": 1,
      "navs_in_header": 1,
      "navs_floating": 0,
      "main_inside_section": true,
      "total_divs": 150,
      "total_semantic": 50,
      "div_ratio": 0.75,
      "has_divitis": true
    }
  },
  "evidence": {
    "hierarchy": [...]
  }
}
```

---

### PASO 7: Ver todos los resultados de la dimensión semántica

```bash
curl "http://localhost:8000/api/v1/evaluation/results/{evaluation_id}/dimension/semantica" | jq .
```

Esto te mostrará todos los criterios de semántica (SEM-01, SEM-02, **SEM-03**, SEM-04, etc.)

---

## 📊 INTERPRETANDO LOS RESULTADOS DE SEM-03

### ✅ PASS (90-100%)
```json
{
  "status": "pass",
  "score": 14.5,
  "percentage": 96.67,
  "issues": [],
  "recommendations": []
}
```
**Significado:** Estructura semántica excelente, sigue estándares W3C.

---

### ⚠️ PARTIAL (70-89%)
```json
{
  "status": "partial",
  "score": 11.5,
  "percentage": 76.67,
  "issues": [
    "Alto uso de <div> (55% del contenido)"
  ],
  "recommendations": [
    "Considerar usar más elementos semánticos HTML5"
  ]
}
```
**Significado:** Estructura básica correcta, pero mejorable.

---

### ❌ FAIL (<70%)
```json
{
  "status": "fail",
  "score": 9.0,
  "percentage": 60.0,
  "issues": [
    "Falta elemento <main>",
    "<main> está incorrectamente dentro de <section>",
    "Todos los <nav> están fuera de <header>/<footer>",
    "Exceso de <div> genéricos (75% del contenido)"
  ],
  "recommendations": [
    "Agregar <main> único para el contenido principal",
    "Mover <main> fuera de <section>. Estructura correcta: <main> contiene <section>, no al revés",
    "Colocar <nav> dentro de <header> para mejor semántica",
    "Reemplazar <div> por elementos semánticos donde sea apropiado (<section>, <article>, <aside>)"
  ]
}
```
**Significado:** Múltiples problemas estructurales que deben corregirse.

---

## 🎯 CASOS DE PRUEBA ESPECÍFICOS

### Caso 1: Verificar detección de main dentro de section

```bash
# 1. Crawlear el sitio
WEBSITE_ID=$(curl -s -X POST "http://localhost:8000/api/v1/crawler/crawl" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://tu-sitio.gob.bo\", \"institution_name\": \"Test\"}" | jq -r .website_id)

# 2. Ver si tiene el problema
curl -s "http://localhost:8000/api/v1/crawler/websites/$WEBSITE_ID" | \
  jq '.structure.document_hierarchy.structure_analysis.main_inside_section'

# 3. Evaluar
EVAL_ID=$(curl -s -X POST "http://localhost:8000/api/v1/evaluation/evaluate/$WEBSITE_ID" | jq -r .evaluation_id)

# 4. Ver resultado de SEM-03
curl -s "http://localhost:8000/api/v1/evaluation/results/$EVAL_ID/dimension/semantica" | \
  jq '.criteria[] | select(.criteria_id == "SEM-03") | .details.issues'
```

---

### Caso 2: Verificar detección de div-itis

```bash
# Ver el ratio de divs del último sitio crawleado
curl -s "http://localhost:8000/api/v1/crawler/websites/$WEBSITE_ID" | \
  jq '.structure.document_hierarchy.structure_analysis | {div_ratio, has_divitis, total_divs, total_semantic}'
```

---

### Caso 3: Listar todos los sitios evaluados

```bash
curl "http://localhost:8000/api/v1/crawler/websites" | jq '.items[] | {id, url, crawl_status, last_crawled_at}'
```

---

## 🐛 TROUBLESHOOTING

### Problema: "Error durante el crawling"
```bash
# Ver logs del contenedor Docker
docker logs gob-bo-evaluator-backend -f
```

### Problema: "Sitio web no encontrado"
```bash
# Listar todos los sitios
curl "http://localhost:8000/api/v1/crawler/websites" | jq .
```

### Problema: "No se encontró contenido extraído"
```bash
# Verificar estado del crawling
curl "http://localhost:8000/api/v1/crawler/websites/{website_id}" | jq '.crawl_status'
```

---

## 📝 PRUEBA COMPLETA DE EXTREMO A EXTREMO

Copia y pega este script completo:

```bash
#!/bin/bash

echo "🚀 Iniciando prueba completa de SEM-03..."
echo ""

# 1. Health check
echo "1️⃣ Verificando servicio..."
curl -s http://localhost:8000/health | jq .status
echo ""

# 2. Crawlear sitio
echo "2️⃣ Crawleando sitio..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/crawler/crawl" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.migracion.gob.bo", "institution_name": "Dirección General de Migración"}')

WEBSITE_ID=$(echo $RESPONSE | jq -r .website_id)
echo "✅ Website ID: $WEBSITE_ID"
echo ""

# 3. Ver análisis de estructura
echo "3️⃣ Análisis de estructura HTML:"
curl -s "http://localhost:8000/api/v1/crawler/websites/$WEBSITE_ID" | \
  jq '.structure.document_hierarchy.structure_analysis'
echo ""

# 4. Evaluar
echo "4️⃣ Evaluando sitio..."
EVAL_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/evaluation/evaluate/$WEBSITE_ID")
EVAL_ID=$(echo $EVAL_RESPONSE | jq -r .evaluation_id)
echo "✅ Evaluation ID: $EVAL_ID"
echo ""

# 5. Ver resultado de SEM-03
echo "5️⃣ Resultado de SEM-03:"
curl -s "http://localhost:8000/api/v1/evaluation/results/$EVAL_ID/dimension/semantica" | \
  jq '.criteria[] | select(.criteria_id == "SEM-03") | {
    criteria_id,
    status,
    score,
    max_score,
    percentage,
    issues: .details.issues,
    recommendations: .details.recommendations
  }'

echo ""
echo "✨ Prueba completada!"
```

Guarda esto como `test_sem03.sh` y ejecútalo:
```bash
chmod +x test_sem03.sh
./test_sem03.sh
```

---

## ✅ CHECKLIST DE VALIDACIÓN

Verifica que el nuevo SEM-03 está funcionando correctamente:

- [ ] El crawler extrae `document_hierarchy` en la estructura
- [ ] `structure_analysis` contiene todos los campos esperados
- [ ] SEM-03 tiene `max_score: 15` (no 8)
- [ ] El status puede ser: `pass`, `partial`, o `fail`
- [ ] Los `issues` son específicos y descriptivos
- [ ] Las `recommendations` son accionables
- [ ] Detecta `main_inside_section` correctamente
- [ ] Detecta `div-itis` (ratio > 0.7)
- [ ] Detecta `navs_floating`
- [ ] Los puntajes reflejan los problemas encontrados

---

## 🎓 EJEMPLOS DE RESULTADOS REALES

### Sitio con BUENA estructura (hipotético):
```json
{
  "score": 15.0,
  "percentage": 100.0,
  "status": "pass",
  "structure_analysis": {
    "main_count": 1,
    "main_inside_section": false,
    "navs_floating": 0,
    "div_ratio": 0.35,
    "has_divitis": false
  }
}
```

### Sitio con PROBLEMAS (hipotético):
```json
{
  "score": 10.0,
  "percentage": 66.67,
  "status": "fail",
  "issues": [
    "<main> está incorrectamente dentro de <section>",
    "Exceso de <div> genéricos (75% del contenido)"
  ],
  "structure_analysis": {
    "main_count": 1,
    "main_inside_section": true,
    "navs_floating": 0,
    "div_ratio": 0.75,
    "has_divitis": true
  }
}
```

---

## 📞 NECESITAS AYUDA

Si encuentras problemas:
1. Revisa los logs de Docker
2. Verifica que el sitio sea `.gob.bo` válido
3. Asegúrate de que el sitio esté accesible
4. Revisa que el puerto 8000 esté disponible

¡Listo para probar! 🚀
