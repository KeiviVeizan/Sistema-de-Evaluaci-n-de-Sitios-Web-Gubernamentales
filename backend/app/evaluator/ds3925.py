"""
Evaluador de cumplimiento del Decreto Supremo 3925.

Implementa la verificación de criterios establecidos en el D.S. 3925
para sitios web gubernamentales bolivianos.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DS3925Criteria:
    """
    Criterio del D.S. 3925.

    Attributes:
        code: Código del criterio (ej: DS-001)
        name: Nombre del criterio
        description: Descripción detallada
        category: Categoría (soberanía digital, datos abiertos, etc.)
        weight: Peso del criterio en la evaluación (0-1)
    """
    code: str
    name: str
    description: str
    category: str
    weight: float = 1.0


class DS3925Evaluator:
    """
    Evaluador de cumplimiento del Decreto Supremo 3925.

    Verifica el cumplimiento de criterios de soberanía digital,
    uso de software libre, datos abiertos y estándares web.
    """

    # Criterios del D.S. 3925
    CRITERIA = [
        # Soberanía Digital
        DS3925Criteria(
            code="DS-001",
            name="Dominio .gob.bo",
            description="El sitio debe usar dominio .gob.bo oficial",
            category="soberania_digital",
            weight=2.0
        ),
        DS3925Criteria(
            code="DS-002",
            name="Hosting en Bolivia",
            description="Preferencia por hosting en servidores nacionales",
            category="soberania_digital",
            weight=1.5
        ),
        DS3925Criteria(
            code="DS-003",
            name="Certificado SSL/TLS",
            description="Uso de HTTPS para conexiones seguras",
            category="soberania_digital",
            weight=2.0
        ),

        # Software Libre
        DS3925Criteria(
            code="DS-004",
            name="Tecnologías de código abierto",
            description="Preferencia por tecnologías de código abierto",
            category="software_libre",
            weight=1.0
        ),
        DS3925Criteria(
            code="DS-005",
            name="Formatos abiertos",
            description="Uso de formatos de documentos abiertos (ODF, PDF/A)",
            category="software_libre",
            weight=1.5
        ),

        # Datos Abiertos
        DS3925Criteria(
            code="DS-006",
            name="Datos abiertos disponibles",
            description="Publicación de datasets en formatos abiertos",
            category="datos_abiertos",
            weight=1.5
        ),
        DS3925Criteria(
            code="DS-007",
            name="API de datos",
            description="Disponibilidad de API para acceso a datos",
            category="datos_abiertos",
            weight=1.0
        ),

        # Transparencia
        DS3925Criteria(
            code="DS-008",
            name="Información institucional",
            description="Información clara sobre la institución",
            category="transparencia",
            weight=2.0
        ),
        DS3925Criteria(
            code="DS-009",
            name="Contacto accesible",
            description="Información de contacto visible y accesible",
            category="transparencia",
            weight=1.5
        ),
        DS3925Criteria(
            code="DS-010",
            name="Actualización periódica",
            description="Contenido actualizado regularmente",
            category="transparencia",
            weight=1.0
        ),
    ]

    def __init__(self):
        """Inicializa el evaluador DS3925."""
        self.criteria_dict = {c.code: c for c in self.CRITERIA}
        logger.info("Evaluador D.S. 3925 inicializado")

    def evaluate(self, page_data: Dict) -> Dict[str, any]:
        """
        Evalúa una página según criterios del D.S. 3925.

        Args:
            page_data: Datos extraídos de la página web

        Returns:
            dict: Resultados de la evaluación por criterio
        """
        results = {}

        # Evaluar cada criterio
        results["DS-001"] = self._check_gob_bo_domain(page_data)
        results["DS-002"] = self._check_national_hosting(page_data)
        results["DS-003"] = self._check_ssl_certificate(page_data)
        results["DS-004"] = self._check_open_source_tech(page_data)
        results["DS-005"] = self._check_open_formats(page_data)
        results["DS-006"] = self._check_open_data(page_data)
        results["DS-007"] = self._check_data_api(page_data)
        results["DS-008"] = self._check_institutional_info(page_data)
        results["DS-009"] = self._check_contact_info(page_data)
        results["DS-010"] = self._check_content_freshness(page_data)

        return results

    def _check_gob_bo_domain(self, data: Dict) -> Dict:
        """Verifica uso de dominio .gob.bo"""
        url = data.get('url', '')
        passed = '.gob.bo' in url.lower()

        return {
            'status': 'pass' if passed else 'fail',
            'score': 100 if passed else 0,
            'details': {
                'url': url,
                'message': 'Dominio .gob.bo válido' if passed else 'No usa dominio .gob.bo'
            }
        }

    def _check_national_hosting(self, data: Dict) -> Dict:
        """Verifica hosting nacional (requiere análisis adicional)"""
        # TODO: Implementar verificación de IP y geolocalización
        return {
            'status': 'na',
            'score': None,
            'details': {
                'message': 'Verificación de hosting requiere análisis de IP'
            }
        }

    def _check_ssl_certificate(self, data: Dict) -> Dict:
        """Verifica uso de HTTPS"""
        url = data.get('url', '')
        passed = url.startswith('https://')

        return {
            'status': 'pass' if passed else 'fail',
            'score': 100 if passed else 0,
            'details': {
                'message': 'Usa HTTPS' if passed else 'No usa HTTPS (inseguro)'
            }
        }

    def _check_open_source_tech(self, data: Dict) -> Dict:
        """Verifica uso de tecnologías de código abierto"""
        # TODO: Implementar detección de tecnologías
        return {
            'status': 'na',
            'score': None,
            'details': {
                'message': 'Requiere análisis de tecnologías del servidor'
            }
        }

    def _check_open_formats(self, data: Dict) -> Dict:
        """Verifica uso de formatos abiertos en documentos"""
        # TODO: Analizar enlaces a documentos
        return {
            'status': 'na',
            'score': None,
            'details': {
                'message': 'Requiere análisis de documentos enlazados'
            }
        }

    def _check_open_data(self, data: Dict) -> Dict:
        """Verifica disponibilidad de datos abiertos"""
        text = data.get('text_content', '').lower()
        keywords = ['datos abiertos', 'open data', 'dataset', 'descargar datos']

        found = any(keyword in text for keyword in keywords)

        return {
            'status': 'pass' if found else 'fail',
            'score': 100 if found else 0,
            'details': {
                'message': 'Referencias a datos abiertos encontradas' if found
                          else 'No se encontraron referencias a datos abiertos'
            }
        }

    def _check_data_api(self, data: Dict) -> Dict:
        """Verifica disponibilidad de API"""
        text = data.get('text_content', '').lower()
        keywords = ['api', 'web service', 'servicios web', 'rest', 'endpoint']

        found = any(keyword in text for keyword in keywords)

        return {
            'status': 'pass' if found else 'fail',
            'score': 100 if found else 0,
            'details': {
                'message': 'Referencias a API encontradas' if found
                          else 'No se encontraron referencias a API'
            }
        }

    def _check_institutional_info(self, data: Dict) -> Dict:
        """Verifica información institucional"""
        keywords = ['misión', 'visión', 'objetivo', 'acerca de', 'quiénes somos']
        text = data.get('text_content', '').lower()

        found = any(keyword in text for keyword in keywords)

        return {
            'status': 'pass' if found else 'fail',
            'score': 100 if found else 50,
            'details': {
                'message': 'Información institucional presente' if found
                          else 'Información institucional limitada'
            }
        }

    def _check_contact_info(self, data: Dict) -> Dict:
        """Verifica información de contacto"""
        keywords = ['contacto', 'teléfono', 'correo', 'email', 'dirección']
        text = data.get('text_content', '').lower()

        found = any(keyword in text for keyword in keywords)

        return {
            'status': 'pass' if found else 'fail',
            'score': 100 if found else 0,
            'details': {
                'message': 'Información de contacto disponible' if found
                          else 'No se encuentra información de contacto'
            }
        }

    def _check_content_freshness(self, data: Dict) -> Dict:
        """Verifica actualización de contenido"""
        # TODO: Implementar verificación de fechas
        return {
            'status': 'na',
            'score': None,
            'details': {
                'message': 'Requiere análisis de fechas de actualización'
            }
        }

    def get_criteria_by_code(self, code: str) -> Optional[DS3925Criteria]:
        """
        Obtiene un criterio por su código.

        Args:
            code: Código del criterio

        Returns:
            DS3925Criteria: Criterio encontrado o None
        """
        return self.criteria_dict.get(code)

    def get_criteria_by_category(self, category: str) -> List[DS3925Criteria]:
        """
        Obtiene todos los criterios de una categoría.

        Args:
            category: Nombre de la categoría

        Returns:
            list: Lista de criterios de la categoría
        """
        return [c for c in self.CRITERIA if c.category == category]
