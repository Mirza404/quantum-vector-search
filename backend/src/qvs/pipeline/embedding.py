from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Sequence
import hashlib
import random

import numpy as np


class EmbeddingGenerator(ABC):
    """Strategy interface for turning text into embedding vectors."""

    @abstractmethod
    def embed(self, text: str, *, dimension: int) -> List[float]:
        """Return a deterministic embedding of length == dimension."""

    def embed_many(self, texts: Sequence[str], *, dimension: int) -> List[List[float]]:
        return [self.embed(text, dimension=dimension) for text in texts]


class MockCLIPEmbeddingGenerator(EmbeddingGenerator):
    """Deterministic pseudo-CLIP implementation used for local testing."""

    def __init__(self, *, seed: str = "mock-clip") -> None:
        self._seed = seed

    def embed(self, text: str, *, dimension: int) -> List[float]:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        digest = hashlib.sha256(f"{self._seed}:{text}".encode("utf-8")).hexdigest()
        rng = random.Random(int(digest, 16))
        vector = [rng.uniform(-1.0, 1.0) for _ in range(dimension)]
        return vector


class CLIPEmbeddingModel:
    """Thin wrapper around OpenAI CLIP for both text and image embeddings."""

    def __init__(
        self,
        *,
        model_name: str = "ViT-B/32",
        device: str | None = None,
        batch_size: int = 32,
        normalize: bool = True,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        try:
            import clip as clip_lib  # type: ignore
            import torch as torch_lib
            from PIL import Image as pil_image
        except ImportError as exc:  # pragma: no cover - defensive guard
            raise RuntimeError(
                "CLIPEmbeddingModel requires the 'clip', 'torch', and 'Pillow' packages to be installed"
            ) from exc
        self._clip = clip_lib
        self._torch = torch_lib
        self._pil_image = pil_image
        self._device = self._resolve_device(torch_lib, device)
        self._batch_size = batch_size
        self._normalize_default = normalize
        self._model, self._preprocess = clip_lib.load(model_name, device=self._device)
        if self._device.type == "cpu":
            self._model = self._model.float()
        self._model.eval()
        with torch_lib.inference_mode():
            probe = clip_lib.tokenize(["dimension-probe"], truncate=True).to(self._device)
            features = self._model.encode_text(probe)
        self._embedding_dim = int(features.shape[-1])

    @staticmethod
    def _resolve_device(torch_lib: "torch", preferred: str | None) -> "torch.device":
        if preferred:
            return torch_lib.device(preferred)
        if torch_lib.cuda.is_available():
            return torch_lib.device("cuda")
        if hasattr(torch_lib.backends, "mps") and torch_lib.backends.mps.is_available():
            return torch_lib.device("mps")
        return torch_lib.device("cpu")

    @property
    def embedding_dimension(self) -> int:
        return self._embedding_dim

    def encode_texts(
        self,
        texts: Sequence[str],
        *,
        batch_size: int | None = None,
        normalize: bool | None = None,
    ) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._embedding_dim), dtype=np.float32)
        bs = batch_size or self._batch_size
        norm = self._normalize_default if normalize is None else normalize
        tensors = []
        for start in range(0, len(texts), bs):
            chunk = texts[start : start + bs]
            tokens = self._clip.tokenize(chunk, truncate=True).to(self._device)
            with self._torch.inference_mode():
                features = self._model.encode_text(tokens)
            features = features.float()
            if norm:
                features = self._torch.nn.functional.normalize(features, p=2, dim=-1)
            tensors.append(features.cpu())
        matrix = self._torch.cat(tensors, dim=0).contiguous()
        return matrix.numpy()

    def encode_images(
        self,
        image_paths: Sequence[str | Path],
        *,
        batch_size: int | None = None,
        normalize: bool | None = None,
    ) -> np.ndarray:
        if not image_paths:
            return np.zeros((0, self._embedding_dim), dtype=np.float32)
        bs = batch_size or self._batch_size
        norm = self._normalize_default if normalize is None else normalize
        tensors = []
        for start in range(0, len(image_paths), bs):
            chunk = image_paths[start : start + bs]
            batch_tensors = []
            for raw_path in chunk:
                path = Path(raw_path)
                if not path.exists():
                    raise FileNotFoundError(f"image not found: {path}")
                with self._pil_image.open(path) as image:
                    batch_tensors.append(self._preprocess(image.convert("RGB")))
            pixel_batch = self._torch.stack(batch_tensors).to(self._device)
            with self._torch.inference_mode():
                features = self._model.encode_image(pixel_batch)
            features = features.float()
            if norm:
                features = self._torch.nn.functional.normalize(features, p=2, dim=-1)
            tensors.append(features.cpu())
        matrix = self._torch.cat(tensors, dim=0).contiguous()
        return matrix.numpy()


class CLIPTextEmbeddingGenerator(EmbeddingGenerator):
    """Strategy adapter that feeds text through the CLIP text encoder."""

    def __init__(
        self,
        *,
        model: CLIPEmbeddingModel | None = None,
        model_name: str = "ViT-B/32",
        device: str | None = None,
        batch_size: int = 32,
        normalize: bool = True,
    ) -> None:
        self._model = model or CLIPEmbeddingModel(
            model_name=model_name,
            device=device,
            batch_size=batch_size,
            normalize=normalize,
        )
        self._normalize = normalize

    def embed(self, text: str, *, dimension: int) -> List[float]:
        self._validate_dim(dimension)
        vector = self._model.encode_texts([text], normalize=self._normalize)[0]
        return self._trim(vector, dimension)

    def embed_many(self, texts: Sequence[str], *, dimension: int) -> List[List[float]]:
        self._validate_dim(dimension)
        if not texts:
            return []
        matrix = self._model.encode_texts(texts, normalize=self._normalize)
        return [self._trim(vector, dimension) for vector in matrix]

    def _validate_dim(self, dimension: int) -> None:
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        if dimension > self._model.embedding_dimension:
            raise ValueError(
                f"dimension {dimension} exceeds CLIP output size {self._model.embedding_dimension}"
            )

    @staticmethod
    def _trim(vector: np.ndarray, dimension: int) -> List[float]:
        return vector[:dimension].astype(np.float32).tolist()
