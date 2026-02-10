# Documentación Técnica del Crawler

## Descripción General

El módulo **Crawler** es el componente core encargado de navegar por los sitios web gubernamentales (.gob.bo), renderizar su contenido dinámico y aplicar heurísticas de extracción para alimentar el sistema de evaluación.

## Arquitectura y Flujo de Trabajo

El siguiente diagrama explica paso a paso qué hace el crawler, desde que recibe una URL hasta que guarda los resultados.

```mermaid
graph TD
    subgraph "1. Entradas (Inputs)"
    A[URL del Sitio Web .gob.bo] --> B{¿Es válida?}
    B -- No --> C[Error: Sitio no gubernamental]
    B -- Si --> D{¿Robots.txt permite entrar?}
    D -- No (Disallow) --> E[Error: Acceso bloqueado]
    D -- Si (Allow) --> F[Pasar a Fase de Extracción]
    end

    subgraph "2. Fase de Extracción (Proceso)"
    F --> G[Navegador Automático (Playwright)]
    G --> G1[Carga página con HTML + Javascript]
    G1 --> G2[Aplica 'Auto-Scroll' para cargar imágenes]
    G2 --> H[Obtiene el HTML Final Completo]
    H --> I[Parsing: Lee el código con BeautifulSoup]
    
    I --> J{Aplicación de Heurísticas}
    J --> J1[Heurística: Busca Menús y Títulos]
    J --> J2[Heurística: Detecta Redes Sociales]
    J --> J3[Heurística: Analiza Imágenes y Alt]
    J --> J4[Heurística: Busca Trackers Externos]
    end

    subgraph "3. Salidas (Outputs)"
    J1 & J2 & J3 & J4 --> K[Salida 1: Datos Estructurales (JSON)]
    J --> L[Salida 2: Corpus de Texto (NLP)]
    
    K --> M[(Base de Datos)]
    L --> M
    end
```

### Explicación Explícita del Flujo

El crawler no hace "magia", sigue un proceso lógico estricto:

**Paso 1: Las Entradas (Inputs)**
*   **La URL**: Todo empieza con la dirección web (ej: `minedu.gob.bo`).
*   **Verificaciones**: Antes de entrar, el sistema verifica dos cosas:
    1.  ¿Es realmente un sitio `.gob.bo`? (Seguridad).
    2.  ¿El archivo `robots.txt` nos da permiso? (Ética y Estándares). Si el sitio dice "no pasar", respetamos esa regla.

**Paso 2: El Proceso de Extracción (Core)**
Aquí es donde ocurre la automatización.
*   **Navegación Real**: No solo descargamos archivo, usamos un navegador real (Playwright) para "ver" la página igual que un usuario humano. Esto es vital para sitios modernos (SPA) que usan mucho JavaScript.
*   **Auto-Scroll**: El crawler baja automáticamente por la página. ¿Por qué? Para activar el *Lazy Loading* (imágenes que solo cargan cuando las ves). Si no hiciéramos esto, capturaríamos la mitad de la información.
*   **Aplicación de Heurísticas**: Una vez obtenido el código, aplicamos reglas inteligentes (patrones) para entender qué es cada cosa: *"Si tiene un @ es un correo"*, *"Si está arriba y tiene enlaces, es un menú"*.

**Paso 3: Las Salidas (Outputs)**
El crawler genera dos tipos de resultados finales:
1.  **Datos Estructurales**: Un archivo JSON con toda la evaluación técnica (¿Tiene H1? ¿Las imágenes tienen texto alternativo? ¿Usa HTTPS?).
2.  **Corpus de Texto**: Extrae todo el texto visible (párrafos, noticias) limpio de código, listo para que el módulo de Inteligencia Artificial (NLP) analice si el lenguaje es claro y sencillo.

### Sobre el Tiempo y Eficiencia
El uso de este crawler introduce una **mejora de eficiencia** crítica:
*   **Manual**: Una evaluación humana detallada de los 31 criterios podía tomar **3 a 5 días**.
*   **Automática**: Este crawler realiza la extracción completa en **20 a 30 segundos** por sitio, permitiendo evaluaciones masivas en tiempo real.

---

## Implementación en Código (Evidencia)

Para demostrar cómo se aplican las reglas en el código, revisa el archivo `backend/app/crawler/html_crawler.py`. Aquí están los ejemplos clave que debes mostrar:

### 1. Heurística de Enlaces (Redes Sociales y Contacto)
**Dónde**: Método `_extract_links` (Línea ~670)
**La Lógica**: No solo extrae `<a>`, compara el dominio contra una "Lista Blanca" de redes sociales conocidas.

```python
# Definición de patrones (Heurística de Conocimiento)
SOCIAL_DOMAINS = ['facebook.com', 'twitter.com', 'instagram.com', 'youtube.com']

# Aplicación en el código
elif any(domain in parsed.netloc for domain in self.SOCIAL_DOMAINS):
    social_links.append(link_data)  # ¡Es una red social!
elif href.startswith('mailto:'):
    email_links.append(link_data)   # ¡Es un correo!
elif href.startswith('tel:'):
    phone_links.append(link_data)   # ¡Es un teléfono!
```

### 2. Heurística de Imágenes (Accesibilidad)
**Dónde**: Método `_extract_images` (Línea ~608)
**La Lógica**: Analiza cada imagen para ver si cumple la regla de tener texto opcional (`alt`).

```python
# Lógica de Validación (Heurística de Regla)
images_list.append({
    'src': src,
    'alt': alt,
    'has_alt': 'alt' in img.attrs,      # ¿Existe el atributo?
    'alt_empty': alt == '',             # ¿Está vacío?
    # ...
})
```

### 3. Heurística de Jerarquía (Estructura)
**Dónde**: Método `_extract_headings` (Línea ~545)
**La Lógica**: Recorre todos los H1-H6 y verifica si el orden lógico se rompe (ej: saltar de H1 a H3).

```python
# Lógica de Secuencia
for i, level in enumerate(levels_used):
    if level > previous_level + 1:
        hierarchy_valid = False  # ¡Error! Salto de jerarquía detectado
```

---

## Diferenciación Técnica: ¿Por qué no usar un Crawler genérico?

Esta es la diferencia clave entre un "Crawler Normal" (como Googlebot o un script básico de Scrapy) y este **Crawler Evaluador**:

| Característica | Crawler Genérico (Normal) | Nuestro Crawler (Heurístico) |
| :--- | :--- | :--- |
| **Objetivo** | Indexar contenido (encontrar palabras clave para buscadores). | **Evaluar calidad** y cumplimiento de normas. |
| **Manejo de HTML** | Extrae todo el texto plano indiscriminadamente. | Extrae **Estructura Semántica** (sabe qué es un Menú vs. un Artículo). |
| **Enlaces** | Solo los sigue (para encontrar más páginas). | Los **Clasifica** (Redes Sociales, Contacto, Navegación) usando patrones. |
| **Validación** | No le importa si el HTML está "roto" o mal hecho. | **Detecta errores** de jerarquía (H1->H3), falta de ALT, y etiquetas obsoletas. |
| **Salida** | Un índice de texto plano o una lista de URLs. | Un **Reporte JSON Estructurado** con métricas de accesibilidad y usabilidad. |

**En resumen:**
Un crawler normal dice: *"Aquí hay una imagen de un gato"*.
Nuestro crawler dice: *"Aquí hay una imagen (<img>), tiene dimensiones correctas (width/height), pero **falla la normativa** porque no tiene descripción alternativa (alt='gato')"*.

Esta capacidad de **"Entender para Evaluar"** es lo que lo convierte en un sistema experto y no solo una herramienta de descarga.

---

## Diferencia vs. Evaluadores SEO (Lighthouse, Screaming Frog)

Es común que te pregunten: *"¿Por qué no usar simplemente Google Lighthouse o Ahrefs?"*. Aquí está tu defensa:

| Característica | Herramientas SEO (Lighthouse/Paseo) | Tu Evaluador (GobBo) |
| :--- | :--- | :--- |
| **Soberanía Digital** | **Sancionan** si no usas CDNs (ej. Cloudflare) para velocidad. | **Sancionan** si usas CDNs extranjeras (violación de D.S. 3925 / Hosting Local). |
| **Privacidad** | Ignoran trackers (Google Analytics es "bueno"). | **Detecta y alerta** sobre trackers externos como violación de soberanía. |
| **Contexto Local** | Reglas genéricas internacionales. | Reglas específicas **Bolivianas** (ej. buscar "Bolivia a tu servicio", botones de WhatsApp). |
| **Análisis de Texto** | Fórmulas matemáticas básicas (Flesch-Kincaid). | **Inteligencia Artificial (NLP)** entrenada para detectar lenguaje claro en español. |
| **Persistencia** | Auditoría de un solo momento ("Snapshot"). | **Histórico Evolutivo**: Guarda el progreso en BD para ver si la institución mejora con el tiempo. |

**El "Valor Único" (USP):**
Mientras un evaluador SEO te optimiza para **Google** (Mercado), tu sistema optimiza para el **Ciudadano y la Ley** (Estado). Son objetivos opuestos:
*   SEO: "Quiero vender más / tener más tráfico".
*   GobBo: "Quiero que todos accedan / cumplir la ley".





---

## Heurísticas y Reglas de Extracción

El crawler aplica un conjunto de reglas lógicas y coincidencia de patrones para estructurar la información no estructurada de la web.

### 1. Heurísticas de Clasificación de Enlaces
Se analizan todos los elementos `<a>` y se clasifican según su destino (`href`) usando listas de control y patrones.

| Categoría | Método de Detección | Listas/Patrones Usados |
|-----------|---------------------|------------------------|
| **Redes Sociales** | Coincidencia de dominio | `facebook.com`, `twitter.com`, `instagram.com`, `youtube.com`, `tiktok.com`, `linkedin.com` |
| **Mensajería** | Coincidencia de dominio | `wa.me`, `api.whatsapp.com`, `t.me` |
| **Correo Electrónico** | Protocolo | `mailto:` |
| **Teléfono** | Protocolo | `tel:` |
| **Enlaces Genéricos** | Texto del enlace | "click aquí", "ver más", "leer más", "siguiente" |
| **Enlaces Vacíos** | Lógica | `text_length == 0` AND `title_length == 0` |

### 2. Heurísticas de Recursos Externos (Soberanía Digital)
Detecta dependencias de terceros que podrían violar la soberanía de datos.

| Recurso | Método | Patrones |
|---------|--------|----------|
| **Trackers** | Búsqueda en `src` de scripts | `google-analytics`, `facebook-pixel`, `doubleclick`, `googletagmanager` |
| **Fuentes Externas** | Búsqueda en `<link>` y CSS | `fonts.googleapis.com`, `use.typekit.net` |
| **CDNs** | Búsqueda parcial en dominios | Detecta dominios que no son `.gob.bo` para recursos estáticos |

### 3. Heurísticas de Estructura y Semántica (HTML5)
Analiza la calidad del código y el uso de estándares modernos.

-   **DOCTYPE**: Verifica si el primer nodo es `<!DOCTYPE html>` (HTML5).
-   **Elementos Obsoletos**: Busca tags depreciados como `<font>`, `<center>`, `<marquee>`, `<blink>`.
-   **Atributos de Presentación**: Detecta atributos visuales en HTML (`align`, `bgcolor`, `border`) que deberían estar en CSS.
-   **Estructura Semántica**: Contabiliza la presencia de `<header>`, `<nav>`, `<main>`, `<footer>` para determinar si el sitio tiene una arquitectura semántica correcta.

### 4. Heurísticas de Accesibilidad
-   **Imágenes**:
    -   Calcula el porcentaje de cumplimiento de texto alternativo (`alt`).
    -   Regla: `tiene_alt = existe atributo alt AND largo(alt) > 0`.
-   **Jerarquía de Encabezados**:
    -   Extrae la secuencia de `H1` a `H6`.
    -   Valida lógica: No deben haber saltos (ej: H1 -> H3 es estructura inválida).
    -   Valida unicidad: Debe existir exactamente un `H1`.
-   **Formularios**:
    -   Verifica si los `input` tienen un `label` asociado (explícito o implícito).

### 5. Heurísticas de Metadatos
Extrae información clave para SEO y Usabilidad.
-   **Institución en Título**: Extrae el `<title>` para verificar si contiene el nombre de la institución.
-   **Responsive Design**: Verifica la presencia de `<meta name="viewport">`.

## Estructura del Código

El código principal se encuentra en `backend/app/crawler/html_crawler.py`.

### Clase `GobBoCrawler`

La clase principal que orquesta todo el proceso.

#### Inicialización
```python
crawler = GobBoCrawler(timeout=30, user_agent="...")
```

#### Método `crawl(url)`
Orquesta el flujo completo descrito en el diagrama de Workflow.

### Métodos Privados de Extracción
Cada método encapsula la lógica de una familia de heurísticas:
- `_extract_structure()`: DOCTYPE, obsoletos.
- `_extract_metadata()`: Meta tags.
- `_extract_semantic_elements()`: Tags semánticos.
- `_extract_headings()`: Jerarquía H1-H6.
- `_extract_images()`: Análisis atributos ALT.
- `_extract_links()`: Clasificación de URLs.
- `_extract_external_resources()`: Detección de trackers/CDNs.

## Configuración

El comportamiento del crawler puede ajustarse mediante variables de entorno en `.env`:

- `CRAWLER_TIMEOUT`: Tiempo de espera en segundos.
- `CRAWLER_USER_AGENT`: String de identificación del bot.
