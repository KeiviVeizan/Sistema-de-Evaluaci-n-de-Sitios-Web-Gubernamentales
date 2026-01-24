# Script de prueba automatizado para validador SEM-03 (PowerShell)
# Ejecuta: .\test_sem03.ps1

$ErrorActionPreference = "Stop"
$BASE_URL = "http://localhost:8000"
$API_PREFIX = "/api/v1"

function Show-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
}

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   🧪 PRUEBA AUTOMATIZADA - VALIDADOR SEM-03 MEJORADO         ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# 1. Health check
Show-Step "PASO 1: Verificando que el servicio está corriendo"
try {
    $health = Invoke-RestMethod -Uri "$BASE_URL/health" -Method Get
    if ($health.status -eq "healthy") {
        Write-Host "✅ Servicio operativo" -ForegroundColor Green
    } else {
        Write-Host "❌ Servicio no disponible" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ No se pudo conectar al servicio en $BASE_URL" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# 2. Crawlear sitio
Show-Step "PASO 2: Crawleando sitio web .gob.bo"
Write-Host "Sitio: https://www.migracion.gob.bo"

$crawlBody = @{
    url = "https://www.migracion.gob.bo"
    institution_name = "Dirección General de Migración"
} | ConvertTo-Json

try {
    $crawlResponse = Invoke-RestMethod -Uri "$BASE_URL$API_PREFIX/crawler/crawl" `
        -Method Post `
        -ContentType "application/json" `
        -Body $crawlBody

    $WEBSITE_ID = $crawlResponse.website_id

    if (-not $WEBSITE_ID) {
        Write-Host "❌ Error en el crawling" -ForegroundColor Red
        Write-Host ($crawlResponse | ConvertTo-Json -Depth 10)
        exit 1
    }

    Write-Host "✅ Crawling exitoso" -ForegroundColor Green
    Write-Host "Website ID: $WEBSITE_ID"
    Write-Host ""
    Write-Host "Resumen del crawling:"
    Write-Host ($crawlResponse.summary | ConvertTo-Json -Depth 5)
} catch {
    Write-Host "❌ Error durante el crawling" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# 3. Ver estructura extraída
Show-Step "PASO 3: Analizando estructura semántica extraída"
try {
    $content = Invoke-RestMethod -Uri "$BASE_URL$API_PREFIX/crawler/websites/$WEBSITE_ID" -Method Get

    Write-Host "📊 Análisis de estructura HTML:"
    $structureAnalysis = $content.structure.document_hierarchy.structure_analysis
    Write-Host ($structureAnalysis | ConvertTo-Json -Depth 5)

    Write-Host ""
    Write-Host "📝 Indicadores clave:"
    Write-Host "  • Elementos <main>: $($structureAnalysis.main_count)"
    Write-Host "  • <main> dentro de <section>: $($structureAnalysis.main_inside_section)"
    Write-Host "  • Ratio de <div>: $($structureAnalysis.div_ratio)"
    Write-Host "  • Tiene div-itis: $($structureAnalysis.has_divitis)"
    Write-Host "  • <nav> flotantes: $($structureAnalysis.navs_floating)"
} catch {
    Write-Host "❌ Error al obtener contenido extraído" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# 4. Ejecutar evaluación
Show-Step "PASO 4: Ejecutando evaluación completa"
try {
    $evalResponse = Invoke-RestMethod -Uri "$BASE_URL$API_PREFIX/evaluation/evaluate/$WEBSITE_ID" `
        -Method Post

    $EVAL_ID = $evalResponse.evaluation_id

    if (-not $EVAL_ID) {
        Write-Host "❌ Error en la evaluación" -ForegroundColor Red
        Write-Host ($evalResponse | ConvertTo-Json -Depth 10)
        exit 1
    }

    Write-Host "✅ Evaluación completada" -ForegroundColor Green
    Write-Host "Evaluation ID: $EVAL_ID"
    Write-Host ""
    Write-Host "Puntajes generales:"
    Write-Host ($evalResponse.scores | ConvertTo-Json -Depth 3)
} catch {
    Write-Host "❌ Error durante la evaluación" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# 5. Obtener resultados de SEM-03
Show-Step "PASO 5: Resultados del criterio SEM-03"
try {
    $dimensionResults = Invoke-RestMethod -Uri "$BASE_URL$API_PREFIX/evaluation/results/$EVAL_ID/dimension/semantica" `
        -Method Get

    $sem03Result = $dimensionResults.criteria | Where-Object { $_.criteria_id -eq "SEM-03" }

    Write-Host "Criterio: SEM-03 - Estructura semántica HTML5"
    Write-Host "Lineamiento: HTML5 / W3C"
    Write-Host ""

    # Mostrar status con color
    switch ($sem03Result.status) {
        "pass" {
            Write-Host "Estado: ✅ PASS" -ForegroundColor Green
        }
        "partial" {
            Write-Host "Estado: ⚠️  PARTIAL" -ForegroundColor Yellow
        }
        "fail" {
            Write-Host "Estado: ❌ FAIL" -ForegroundColor Red
        }
        default {
            Write-Host "Estado: $($sem03Result.status)"
        }
    }

    Write-Host "Puntaje: $($sem03Result.score) / $($sem03Result.max_score) ($($sem03Result.percentage)%)"
    Write-Host ""

    # Mostrar issues
    if ($sem03Result.details.issues -and $sem03Result.details.issues.Count -gt 0) {
        Write-Host "🔍 Problemas detectados:" -ForegroundColor Red
        foreach ($issue in $sem03Result.details.issues) {
            Write-Host "  ❌ $issue"
        }
        Write-Host ""
    }

    # Mostrar recomendaciones
    if ($sem03Result.details.recommendations -and $sem03Result.details.recommendations.Count -gt 0) {
        Write-Host "💡 Recomendaciones:" -ForegroundColor Yellow
        foreach ($rec in $sem03Result.details.recommendations) {
            Write-Host "  → $rec"
        }
        Write-Host ""
    }
} catch {
    Write-Host "❌ Error al obtener resultados de SEM-03" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# 6. Desglose detallado
Show-Step "PASO 6: Desglose detallado de la evaluación"
Write-Host ($sem03Result | Select-Object @{N='Status';E={$_.status}},
                                         @{N='Score';E={$_.score}},
                                         @{N='MaxScore';E={$_.max_score}},
                                         @{N='Percentage';E={$_.percentage}},
                                         @{N='ElementsPresent';E={$_.details.elements_present}},
                                         @{N='StructureCorrect';E={$_.details.structure_correct}},
                                         @{N='NoAntipatterns';E={$_.details.no_antipatterns}} |
                Format-List)

Write-Host "Análisis de estructura:"
Write-Host ($sem03Result.details.structure_analysis | ConvertTo-Json -Depth 3)

# 7. Comparar con otros criterios
Show-Step "PASO 7: Comparación con otros criterios de semántica"
foreach ($criteria in $dimensionResults.criteria) {
    $statusEmoji = switch ($criteria.status) {
        "pass" { "✅" }
        "partial" { "⚠️ " }
        "fail" { "❌" }
        default { "  " }
    }
    Write-Host "$statusEmoji [$($criteria.criteria_id)] $($criteria.criteria_name): $($criteria.score)/$($criteria.max_score) ($($criteria.percentage)%)"
}

# 8. Resumen final
Show-Step "📊 RESUMEN FINAL DE LA PRUEBA"

Write-Host "Website evaluado:" -ForegroundColor Blue
Write-Host "  • ID: $WEBSITE_ID"
Write-Host "  • URL: https://www.migracion.gob.bo"
Write-Host ""

Write-Host "SEM-03 - Estructura semántica HTML5:" -ForegroundColor Blue
Write-Host "  • Puntaje: $($sem03Result.score) / $($sem03Result.max_score) ($($sem03Result.percentage)%)"
Write-Host "  • Estado: $($sem03Result.status)"
Write-Host "  • Problemas encontrados: $($sem03Result.details.issues.Count)"
Write-Host ""

Write-Host "Indicadores técnicos:" -ForegroundColor Blue
Write-Host "  • <main> dentro de <section>: $($structureAnalysis.main_inside_section)"
Write-Host "  • Ratio de divs: $($structureAnalysis.div_ratio)"
Write-Host "  • Div-itis: $($structureAnalysis.has_divitis)"
Write-Host "  • Nav flotantes: $($structureAnalysis.navs_floating)"
Write-Host ""

# Resultado final
switch ($sem03Result.status) {
    "pass" {
        Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║   ✅ PRUEBA EXITOSA - Estructura semántica correcta          ║" -ForegroundColor Green
        Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    }
    "partial" {
        Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
        Write-Host "║   ⚠️  PRUEBA PARCIAL - Estructura mejorable                   ║" -ForegroundColor Yellow
        Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
    }
    "fail" {
        Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Red
        Write-Host "║   ❌ PRUEBA FALLIDA - Problemas estructurales detectados      ║" -ForegroundColor Red
        Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🔗 Para ver más detalles:"
Write-Host "   • Contenido extraído: $BASE_URL$API_PREFIX/crawler/websites/$WEBSITE_ID"
Write-Host "   • Resultados completos: $BASE_URL$API_PREFIX/evaluation/results/$EVAL_ID"
Write-Host "   • Documentación API: $BASE_URL/docs"
Write-Host ""
