# GUIA PARA INSPECCION MANUAL (Ground Truth)

Esta guia explica como realizar inspecciones manuales de sitios web para crear
datos de ground truth que permitan medir la cobertura del crawler.

## Objetivo

El ground truth representa el "valor real" de elementos en una pagina web,
obtenido mediante inspeccion manual. Comparando la extraccion del crawler
contra estos valores, podemos medir su efectividad.

## Procedimiento de Inspeccion

### 1. Preparacion

1. Abrir el sitio en Chrome o Firefox
2. Abrir DevTools (F12)
3. Hacer scroll completo hasta el final de la pagina
4. Esperar a que cargue todo el contenido dinamico (3-5 segundos)

### 2. Ejecutar Comandos de Conteo

En la Consola de DevTools, ejecutar los siguientes comandos:

```javascript
// ============================================
// CONTEO DE ELEMENTOS PARA GROUND TRUTH
// ============================================

// 1. Contar links visibles
console.log("Links:", document.querySelectorAll('a[href]').length);

// 2. Contar imagenes
console.log("Imagenes:", document.querySelectorAll('img').length);

// 3. Contar formularios
console.log("Formularios:", document.querySelectorAll('form').length);

// 4. Contar secciones (headings h1-h6)
console.log("Secciones:", document.querySelectorAll('h1, h2, h3, h4, h5, h6').length);

// 5. Contar botones
console.log("Botones:", document.querySelectorAll('button, input[type="submit"], input[type="button"]').length);

// 6. Contar labels de formulario
console.log("Labels:", document.querySelectorAll('label').length);

// 7. Contar palabras visibles
console.log("Palabras:", document.body.innerText.split(/\s+/).filter(w => w.length > 0).length);

// ============================================
// SCRIPT COMPLETO (copiar todo junto)
// ============================================
(function() {
    const results = {
        links: document.querySelectorAll('a[href]').length,
        images: document.querySelectorAll('img').length,
        forms: document.querySelectorAll('form').length,
        sections: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
        buttons: document.querySelectorAll('button, input[type="submit"], input[type="button"]').length,
        labels: document.querySelectorAll('label').length,
        text_words: document.body.innerText.split(/\s+/).filter(w => w.length > 0).length
    };

    console.log("=== GROUND TRUTH ===");
    console.log(JSON.stringify(results, null, 2));

    // Copiar al portapapeles
    navigator.clipboard.writeText(JSON.stringify(results, null, 2))
        .then(() => console.log("Copiado al portapapeles!"))
        .catch(() => console.log("No se pudo copiar automaticamente"));

    return results;
})();
```

### 3. Registrar en ground_truth_sites.json

Agregar el nuevo sitio al archivo `tests/ground_truth_sites.json`:

```json
{
  "url": "https://www.ejemplo.gob.bo",
  "architecture": "MPA",
  "manual_inspection": {
    "links": 127,
    "images": 45,
    "forms": 2,
    "sections": 18,
    "buttons": 8,
    "text_words": 3450,
    "labels": 4
  },
  "inspection_date": "2025-01-25",
  "notes": "Conteo manual tras scroll completo"
}
```

## Criterios de Conteo

### Links
- Contar TODOS los `<a>` con atributo `href`
- Incluir links en header, footer, navegacion y contenido
- Incluir links ocultos pero presentes en DOM

### Imagenes
- Contar TODAS las etiquetas `<img>`
- Incluir iconos, logos, imagenes decorativas
- No contar imagenes de fondo CSS

### Formularios
- Contar etiquetas `<form>`
- Incluir formularios de busqueda, login, contacto

### Secciones (Headings)
- Contar h1, h2, h3, h4, h5, h6
- Cada heading cuenta como una seccion

### Botones
- Contar `<button>`
- Contar `<input type="submit">`
- Contar `<input type="button">`
- NO contar links estilizados como botones

### Labels
- Contar `<label>` de formularios
- Incluir labels asociados y no asociados

### Palabras
- Contar palabras visibles en la pagina
- Usar `document.body.innerText` para obtener texto visible
- Dividir por espacios y filtrar vacios

## Arquitectura del Sitio

Clasificar el sitio como:

- **MPA** (Multi-Page Application): Sitio tradicional con navegacion por paginas
- **SPA** (Single-Page Application): Sitio que carga contenido dinamicamente sin recargar

### Como identificar:

**MPA:**
- La URL cambia completamente al navegar
- La pagina se recarga completamente
- Tecnologias: PHP, WordPress, Joomla, Django templates

**SPA:**
- La URL puede cambiar pero sin recarga
- Solo cambia parte del contenido
- Tecnologias: React, Angular, Vue.js

## Notas Importantes

1. **Consistencia**: Siempre hacer scroll completo antes de contar
2. **Contenido dinamico**: Esperar a que cargue todo (lazy loading)
3. **Viewport**: Usar resolucion estandar (1920x1080)
4. **Fecha**: Registrar fecha de inspeccion (los sitios cambian)
5. **Notas**: Documentar particularidades del sitio

## Ejemplo de Sesion

```
1. Abrir https://www.aduana.gob.bo
2. F12 -> Consola
3. Scroll hasta el final
4. Esperar 3 segundos
5. Ejecutar script de conteo
6. Copiar resultados
7. Agregar a ground_truth_sites.json
8. Ejecutar: python tests/test_coverage_analysis.py
```

## Interpretacion de Resultados

| Cobertura | Interpretacion |
|-----------|----------------|
| >= 95%    | Excelente - El crawler extrae casi todo |
| 90-95%    | Bueno - Pocas perdidas |
| 80-90%    | Aceptable - Revisar categorias bajas |
| < 80%     | Mejorar - Hay problemas de extraccion |

### Comparacion con Googlebot

- MPAs: Googlebot promedio 97%
- SPAs: Googlebot promedio 85%

Si tu crawler supera estos valores, esta funcionando muy bien.
