"""
Guia de Buenas Practicas HTML5 Semantico.

Basado en:
- W3C HTML Living Standard
- MDN Web Docs
- WCAG 2.0 Best Practices

Este modulo define las reglas para evaluar si un sitio web
usa correctamente los elementos semanticos de HTML5.
"""

# Reglas por elemento semantico
BUENAS_PRACTICAS = {
    'main': {
        'debe': [
            'Ser unico en el documento (solo un <main>)',
            'Contener el contenido principal del documento',
            'No estar dentro de <article>, <aside>, <footer>, <header>, <nav>'
        ],
        'no_debe': [
            'Aparecer mas de una vez sin hidden',
            'Estar dentro de elementos seccionales',
            'Estar anidado dentro de otro <main>'
        ],
        'nivel_max': 2,  # Deberia estar cerca de body
        'peso': 3.0  # Peso en scoring (critico)
    },

    'header': {
        'debe': [
            'Contener contenido introductorio o de navegacion',
            'Puede ser global (header del sitio) o seccional (header de article/section)'
        ],
        'no_debe': [
            'Estar dentro de <footer> o <address>',
            'Contener otro <header> o <footer>'
        ],
        'puede_repetir': True,
        'nivel_max': 3,
        'peso': 2.0
    },

    'footer': {
        'debe': [
            'Contener informacion sobre su seccion/documento',
            'Puede ser global o seccional'
        ],
        'no_debe': [
            'Estar dentro de <header> o <address>',
            'Contener otro <header> o <footer>'
        ],
        'puede_repetir': True,
        'nivel_max': 3,
        'peso': 2.0
    },

    'nav': {
        'debe': [
            'Contener navegacion principal o secciones de navegacion',
            'Usarse para bloques importantes de navegacion'
        ],
        'no_debe': [
            'Usarse para TODOS los enlaces (solo navegacion importante)',
            'Anidarse excesivamente'
        ],
        'puede_repetir': True,
        'nivel_max': 3,
        'ubicacion_preferida': ['header', 'footer'],
        'peso': 2.0
    },

    'article': {
        'debe': [
            'Ser contenido autonomo y reutilizable',
            'Tener sentido por si solo (post, noticia, comentario, widget)'
        ],
        'no_debe': [
            'Usarse solo para aplicar estilos',
            'Contener <main>'
        ],
        'puede_repetir': True,
        'jerarquia': 'Puede contener <section>, <header>, <footer>',
        'peso': 1.5
    },

    'section': {
        'debe': [
            'Agrupar contenido tematico relacionado',
            'Tipicamente tener un heading (h1-h6)'
        ],
        'no_debe': [
            'Usarse solo para aplicar estilos (usar <div> para eso)',
            'Usarse cuando <article> es mas apropiado',
            'Contener <main>'
        ],
        'puede_repetir': True,
        'jerarquia': 'Generalmente contiene <article>, no al reves',
        'peso': 1.5
    },

    'aside': {
        'debe': [
            'Contener contenido tangencialmente relacionado',
            'Usarse para sidebars, callouts, ads relacionados'
        ],
        'no_debe': [
            'Contener el contenido principal',
            'Usarse excesivamente'
        ],
        'puede_repetir': True,
        'peso': 1.0
    }
}


# Reglas anti-divitis
DIVITIS_RULES = {
    'max_div_depth': 5,      # Mas de 5 niveles = problema
    'critical_depth': 8,      # Mas de 8 niveles = critico
    'max_consecutive_divs': 3,  # Mas de 3 divs seguidos sin contenido = malo
    'ratio_threshold_warning': 0.6,  # Mas de 60% divs = warning
    'ratio_threshold_fail': 0.75,     # Mas de 75% divs = fail
}


# Jerarquias permitidas y prohibidas
JERARQUIAS = {
    'main_no_puede_estar_en': ['article', 'aside', 'footer', 'header', 'nav', 'section'],
    'header_no_puede_estar_en': ['footer', 'address', 'header'],
    'footer_no_puede_estar_en': ['header', 'address', 'footer'],
    'nav_ubicacion_preferida': ['header', 'footer', 'body'],
}


# Violaciones conocidas y su penalizacion
VIOLACIONES = {
    'main_dentro_de_section': {
        'mensaje': '<main> esta incorrectamente dentro de <section>',
        'penalizacion': 2.0,
        'severidad': 'alta'
    },
    'main_dentro_de_article': {
        'mensaje': '<main> esta incorrectamente dentro de <article>',
        'penalizacion': 2.0,
        'severidad': 'alta'
    },
    'multiples_main': {
        'mensaje': 'Multiples elementos <main> (debe ser unico)',
        'penalizacion': 1.5,
        'severidad': 'alta'
    },
    'nav_flotante': {
        'mensaje': '<nav> fuera de <header> o <footer>',
        'penalizacion': 0.5,
        'severidad': 'baja'
    },
    'divitis_severa': {
        'mensaje': 'Exceso critico de <div> (divitis)',
        'penalizacion': 3.0,
        'severidad': 'alta'
    },
    'divitis_moderada': {
        'mensaje': 'Uso excesivo de <div>',
        'penalizacion': 1.5,
        'severidad': 'media'
    },
    'falta_main': {
        'mensaje': 'Falta elemento <main> para contenido principal',
        'penalizacion': 2.0,
        'severidad': 'alta'
    },
    'falta_estructura_basica': {
        'mensaje': 'Falta estructura semantica basica (header/main/footer)',
        'penalizacion': 3.0,
        'severidad': 'alta'
    }
}


def detectar_violaciones(structure_analysis: dict) -> list:
    """
    Detecta violaciones de buenas practicas HTML5 basado en el analisis estructural.

    Args:
        structure_analysis: Dict con analisis del crawler

    Returns:
        Lista de violaciones detectadas con sus penalizaciones
    """
    violaciones = []

    # Verificar main_inside_section
    if structure_analysis.get('main_inside_section', False):
        violaciones.append(VIOLACIONES['main_dentro_de_section'])

    # Verificar multiples main
    main_count = structure_analysis.get('main_count', 0)
    if main_count > 1:
        violaciones.append(VIOLACIONES['multiples_main'])
    elif main_count == 0:
        violaciones.append(VIOLACIONES['falta_main'])

    # Verificar navs flotantes (todos fuera de header/footer)
    nav_count = structure_analysis.get('nav_count', 0)
    navs_floating = structure_analysis.get('navs_floating', 0)
    if nav_count > 0 and navs_floating == nav_count:
        violaciones.append(VIOLACIONES['nav_flotante'])

    # Verificar divitis
    has_divitis = structure_analysis.get('has_divitis', False)
    div_ratio = structure_analysis.get('div_ratio', 0)

    if has_divitis or div_ratio > DIVITIS_RULES['ratio_threshold_fail']:
        violaciones.append(VIOLACIONES['divitis_severa'])
    elif div_ratio > DIVITIS_RULES['ratio_threshold_warning']:
        violaciones.append(VIOLACIONES['divitis_moderada'])

    # Verificar estructura basica
    header_count = structure_analysis.get('header_count', 0)
    footer_count = structure_analysis.get('footer_count', 0)

    if main_count == 0 and header_count == 0 and footer_count == 0:
        violaciones.append(VIOLACIONES['falta_estructura_basica'])

    return violaciones


def calcular_penalizacion_total(violaciones: list) -> float:
    """
    Calcula la penalizacion total basada en violaciones detectadas.

    Args:
        violaciones: Lista de violaciones

    Returns:
        Penalizacion total (float)
    """
    return sum(v.get('penalizacion', 0) for v in violaciones)


def generar_recomendaciones(violaciones: list, structure_analysis: dict) -> list:
    """
    Genera recomendaciones basadas en violaciones detectadas.

    Args:
        violaciones: Lista de violaciones
        structure_analysis: Analisis estructural

    Returns:
        Lista de recomendaciones
    """
    recomendaciones = []

    for v in violaciones:
        if v == VIOLACIONES['main_dentro_de_section']:
            recomendaciones.append(
                'Mover <main> fuera de <section>. Estructura correcta: '
                '<main> contiene <section>, no al reves'
            )
        elif v == VIOLACIONES['multiples_main']:
            recomendaciones.append(
                'Usar solo un <main> por pagina para el contenido principal'
            )
        elif v == VIOLACIONES['falta_main']:
            recomendaciones.append(
                'Agregar <main> para envolver el contenido principal de la pagina'
            )
        elif v == VIOLACIONES['nav_flotante']:
            recomendaciones.append(
                'Colocar <nav> dentro de <header> para mejor semantica'
            )
        elif v == VIOLACIONES['divitis_severa']:
            recomendaciones.append(
                'Reducir uso excesivo de <div>. Reemplazar por tags semanticos: '
                '<section>, <article>, <aside>, <figure>'
            )
        elif v == VIOLACIONES['divitis_moderada']:
            recomendaciones.append(
                'Considerar reemplazar algunos <div> por elementos semanticos apropiados'
            )
        elif v == VIOLACIONES['falta_estructura_basica']:
            recomendaciones.append(
                'Implementar estructura semantica basica: <header>, <main>, <footer>'
            )

    # Recomendaciones adicionales basadas en conteos
    if structure_analysis.get('article_count', 0) == 0:
        recomendaciones.append(
            'Considerar usar <article> para contenido autonomo (noticias, posts, etc.)'
        )

    if structure_analysis.get('section_count', 0) == 0:
        recomendaciones.append(
            'Considerar usar <section> para agrupar contenido tematico'
        )

    return recomendaciones
