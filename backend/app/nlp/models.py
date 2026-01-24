"""
Gestión de modelos de NLP (BETO).

Este módulo encapsula la carga, gestión y uso del modelo BETO pre-entrenado
para análisis de lenguaje natural en español.

References:
    Cañete, J., et al. (2020). Spanish Pre-Trained BERT Model and
    Evaluation Data. In PML4DC at ICLR 2020.
"""

import logging
from typing import Optional
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

logger = logging.getLogger(__name__)


class BETOModelManager:
    """
    Gestor singleton del modelo BETO para análisis de texto en español.

    Attributes:
        model_name: dccuchile/bert-base-spanish-wwm-cased
        device: cuda o cpu (detectado automáticamente)
        _model: Modelo BETO cargado (lazy loading)
        _tokenizer: Tokenizador asociado
        _is_loaded: Flag de estado de carga

    Example:
        >>> manager = BETOModelManager()
        >>> embedding = manager.encode("Texto de ejemplo")
        >>> embedding.shape
        (768,)
    """

    _instance: Optional['BETOModelManager'] = None

    def __new__(cls):
        """Implementa patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializa el gestor sin cargar el modelo (lazy loading)."""
        if not hasattr(self, '_initialized'):
            self.model_name = "dccuchile/bert-base-spanish-wwm-cased"
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model: Optional[AutoModel] = None
            self._tokenizer: Optional[AutoTokenizer] = None
            self._is_loaded = False
            self._initialized = True
            logger.info(f"BETOModelManager inicializado (device: {self.device})")

    def load_model(self) -> None:
        """
        Carga el modelo BETO y su tokenizador.

        Raises:
            RuntimeError: Si falla la carga del modelo
        """
        if self._is_loaded:
            logger.debug("Modelo BETO ya está cargado")
            return

        try:
            logger.info(f"Cargando modelo BETO: {self.model_name}")

            # Cargar tokenizador
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                use_fast=True
            )

            # Cargar modelo
            self._model = AutoModel.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32
            ).to(self.device)

            # Modo evaluación
            self._model.eval()

            self._is_loaded = True
            logger.info("Modelo BETO cargado exitosamente")

        except Exception as e:
            logger.error(f"Error al cargar modelo BETO: {str(e)}")
            raise RuntimeError(f"Fallo en carga de modelo: {str(e)}") from e

    def encode(
        self,
        text: str,
        max_length: int = 512,
        pooling: str = 'mean'
    ) -> np.ndarray:
        """
        Genera embedding vectorial de un texto usando BETO.

        Args:
            text: Texto a codificar
            max_length: Longitud máxima de tokens
            pooling: Estrategia ('mean', 'cls', 'max')

        Returns:
            Vector embedding [768]

        Raises:
            ValueError: Si el texto está vacío
            RuntimeError: Si el modelo no está cargado
        """
        if not text or not text.strip():
            raise ValueError("El texto no puede estar vacío")

        if not self._is_loaded:
            self.load_model()

        try:
            # Tokenizar
            inputs = self._tokenizer(
                text,
                max_length=max_length,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            ).to(self.device)

            # Inferencia
            with torch.no_grad():
                outputs = self._model(**inputs)

            # Extraer embeddings
            last_hidden_state = outputs.last_hidden_state

            # Aplicar pooling
            if pooling == 'mean':
                attention_mask = inputs['attention_mask']
                mask_expanded = attention_mask.unsqueeze(-1).expand(
                    last_hidden_state.size()
                ).float()
                sum_embeddings = torch.sum(last_hidden_state * mask_expanded, dim=1)
                sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
                embedding = sum_embeddings / sum_mask
            elif pooling == 'cls':
                embedding = last_hidden_state[:, 0, :]
            else:
                raise ValueError(f"Pooling inválido: {pooling}")

            return embedding.cpu().numpy().squeeze()

        except Exception as e:
            logger.error(f"Error al generar embedding: {str(e)}")
            raise RuntimeError(f"Fallo en encoding: {str(e)}") from e

    def compute_similarity(
        self,
        text1: str,
        text2: str,
        metric: str = 'cosine'
    ) -> float:
        """
        Calcula similitud semántica entre dos textos.

        Args:
            text1: Primer texto
            text2: Segundo texto
            metric: Métrica ('cosine', 'euclidean')

        Returns:
            Score de similitud [0, 1] para coseno

        Example:
            >>> sim = manager.compute_similarity(
            ...     "Servicios de Salud",
            ...     "Atención médica y programas de vacunación"
            ... )
            >>> sim
            0.823
        """
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)

        if metric == 'cosine':
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        else:
            raise ValueError(f"Métrica inválida: {metric}")


# Singleton global
beto_manager = BETOModelManager()
