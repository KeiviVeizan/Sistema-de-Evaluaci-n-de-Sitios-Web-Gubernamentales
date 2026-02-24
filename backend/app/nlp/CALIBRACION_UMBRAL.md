# Calibración del Umbral de Coherencia Semántica

## Resumen

El sistema de evaluación de coherencia semántica utiliza un **umbral calibrado de 0.80** para clasificar la coherencia entre encabezados y contenido en sitios web gubernamentales.

Este umbral fue determinado mediante un proceso de calibración experimental riguroso utilizando el modelo BETO (BERT para español).

---

## Métricas del Umbral Óptimo

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| **Umbral (θ)** | **0.80** | Valor de corte óptimo para similitud coseno |
| **Precisión** | 85.39% | 85.39% de lo clasificado como coherente es realmente coherente |
| **Recall** | 83.36% | 83.36% de los casos coherentes son detectados correctamente |
| **F1-Score** | 84.37% | Balance óptimo entre precisión y recall |
| **Accuracy** | 84.18% | Exactitud general del clasificador |

---

## Proceso de Calibración

### Dataset de Entrenamiento

- **Total de ejemplos:** 1,068 pares (encabezado, contenido)
- **Coherentes (etiqueta=1):** 547 ejemplos (51.2%)
- **No coherentes (etiqueta=0):** 521 ejemplos (48.8%)
- **Fuente:** Sitios web gubernamentales bolivianos reales
  - Instituciones: ADSIB, AGETIC, SIN, SEGIP, SERECI, FUNDEMPRESA, Ministerios

### Tipos de Ejemplos

**Coherentes (θ ≥ 0.80):**
- Encabezado: "Servicios de Salud" → Contenido: descripción de atención médica
- Encabezado: "Trámite de Licencia" → Contenido: requisitos y proceso del trámite
- Encabezado: "Bono Juancito Pinto" → Contenido: detalles del beneficio social

**No Coherentes (θ < 0.80):**
- Encabezados genéricos: "Ver más", "Clic aquí", "Descargar", "Información"
- Encabezados muy cortos: "Doc", "PDF", "Link"
- Contenido no relacionado con el encabezado

### Análisis de Umbrales Evaluados

| Umbral | Precisión | Recall | F1-Score | Observación |
|--------|-----------|--------|----------|-------------|
| 0.50 | 51.22% | 100.00% | 67.74% | Sobreclasifica (muchos falsos positivos) |
| 0.65 | 53.84% | 100.00% | 69.99% | Sobreclasifica |
| 0.70 | 60.60% | 99.82% | 75.41% | Sobreclasifica |
| 0.75 | 70.55% | 98.54% | 82.23% | Sobreclasifica |
| **0.80** | **85.39%** | **83.36%** | **84.37%** | **✓ ÓPTIMO** |
| 0.85 | 98.61% | 25.96% | 41.10% | Subclasifica (muchos falsos negativos) |
| 0.90 | 100.00% | 0.37% | 0.73% | Subclasifica |

**Conclusión:** θ = 0.80 ofrece el mejor balance entre precisión y recall.

---

## Distribución de Similitudes

### Estadísticas Generales

- **Promedio:** 0.7821
- **Mínima:** 0.5298
- **Máxima:** 0.9059
- **Desviación estándar:** 0.0689
- **Mediana:** 0.8001

### Por Clase

**Coherentes (etiqueta=1):**
- Promedio: 0.8296 ± 0.0313
- Rango: [0.6784, 0.9059]

**No Coherentes (etiqueta=0):**
- Promedio: 0.7323 ± 0.0621
- Rango: [0.5298, 0.8701]

**Interpretación:** Existe separación clara entre clases. El umbral 0.80 se sitúa entre ambas distribuciones.

---

## Uso en el Sistema

### Carga Automática del Umbral

El sistema carga automáticamente el umbral calibrado desde `umbral_optimo.json`:

```python
from app.nlp.coherence import CoherenceAnalyzer

# Carga automática del umbral calibrado (0.80)
analyzer = CoherenceAnalyzer()

# Analizar sección
result = analyzer.analyze_section(
    heading="Servicios de Salud",
    content="El Ministerio de Salud ofrece atención médica..."
)

print(result.similarity_score)  # e.g., 0.823
print(result.is_coherent)       # True (>= 0.80)
```

### Uso con Umbral Personalizado

Si necesitas experimentar con otro umbral:

```python
# Usar un umbral diferente (no recomendado)
analyzer = CoherenceAnalyzer(coherence_threshold=0.75)
```

### Archivo de Configuración

El archivo `umbral_optimo.json` contiene:

```json
{
    "umbral_optimo": 0.80,
    "precision": 0.8539,
    "recall": 0.8336,
    "f1_score": 0.8437,
    "accuracy": 0.8418,
    "total_ejemplos": 1068,
    "coherentes": 547,
    "no_coherentes": 521
}
```

---

## Interpretación de Resultados

### Score de Similitud (0-1)

- **≥ 0.80:** Coherente - El contenido desarrolla el tema del encabezado
- **0.70 - 0.79:** Parcialmente coherente - Relación débil
- **< 0.70:** No coherente - Contenido no relacionado o encabezado genérico

### Casos de Uso Típicos

1. **Alta Coherencia (0.85-0.95):**
   - Encabezado: "Registro de Empresas"
   - Contenido: Descripción detallada del proceso en FUNDEMPRESA
   - → Clasificación: COHERENTE ✓

2. **Coherencia Límite (0.78-0.82):**
   - Encabezado: "Trámites y Servicios"
   - Contenido: Lista genérica de documentos
   - → Zona gris, depende del contexto

3. **Baja Coherencia (< 0.70):**
   - Encabezado: "Ver más"
   - Contenido: Cualquier texto
   - → Clasificación: NO COHERENTE ✗

---

## Validación y Actualización

### Recalibración Futura

Si se requiere recalibrar el umbral con nuevos datos:

1. Ejecutar `calibracion_umbral.py` con nuevo dataset
2. Copiar `umbral_optimo.json` a `backend/app/nlp/`
3. Reiniciar el sistema

### Requerimientos para Recalibración

- Mínimo 1,000 ejemplos balanceados (50% coherentes, 50% no coherentes)
- Ejemplos de sitios gubernamentales bolivianos reales
- Anotación manual de coherencia por expertos

---

## Referencias

- **Modelo BETO:** Cañete, J., et al. (2020). Spanish Pre-Trained BERT Model. PML4DC at ICLR 2020.
- **Sentence-BERT:** Reimers & Gurevych (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.
- **WCAG 2.4.6:** Headings and Labels (Level AA)

---

## Archivos Relacionados

- `calibracion_umbral.py` - Script de calibración
- `umbral_optimo.json` - Configuración del umbral
- `mis_ejemplos_calibracion_ampliado.csv` - Dataset de calibración (1,068 ejemplos)
- `coherence.py` - Implementación del analizador
- `models.py` - Gestor del modelo BETO

---

**Fecha de calibración:** 2026-02-23
**Versión:** 1.0
**Modelo:** `dccuchile/bert-base-spanish-wwm-cased`
