"""
Evaluador de Soberanía Digital (10%)
Evalúa 4 criterios: PROH-01 a PROH-04
"""
from typing import Dict, List
from urllib.parse import urlparse
from .base_evaluator import BaseEvaluator, CriteriaEvaluation


class EvaluadorSoberania(BaseEvaluator):
    """
    Evaluador de criterios de soberanía digital
    """

    def __init__(self):
        super().__init__(dimension="soberania")

        # Pesos según tabla_final.xlsx
        self.criterios = {
            "PROH-01": {"name": "Sin Google Analytics", "points": 25, "lineamiento": "D.S. 3925 (PROH-01)"},
            "PROH-02": {"name": "Sin servicios de terceros no autorizados", "points": 25, "lineamiento": "D.S. 3925 (PROH-02)"},
            "PROH-03": {"name": "Hosting en Bolivia o autorizados", "points": 25, "lineamiento": "D.S. 3925 (PROH-03)"},
            "PROH-04": {"name": "Sin publicidad externa", "points": 25, "lineamiento": "D.S. 3925 (PROH-04)"}
        }

    def evaluate(self, extracted_content: Dict) -> List[CriteriaEvaluation]:
        """Evalúa todos los criterios de soberanía digital"""
        self.clear_results()

        # Extraer datos relevantes
        external_resources = extracted_content.get('external_resources', {})
        structure = extracted_content.get('structure', {})

        # Evaluar cada criterio
        self.add_result(self._evaluar_proh01(external_resources))
        self.add_result(self._evaluar_proh02(external_resources))
        self.add_result(self._evaluar_proh03(external_resources))
        self.add_result(self._evaluar_proh04(external_resources, structure))

        return self.results

    def _evaluar_proh01(self, external_resources: Dict) -> CriteriaEvaluation:
        """
        PROH-01: Sin Google Analytics
        No debe usar Google Analytics, Google Tag Manager u otros servicios de tracking de Google
        """
        scripts = external_resources.get('scripts', [])

        google_services = []
        google_patterns = [
            'google-analytics.com',
            'googletagmanager.com',
            'analytics.google.com',
            'ga.js',
            'gtag.js',
            'gtm.js'
        ]

        for script in scripts:
            script_lower = script.lower()
            for pattern in google_patterns:
                if pattern in script_lower:
                    google_services.append(script)
                    break

        if len(google_services) == 0:
            status = "pass"
            score = 25
            message = "No se detectó Google Analytics u otros servicios de tracking de Google"
        else:
            status = "fail"
            score = 0
            message = f"Se detectaron {len(google_services)} servicio(s) de Google"

        return CriteriaEvaluation(
            criteria_id="PROH-01",
            criteria_name=self.criterios["PROH-01"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PROH-01"]["lineamiento"],
            status=status,
            score=score,
            max_score=25,
            details={
                "google_services_count": len(google_services),
                "scripts_analyzed": len(scripts),
                "message": message
            },
            evidence={
                "google_services_detected": google_services[:5]  # Primeros 5 ejemplos
            }
        )

    def _evaluar_proh02(self, external_resources: Dict) -> CriteriaEvaluation:
        """
        PROH-02: Sin servicios de terceros no autorizados
        No debe usar CDNs o servicios externos no autorizados
        """
        scripts = external_resources.get('scripts', [])
        stylesheets = external_resources.get('stylesheets', [])

        # Servicios comunes de terceros (además de Google)
        third_party_services = {
            'facebook': ['facebook.com', 'fbcdn.net', 'fb.com'],
            'twitter': ['twitter.com', 'twimg.com'],
            'cloudflare': ['cloudflare.com', 'cdnjs.cloudflare.com'],
            'jsdelivr': ['jsdelivr.net'],
            'unpkg': ['unpkg.com'],
            'amazonaws': ['amazonaws.com', 's3.amazonaws.com'],
            'gstatic': ['gstatic.com']
        }

        detected_services = {}
        all_resources = scripts + stylesheets

        for resource in all_resources:
            resource_lower = resource.lower()
            for service_name, patterns in third_party_services.items():
                for pattern in patterns:
                    if pattern in resource_lower:
                        if service_name not in detected_services:
                            detected_services[service_name] = []
                        detected_services[service_name].append(resource)
                        break

        # CDNs autorizados (ejemplo: pueden tener lista blanca)
        authorized_cdns = ['cdnjs.cloudflare.com']  # Ejemplo

        # Filtrar servicios no autorizados
        unauthorized = {}
        for service, resources in detected_services.items():
            for resource in resources:
                is_authorized = any(auth in resource for auth in authorized_cdns)
                if not is_authorized:
                    if service not in unauthorized:
                        unauthorized[service] = []
                    unauthorized[service].append(resource)

        total_unauthorized = sum(len(resources) for resources in unauthorized.values())

        if total_unauthorized == 0:
            status = "pass"
            score = 25
            message = "No se detectaron servicios de terceros no autorizados"
        elif total_unauthorized <= 2:
            status = "partial"
            score = 12
            message = f"Se detectaron {total_unauthorized} recursos de terceros"
        else:
            status = "fail"
            score = 0
            message = f"Se detectaron {total_unauthorized} recursos de terceros no autorizados"

        return CriteriaEvaluation(
            criteria_id="PROH-02",
            criteria_name=self.criterios["PROH-02"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PROH-02"]["lineamiento"],
            status=status,
            score=score,
            max_score=25,
            details={
                "total_unauthorized": total_unauthorized,
                "services_detected": list(unauthorized.keys()),
                "total_resources_analyzed": len(all_resources),
                "message": message
            },
            evidence={
                "unauthorized_services": {k: v[:3] for k, v in unauthorized.items()}  # Primeros 3 de cada uno
            }
        )

    def _evaluar_proh03(self, external_resources: Dict) -> CriteriaEvaluation:
        """
        PROH-03: Hosting en Bolivia o autorizados
        Recursos deben estar en dominios .bo o autorizados
        """
        scripts = external_resources.get('scripts', [])
        stylesheets = external_resources.get('stylesheets', [])
        all_resources = scripts + stylesheets

        bolivia_domains = 0
        foreign_domains = 0
        relative_resources = 0

        for resource in all_resources:
            if not resource or resource.startswith('//') or resource.startswith('data:'):
                continue

            if resource.startswith('/') or not resource.startswith('http'):
                # Recurso relativo (local)
                relative_resources += 1
                bolivia_domains += 1
            else:
                # Recurso absoluto
                try:
                    parsed = urlparse(resource)
                    domain = parsed.netloc.lower()

                    if '.bo' in domain or 'gob.bo' in domain:
                        bolivia_domains += 1
                    else:
                        foreign_domains += 1
                except:
                    continue

        total_analyzed = bolivia_domains + foreign_domains

        if total_analyzed == 0:
            compliance = 100
        else:
            compliance = (bolivia_domains / total_analyzed) * 100

        score = (compliance / 100) * 25

        if compliance >= 90:
            status = "pass"
        elif compliance >= 70:
            status = "partial"
        else:
            status = "fail"

        return CriteriaEvaluation(
            criteria_id="PROH-03",
            criteria_name=self.criterios["PROH-03"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PROH-03"]["lineamiento"],
            status=status,
            score=round(score, 2),
            max_score=25,
            details={
                "bolivia_domains": bolivia_domains,
                "foreign_domains": foreign_domains,
                "relative_resources": relative_resources,
                "total_analyzed": total_analyzed,
                "compliance_percentage": round(compliance, 2),
                "message": f"{bolivia_domains}/{total_analyzed} recursos en dominios bolivianos o locales"
            },
            evidence={
                "total_scripts": len(scripts),
                "total_stylesheets": len(stylesheets)
            }
        )

    def _evaluar_proh04(self, external_resources: Dict, structure: Dict) -> CriteriaEvaluation:
        """
        PROH-04: Sin publicidad externa
        No debe tener scripts de publicidad (AdSense, AdWords, etc.)
        """
        scripts = external_resources.get('scripts', [])

        ad_services = []
        ad_patterns = [
            'adsense',
            'adwords',
            'doubleclick',
            'googlesyndication',
            'adserver',
            'advertising',
            'ads.',
            '/ads/',
            'adservice'
        ]

        for script in scripts:
            script_lower = script.lower()
            for pattern in ad_patterns:
                if pattern in script_lower:
                    ad_services.append(script)
                    break

        # También buscar iframes de publicidad (placeholder)
        # En implementación completa se buscaría en structure

        if len(ad_services) == 0:
            status = "pass"
            score = 25
            message = "No se detectó publicidad externa"
        else:
            status = "fail"
            score = 0
            message = f"Se detectaron {len(ad_services)} servicio(s) de publicidad"

        return CriteriaEvaluation(
            criteria_id="PROH-04",
            criteria_name=self.criterios["PROH-04"]["name"],
            dimension=self.dimension,
            lineamiento=self.criterios["PROH-04"]["lineamiento"],
            status=status,
            score=score,
            max_score=25,
            details={
                "ad_services_count": len(ad_services),
                "scripts_analyzed": len(scripts),
                "message": message
            },
            evidence={
                "ad_services_detected": ad_services[:5]  # Primeros 5 ejemplos
            }
        )
