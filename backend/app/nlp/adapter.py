"""
Adaptador de datos para el módulo NLP.

Convierte el formato del Crawler al formato esperado por NLPAnalyzer.

Author: Keivi Veizan
Version: 1.0.0
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class NLPDataAdapter:
    """
    Adapta datos del Crawler al formato requerido por NLPAnalyzer.

    El Crawler extrae:
    - text_corpus: {'headings': [...], 'paragraphs': [...], 'sections': [...]}
    - links: {'internal': [...], 'external': [...], 'social': [...]}
    - forms: {'inputs_with_label': [...], 'inputs_without_label': [...]}
    - headings: {'h1': [...], 'h2': [...], ...}

    NLPAnalyzer espera:
    - sections: [{'heading': str, 'heading_level': int, 'content': str, 'word_count': int}]
    - links: [{'text': str, 'url': str}]
    - labels: [{'text': str, 'for': str}]
    - buttons: [{'text': str}]
    """

    @staticmethod
    def adapt(extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convierte datos del Crawler al formato NLPAnalyzer.

        Args:
            extracted_content: Datos extraídos por el Crawler

        Returns:
            Dict en formato NLPAnalyzer:
            {
                'url': str,
                'sections': [...],
                'links': [...],
                'labels': [...],
                'buttons': [...]
            }
        """
        logger.debug("Adaptando datos del crawler para NLPAnalyzer")

        # Extraer URL del metadata
        metadata = extracted_content.get('metadata', {})
        url = metadata.get('url', extracted_content.get('url', 'N/A'))

        # Adaptar secciones
        sections = NLPDataAdapter._adapt_sections(extracted_content)

        # Adaptar enlaces
        links = NLPDataAdapter._adapt_links(extracted_content)

        # Adaptar labels de formularios
        labels = NLPDataAdapter._adapt_labels(extracted_content)

        # Adaptar botones
        buttons = NLPDataAdapter._adapt_buttons(extracted_content)

        result = {
            'url': url,
            'sections': sections,
            'links': links,
            'labels': labels,
            'buttons': buttons
        }

        logger.info(
            f"Datos adaptados: {len(sections)} secciones, "
            f"{len(links)} enlaces, {len(labels)} labels"
        )

        return result

    @staticmethod
    def _adapt_sections(extracted: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Adapta secciones de texto para análisis de coherencia.

        Args:
            extracted: Datos del crawler

        Returns:
            Lista de secciones en formato NLPAnalyzer
        """
        sections = []

        # Opción 1: Usar text_corpus.sections si existe (formato preferido)
        text_corpus = extracted.get('text_corpus', {})
        if text_corpus and 'sections' in text_corpus:
            for section in text_corpus.get('sections', []):
                # Normalizar heading_level (puede ser "h1", "h2" o int)
                heading_level = section.get('heading_level', 2)
                if isinstance(heading_level, str):
                    # Convertir "h1" -> 1, "h2" -> 2, etc.
                    try:
                        heading_level = int(heading_level.replace('h', ''))
                    except (ValueError, AttributeError):
                        heading_level = 2

                sections.append({
                    'heading': section.get('heading', ''),
                    'heading_level': heading_level,
                    'content': section.get('content', ''),
                    'word_count': section.get('word_count', len(section.get('content', '').split()))
                })
            return sections

        # Opción 2: Construir desde headings.headings (lista de dicts)
        headings_data = extracted.get('headings', {})
        all_headings = []

        # El crawler devuelve headings como lista de dicts con 'level' y 'text'
        headings_list = headings_data.get('headings', [])
        if isinstance(headings_list, list):
            for h in headings_list:
                if isinstance(h, dict):
                    text = h.get('text', '')
                    level = h.get('level', 2)
                    if text and text.strip():
                        all_headings.append({
                            'text': text.strip(),
                            'level': level
                        })

        # Obtener párrafos para contenido
        paragraphs = []
        if text_corpus and 'paragraphs' in text_corpus:
            paragraphs = text_corpus.get('paragraphs', [])

        # Combinar headings con contenido aproximado
        if all_headings:
            # Distribuir párrafos entre headings
            paragraphs_per_heading = max(1, len(paragraphs) // len(all_headings)) if paragraphs else 0

            for i, heading in enumerate(all_headings):
                start_idx = i * paragraphs_per_heading
                end_idx = start_idx + paragraphs_per_heading
                content_paragraphs = paragraphs[start_idx:end_idx] if paragraphs else []
                content = ' '.join(content_paragraphs) if content_paragraphs else ''

                sections.append({
                    'heading': heading['text'],
                    'heading_level': heading['level'],
                    'content': content,
                    'word_count': len(content.split()) if content else 0
                })

        # Opción 3: Si no hay headings, crear sección genérica
        if not sections and paragraphs:
            full_content = ' '.join(paragraphs[:5])  # Primeros 5 párrafos
            sections.append({
                'heading': 'Contenido Principal',
                'heading_level': 1,
                'content': full_content,
                'word_count': len(full_content.split())
            })

        return sections

    @staticmethod
    def _adapt_links(extracted: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Adapta enlaces para detección de ambigüedades.

        El crawler devuelve:
        {
            'all_links': [...],
            'total_count': int,
            'empty_links': {'links': [...], 'count': int},
            'social': {'links': [...], 'count': int},
            'generic_text': {'links': [...], 'count': int},
            ...
        }

        Args:
            extracted: Datos del crawler

        Returns:
            Lista de enlaces en formato NLPAnalyzer
        """
        links = []
        links_data = extracted.get('links', {})

        def extract_links_from_list(link_list):
            """Extrae enlaces de una lista de dicts."""
            result = []
            if not isinstance(link_list, list):
                return result
            for link in link_list:
                if isinstance(link, dict):
                    text = link.get('text', '')
                    url = link.get('href', link.get('absolute_url', link.get('url', '')))
                    if text and text.strip():
                        result.append({'text': text.strip(), 'url': url or ''})
            return result

        # Opción 1: Usar all_links (todos los enlaces)
        all_links = links_data.get('all_links', [])
        if isinstance(all_links, list):
            links.extend(extract_links_from_list(all_links))
            return links  # Si hay all_links, usamos esos

        # Opción 2: Extraer de categorías anidadas
        for key in ['internal', 'external', 'navigation', 'social', 'messaging', 'generic_text']:
            category = links_data.get(key, {})
            if isinstance(category, dict):
                # Formato anidado: {'links': [...], 'count': int}
                category_links = category.get('links', [])
                links.extend(extract_links_from_list(category_links))
            elif isinstance(category, list):
                # Formato lista directa
                links.extend(extract_links_from_list(category))

        # Opción 3: Si links_data es una lista directa
        if isinstance(links_data, list):
            links.extend(extract_links_from_list(links_data))

        return links

    @staticmethod
    def _adapt_labels(extracted: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Adapta labels de formularios.

        El crawler devuelve:
        {
            'forms': [
                {
                    'action': str,
                    'method': str,
                    'inputs': [
                        {
                            'type': str,
                            'id': str,
                            'name': str,
                            'placeholder': str,
                            'has_label': bool,
                            'label_text': str or None
                        }
                    ]
                }
            ],
            'total_forms': int,
            'total_inputs': int,
            'inputs_with_label': int,  # This is a count, not a list!
            'inputs_without_label': int,
            ...
        }

        Args:
            extracted: Datos del crawler

        Returns:
            Lista de labels en formato NLPAnalyzer
        """
        labels = []
        forms_data = extracted.get('forms', {})

        # Extraer labels de forms.forms (lista de formularios)
        forms_list = forms_data.get('forms', [])
        if isinstance(forms_list, list):
            for form in forms_list:
                if not isinstance(form, dict):
                    continue
                inputs = form.get('inputs', [])
                if not isinstance(inputs, list):
                    continue
                for inp in inputs:
                    if not isinstance(inp, dict):
                        continue
                    # Si tiene label
                    if inp.get('has_label') and inp.get('label_text'):
                        label_text = inp['label_text']
                        # Limpiar placeholders marcados
                        if label_text.startswith('[placeholder:'):
                            label_text = label_text.replace('[placeholder:', '').rstrip(']').strip()
                        if label_text:
                            labels.append({
                                'text': label_text,
                                'for': inp.get('id', inp.get('name', ''))
                            })
                    # Si no tiene label pero tiene placeholder
                    elif inp.get('placeholder'):
                        labels.append({
                            'text': inp['placeholder'],
                            'for': 'placeholder'
                        })

        # Fallback: Si hay lista directa de inputs_with_label (formato legacy)
        if not labels:
            inputs_with_label = forms_data.get('inputs_with_label', [])
            if isinstance(inputs_with_label, list):
                for item in inputs_with_label:
                    if isinstance(item, dict):
                        label_text = item.get('label', item.get('label_text', ''))
                        if label_text and label_text.strip():
                            labels.append({
                                'text': label_text.strip(),
                                'for': item.get('for', item.get('id', ''))
                            })

        return labels

    @staticmethod
    def _adapt_buttons(extracted: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Adapta botones para detección de ambigüedades.

        Args:
            extracted: Datos del crawler

        Returns:
            Lista de botones en formato NLPAnalyzer
        """
        buttons = []
        forms_data = extracted.get('forms', {})

        # Botones de formularios
        for button in forms_data.get('buttons', []):
            text = button.get('text', button.get('value', '')) if isinstance(button, dict) else str(button)
            if text and text.strip():
                buttons.append({'text': text.strip()})

        # Submit inputs
        for submit in forms_data.get('submits', []):
            text = submit.get('value', '') if isinstance(submit, dict) else str(submit)
            if text and text.strip():
                buttons.append({'text': text.strip()})

        return buttons


def adapt_crawler_to_nlp(extracted_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función de conveniencia para adaptar datos.

    Args:
        extracted_content: Datos del Crawler

    Returns:
        Datos en formato NLPAnalyzer
    """
    return NLPDataAdapter.adapt(extracted_content)
