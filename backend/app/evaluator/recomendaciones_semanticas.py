"""
Generador de recomendaciones educativas para problemas semanticos HTML5.

Proporciona:
- Explicacion del problema
- Codigo de ejemplo (antes/despues)
- Referencias a estandares
- Pasos especificos de correccion

Autor: GOB.BO Evaluator
"""
from typing import Dict, List, Optional


class RecomendacionesSemanticas:
    """Genera recomendaciones detalladas con ejemplos de codigo."""

    @staticmethod
    def divitis_severa(div_ratio: float, total_divs: int, total_semantic: int) -> Dict:
        """
        Recomendacion para divitis severa.

        Args:
            div_ratio: Ratio de divs vs total elementos
            total_divs: Total de divs encontrados
            total_semantic: Total de elementos semanticos

        Returns:
            Dict con problema, explicacion, pasos y ejemplos
        """
        porcentaje = int(div_ratio * 100)

        return {
            'problema': f'Divitis severa: {porcentaje}% de elementos son <div> ({total_divs} divs vs {total_semantic} semanticos)',

            'por_que_mal': (
                'El exceso de <div> anidados (divitis) causa:\n'
                '1. Codigo dificil de mantener y debugear\n'
                '2. Menor accesibilidad (lectores de pantalla se pierden)\n'
                '3. Peor SEO (buscadores no entienden la estructura)\n'
                '4. Rendimiento degradado (DOM complejo)\n'
                '5. Incumplimiento del D.S. 3925 sobre accesibilidad'
            ),

            'como_corregir': [
                '1. Identificar divs que solo sirven para layout:',
                '   - Usar CSS Grid/Flexbox en el padre en lugar de divs wrapper',
                '',
                '2. Reemplazar divs con significado semantico:',
                '   - Contenido principal unico    -> <main>',
                '   - Agrupaciones tematicas       -> <section>',
                '   - Contenido autonomo/noticias  -> <article>',
                '   - Contenido relacionado/sidebar-> <aside>',
                '   - Navegacion                   -> <nav>',
                '   - Imagenes con descripcion     -> <figure>/<figcaption>',
                '',
                '3. Eliminar divs wrapper innecesarios',
                '4. Mantener maximo 3-4 niveles de anidamiento'
            ],

            'ejemplo_antes': '''<!-- INCORRECTO: Divitis severa -->
<div class="wrapper">
  <div class="container">
    <div class="content">
      <div class="main">
        <div class="article-wrapper">
          <div class="article-container">
            <div class="article-content">
              <h2>Titulo del articulo</h2>
              <p>Contenido...</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>''',

            'ejemplo_despues': '''<!-- CORRECTO: Semantico y limpio -->
<main class="container">
  <article>
    <h2>Titulo del articulo</h2>
    <p>Contenido...</p>
  </article>
</main>

<!-- CSS para layout (sin divs extra) -->
<style>
  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }
</style>''',

            'referencias': [
                'W3C HTML5 Sectioning: https://www.w3.org/TR/html52/dom.html#sectioning-content',
                'MDN Divitis: https://developer.mozilla.org/en-US/docs/Glossary/Divitis',
                'CSS Flexbox: https://css-tricks.com/snippets/css/a-guide-to-flexbox/',
                'D.S. 3925 Bolivia: Accesibilidad en sitios gubernamentales'
            ]
        }

    @staticmethod
    def main_mal_ubicado(main_count: int, main_inside_section: bool) -> Dict:
        """Recomendacion para <main> mal ubicado o multiple."""
        if main_count > 1:
            problema = f'Multiples <main> ({main_count}) cuando debe ser UNICO'
            detalle = 'Solo debe haber UN elemento <main> visible por documento.'
        elif main_count == 0:
            problema = 'Falta elemento <main> para contenido principal'
            detalle = 'Todo sitio debe tener <main> para identificar el contenido principal.'
        else:
            problema = '<main> esta dentro de <section> (jerarquia incorrecta)'
            detalle = '<main> debe contener <section>, NO al reves.'

        return {
            'problema': problema,

            'por_que_mal': (
                f'{detalle}\n\n'
                'Segun W3C y WCAG:\n'
                '- Solo UN <main> visible por documento\n'
                '- <main> debe contener el contenido principal unico de la pagina\n'
                '- Ayuda a lectores de pantalla a saltar directamente al contenido\n'
                '- Mejora SEO al identificar claramente el contenido primario\n'
                '- Es OBLIGATORIO para cumplir WCAG 2.0 Level AA'
            ),

            'como_corregir': [
                '1. Asegurar solo UN <main> en el documento',
                '',
                '2. Colocar <main> como hijo directo de <body>:',
                '   <body>',
                '     <header>...</header>',
                '     <main>  <-- CONTENIDO PRINCIPAL',
                '       <section>...</section>',
                '       <article>...</article>',
                '     </main>',
                '     <footer>...</footer>',
                '   </body>',
                '',
                '3. NO anidar <main> dentro de:',
                '   - <article>',
                '   - <aside>',
                '   - <section>',
                '   - <header>',
                '   - <footer>',
                '',
                '4. Si hay varios bloques importantes, usar <article> para cada uno'
            ],

            'ejemplo_antes': '''<!-- INCORRECTO: main dentro de section -->
<body>
  <header>...</header>
  <section class="content">
    <main>
      <article>Contenido</article>
    </main>
  </section>
  <footer>...</footer>
</body>''',

            'ejemplo_despues': '''<!-- CORRECTO: main como contenedor principal -->
<body>
  <header>
    <h1>Institucion Gubernamental</h1>
    <nav>
      <ul>
        <li><a href="/">Inicio</a></li>
        <li><a href="/servicios">Servicios</a></li>
      </ul>
    </nav>
  </header>

  <main>
    <section>
      <h2>Servicios Ciudadanos</h2>
      <article>
        <h3>Tramite 1</h3>
        <p>Descripcion...</p>
      </article>
    </section>
  </main>

  <footer>
    <p>Contacto: info@institucion.gob.bo</p>
  </footer>
</body>''',

            'referencias': [
                'W3C <main>: https://www.w3.org/TR/html52/grouping-content.html#the-main-element',
                'MDN <main>: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/main',
                'WCAG Bypass Blocks: https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks'
            ]
        }

    @staticmethod
    def falta_estructura_base(elementos_faltantes: List[str]) -> Dict:
        """Recomendacion cuando falta estructura HTML5 basica."""
        faltantes_str = ', '.join([f'<{e}>' for e in elementos_faltantes])

        return {
            'problema': f'Estructura HTML5 incompleta. Faltan: {faltantes_str}',

            'por_que_mal': (
                'Un sitio web gubernamental DEBE tener estructura semantica:\n\n'
                '1. ACCESIBILIDAD: Usuarios con discapacidades dependen de\n'
                '   lectores de pantalla que usan estos elementos para navegar.\n\n'
                '2. SEO: Buscadores entienden mejor el contenido con estructura.\n\n'
                '3. MANTENIMIENTO: Codigo mas facil de entender y modificar.\n\n'
                '4. CUMPLIMIENTO: D.S. 3925 exige accesibilidad en sitios .gob.bo'
            ),

            'como_corregir': [
                'Implementar estructura HTML5 minima OBLIGATORIA:',
                '',
                '<body>',
                '  <header>',
                '    Logo + Titulo de la institucion',
                '    <nav> con menu principal',
                '  </header>',
                '',
                '  <main>',
                '    Contenido principal UNICO de esta pagina',
                '    <section> para agrupar por tema',
                '    <article> para contenido autonomo',
                '    <aside> para contenido relacionado',
                '  </main>',
                '',
                '  <footer>',
                '    Contacto, enlaces legales, redes sociales',
                '  </footer>',
                '</body>'
            ],

            'ejemplo_antes': '''<!-- INCORRECTO: Solo divs, sin semantica -->
<body>
  <div id="header">
    <div class="logo">Logo</div>
    <div class="menu">
      <div class="menu-item">Inicio</div>
      <div class="menu-item">Servicios</div>
    </div>
  </div>

  <div id="content">
    <div class="post">Noticia 1</div>
    <div class="post">Noticia 2</div>
    <div class="sidebar">Links</div>
  </div>

  <div id="footer">
    <div class="contact">Contacto</div>
  </div>
</body>''',

            'ejemplo_despues': '''<!-- CORRECTO: HTML5 semantico completo -->
<body>
  <header>
    <h1>
      <img src="escudo.png" alt="Escudo de Bolivia">
      Ministerio de Ejemplo
    </h1>
    <nav aria-label="Menu principal">
      <ul>
        <li><a href="/">Inicio</a></li>
        <li><a href="/servicios">Servicios</a></li>
        <li><a href="/tramites">Tramites</a></li>
        <li><a href="/contacto">Contacto</a></li>
      </ul>
    </nav>
  </header>

  <main>
    <section aria-labelledby="noticias-titulo">
      <h2 id="noticias-titulo">Noticias Recientes</h2>

      <article>
        <h3>Nuevo servicio digital</h3>
        <time datetime="2025-01-26">26 de enero, 2025</time>
        <p>Descripcion de la noticia...</p>
        <a href="/noticia/1">Leer mas</a>
      </article>

      <article>
        <h3>Horario de atencion</h3>
        <time datetime="2025-01-25">25 de enero, 2025</time>
        <p>Informacion sobre horarios...</p>
      </article>
    </section>

    <aside aria-label="Enlaces relacionados">
      <h2>Enlaces de Interes</h2>
      <ul>
        <li><a href="https://www.gob.bo">Portal gob.bo</a></li>
        <li><a href="/transparencia">Transparencia</a></li>
      </ul>
    </aside>
  </main>

  <footer>
    <section aria-label="Informacion de contacto">
      <h2>Contacto</h2>
      <address>
        <p>Email: <a href="mailto:info@ministerio.gob.bo">info@ministerio.gob.bo</a></p>
        <p>Telefono: <a href="tel:+59122345678">+591 2 234 5678</a></p>
        <p>Direccion: Av. Ejemplo 123, La Paz, Bolivia</p>
      </address>
    </section>

    <nav aria-label="Redes sociales">
      <a href="https://facebook.com/ministerio">Facebook</a>
      <a href="https://twitter.com/ministerio">Twitter</a>
    </nav>

    <p>&copy; 2025 Ministerio de Ejemplo - Estado Plurinacional de Bolivia</p>
  </footer>
</body>''',

            'referencias': [
                'HTML5 Semantico: https://www.w3schools.com/html/html5_semantic_elements.asp',
                'MDN Document Structure: https://developer.mozilla.org/en-US/docs/Learn/HTML/Introduction_to_HTML/Document_and_website_structure',
                'WCAG 2.0: https://www.w3.org/WAI/WCAG21/quickref/',
                'D.S. 3925: Lineamiento de Sitios Web Gubernamentales Bolivia'
            ]
        }

    @staticmethod
    def nav_mal_ubicado(navs_floating: int, nav_count: int) -> Dict:
        """Recomendacion para <nav> fuera de header/footer."""
        return {
            'problema': f'{navs_floating} de {nav_count} elementos <nav> estan fuera de <header>/<footer>',

            'por_que_mal': (
                'La navegacion principal debe estar dentro de <header> porque:\n\n'
                '1. ACCESIBILIDAD: Lectores de pantalla esperan encontrar\n'
                '   la navegacion dentro del header del documento.\n\n'
                '2. CONSISTENCIA: Usuarios esperan el menu en la parte superior.\n\n'
                '3. SEMANTICA: <header> agrupa contenido introductorio Y navegacion.\n\n'
                '4. SKIP LINKS: Permite saltar al contenido principal facilmente.'
            ),

            'como_corregir': [
                '1. Navegacion PRINCIPAL -> dentro de <header>',
                '2. Navegacion SECUNDARIA (footer links) -> dentro de <footer>',
                '3. Navegacion de SECCION -> dentro del <article>/<section> correspondiente',
                '',
                'Estructura recomendada:',
                '<header>',
                '  <h1>Titulo</h1>',
                '  <nav aria-label="Menu principal">  <-- AQUI',
                '    <ul>...</ul>',
                '  </nav>',
                '</header>'
            ],

            'ejemplo_antes': '''<!-- INCORRECTO: nav flotante -->
<header>
  <h1>Institucion</h1>
</header>

<nav>  <!-- Fuera de header! -->
  <ul>
    <li>Inicio</li>
    <li>Servicios</li>
  </ul>
</nav>

<main>...</main>''',

            'ejemplo_despues': '''<!-- CORRECTO: nav dentro de header -->
<header>
  <h1>Institucion</h1>

  <nav aria-label="Menu principal">
    <ul>
      <li><a href="/">Inicio</a></li>
      <li><a href="/servicios">Servicios</a></li>
      <li><a href="/contacto">Contacto</a></li>
    </ul>
  </nav>
</header>

<main>...</main>

<footer>
  <nav aria-label="Enlaces del pie de pagina">
    <ul>
      <li><a href="/privacidad">Politica de Privacidad</a></li>
      <li><a href="/terminos">Terminos de Uso</a></li>
    </ul>
  </nav>
</footer>''',

            'referencias': [
                'W3C <nav>: https://www.w3.org/TR/html52/sections.html#the-nav-element',
                'MDN <nav>: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/nav',
                'WAI Navigation: https://www.w3.org/WAI/tutorials/menus/'
            ]
        }

    @staticmethod
    def headings_incorrectos(h1_count: int, hierarchy_valid: bool, errors: List) -> Dict:
        """Recomendacion para jerarquia de headings incorrecta."""
        if h1_count == 0:
            problema = 'Falta <h1> - toda pagina debe tener exactamente uno'
        elif h1_count > 1:
            problema = f'Multiples <h1> ({h1_count}) - debe ser UNICO por pagina'
        else:
            problema = 'Saltos en jerarquia de headings (ej: h1 -> h3 sin h2)'

        return {
            'problema': problema,

            'por_que_mal': (
                'Los headings (h1-h6) crean la estructura de navegacion del documento:\n\n'
                '1. ACCESIBILIDAD: Usuarios de lectores de pantalla navegan\n'
                '   por headings. Saltos confunden la estructura.\n\n'
                '2. SEO: Buscadores usan h1 para entender el tema principal.\n\n'
                '3. WCAG 1.3.1: Exige estructura logica de headings.\n\n'
                'Reglas:\n'
                '- UN solo <h1> por pagina (titulo principal)\n'
                '- No saltar niveles (h1 -> h2 -> h3, no h1 -> h3)\n'
                '- Usar headings para estructura, no para estilo'
            ),

            'como_corregir': [
                '1. Exactamente UN <h1> que describa el contenido de la pagina',
                '',
                '2. Seguir jerarquia sin saltos:',
                '   h1 -> Titulo principal de la pagina',
                '     h2 -> Secciones principales',
                '       h3 -> Subsecciones',
                '         h4 -> Detalles',
                '',
                '3. NO usar headings solo para estilo visual:',
                '   - Incorrecto: <h3> porque se ve del tamano que quiero',
                '   - Correcto: <h2 class="small"> con CSS para el tamano',
                '',
                '4. Cada <section>/<article> puede reiniciar en h2'
            ],

            'ejemplo_antes': '''<!-- INCORRECTO: Multiples h1 y saltos -->
<body>
  <h1>Logo de la Institucion</h1>  <!-- h1 para logo? -->

  <h1>Bienvenido al Portal</h1>   <!-- Otro h1! -->

  <h4>Noticias</h4>               <!-- Salto h1 -> h4 -->

  <h2>Servicios</h2>
    <h5>Tramite 1</h5>            <!-- Salto h2 -> h5 -->
</body>''',

            'ejemplo_despues': '''<!-- CORRECTO: Un h1, jerarquia logica -->
<body>
  <header>
    <h1>Portal del Ministerio de Ejemplo</h1>  <!-- UNICO h1 -->
    <nav>...</nav>
  </header>

  <main>
    <section>
      <h2>Noticias Recientes</h2>        <!-- h2 para seccion -->
      <article>
        <h3>Nueva normativa publicada</h3> <!-- h3 para articulo -->
        <p>Contenido...</p>
      </article>
    </section>

    <section>
      <h2>Servicios al Ciudadano</h2>    <!-- h2 para seccion -->
      <article>
        <h3>Tramite de Certificado</h3>   <!-- h3 para articulo -->
        <h4>Requisitos</h4>               <!-- h4 para subseccion -->
        <ul>...</ul>
        <h4>Pasos a seguir</h4>           <!-- h4 para subseccion -->
        <ol>...</ol>
      </article>
    </section>
  </main>
</body>''',

            'referencias': [
                'WCAG H42: https://www.w3.org/WAI/WCAG21/Techniques/html/H42',
                'MDN Headings: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/Heading_Elements',
                'WebAIM Headings: https://webaim.org/techniques/semanticstructure/#headings'
            ]
        }

    @staticmethod
    def falta_meta_seo(tipo: str) -> Dict:
        """Recomendacion para meta tags SEO faltantes."""
        if tipo == 'description':
            return {
                'problema': 'Falta meta description para SEO',

                'por_que_mal': (
                    'La meta description es CRUCIAL para SEO:\n\n'
                    '1. Aparece en resultados de busqueda bajo el titulo\n'
                    '2. Influye en el click-through rate (CTR)\n'
                    '3. Ayuda a buscadores a entender el contenido\n'
                    '4. Es obligatoria para sitios gubernamentales visibles'
                ),

                'como_corregir': [
                    'Agregar en el <head>:',
                    '',
                    '<meta name="description" content="Descripcion clara de 150-160 caracteres">',
                    '',
                    'Caracteristicas de buena description:',
                    '- 150-160 caracteres (Google trunca mas)',
                    '- Describir el contenido ESPECIFICO de esta pagina',
                    '- Incluir palabras clave relevantes',
                    '- Llamado a la accion si aplica'
                ],

                'ejemplo_antes': '''<!-- INCORRECTO: Sin meta description -->
<head>
  <title>Ministerio de Ejemplo</title>
  <!-- Falta description! -->
</head>''',

                'ejemplo_despues': '''<!-- CORRECTO: Con meta description -->
<head>
  <meta charset="UTF-8">
  <title>Ministerio de Ejemplo - Gobierno de Bolivia</title>
  <meta name="description" content="Portal oficial del Ministerio de Ejemplo. Acceda a tramites en linea, noticias institucionales y servicios para la ciudadania boliviana.">
  <meta name="keywords" content="ministerio, bolivia, tramites, gobierno, servicios">
</head>''',

                'referencias': [
                    'Google SEO: https://developers.google.com/search/docs/appearance/snippet',
                    'Moz Meta Description: https://moz.com/learn/seo/meta-description'
                ]
            }
        else:  # keywords
            return {
                'problema': 'Falta meta keywords (opcional pero recomendado)',

                'por_que_mal': (
                    'Aunque meta keywords tiene menos peso en SEO moderno:\n\n'
                    '1. Algunos buscadores locales aun lo consideran\n'
                    '2. Ayuda a categorizar el contenido internamente\n'
                    '3. Es parte de las buenas practicas de metadatos\n'
                    '4. Sitios gubernamentales deben ser ejemplares'
                ),

                'como_corregir': [
                    'Agregar en el <head>:',
                    '',
                    '<meta name="keywords" content="palabra1, palabra2, palabra3">',
                    '',
                    'Recomendaciones:',
                    '- 5-10 palabras clave relevantes',
                    '- Separadas por comas',
                    '- Especificas a esta pagina',
                    '- No repetir excesivamente'
                ],

                'ejemplo_antes': '''<head>
  <title>Tramites en Linea</title>
  <meta name="description" content="...">
  <!-- Falta keywords -->
</head>''',

                'ejemplo_despues': '''<head>
  <title>Tramites en Linea - Ministerio de Ejemplo</title>
  <meta name="description" content="Realice sus tramites gubernamentales en linea...">
  <meta name="keywords" content="tramites, certificados, gobierno, bolivia, ministerio, en linea, digital">
</head>''',

                'referencias': [
                    'MDN meta keywords: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meta/name'
                ]
            }

    @staticmethod
    def formatear_recomendacion(rec: Dict) -> str:
        """
        Formatea una recomendacion en texto legible para consola/logs.

        Args:
            rec: Dict con problema, por_que_mal, como_corregir, ejemplos

        Returns:
            String formateado con toda la informacion
        """
        ancho = 78
        output = []

        # Titulo
        output.append("=" * ancho)
        output.append(f"PROBLEMA: {rec['problema']}")
        output.append("=" * ancho)

        # Por que esta mal
        output.append("\nPOR QUE ESTA MAL:")
        output.append("-" * 40)
        for line in rec['por_que_mal'].split('\n'):
            output.append(f"  {line}")

        # Como corregir
        output.append("\nCOMO CORREGIR:")
        output.append("-" * 40)
        for step in rec['como_corregir']:
            output.append(f"  {step}")

        # Ejemplos
        if 'ejemplo_antes' in rec:
            output.append("\nEJEMPLO - CODIGO INCORRECTO:")
            output.append("-" * 40)
            for line in rec['ejemplo_antes'].split('\n'):
                output.append(f"  {line}")

            output.append("\nEJEMPLO - CODIGO CORRECTO:")
            output.append("-" * 40)
            for line in rec['ejemplo_despues'].split('\n'):
                output.append(f"  {line}")

        # Referencias
        output.append("\nREFERENCIAS:")
        output.append("-" * 40)
        for ref in rec['referencias']:
            output.append(f"  * {ref}")

        output.append("=" * ancho)

        return '\n'.join(output)

    @staticmethod
    def generar_resumen_recomendaciones(recomendaciones: List[Dict]) -> str:
        """
        Genera un resumen ejecutivo de todas las recomendaciones.

        Args:
            recomendaciones: Lista de dicts de recomendaciones

        Returns:
            String con resumen
        """
        if not recomendaciones:
            return "No hay recomendaciones - estructura semantica correcta."

        output = []
        output.append("=" * 60)
        output.append("RESUMEN DE PROBLEMAS DETECTADOS")
        output.append("=" * 60)

        for i, rec in enumerate(recomendaciones, 1):
            output.append(f"\n{i}. {rec['problema']}")
            # Primer paso de como corregir
            if rec['como_corregir']:
                primer_paso = rec['como_corregir'][0]
                if primer_paso:
                    output.append(f"   -> {primer_paso}")

        output.append("\n" + "=" * 60)
        output.append(f"Total: {len(recomendaciones)} problemas a corregir")
        output.append("=" * 60)

        return '\n'.join(output)
