#!/usr/bin/env python3
"""Download a deterministic Flickr30k subset via Hugging Face's dataset viewer API.

Every run wipes backend/data/images/ and regenerates backend/data/ground_truth.jsonc from scratch.

Usage (from backend/):
    python3 scripts/import_dataset.py
"""
from __future__ import annotations

import json
import os
import shutil
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
import yaml
from PIL import Image

BACKEND_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = BACKEND_ROOT / "data" / "images"
GROUND_TRUTH_PATH = BACKEND_ROOT / "data" / "ground_truth.jsonc"
DATASET_NAME = "nlphuji/flickr30k"
FILTER_API_URL = "https://datasets-server.huggingface.co/filter"
SPLITS_API_URL = "https://datasets-server.huggingface.co/splits"
USER_AGENT = "quantum-vector-search-importer/1.0"
HF_TOKEN_ENV_VARS = ("HF_TOKEN", "HUGGINGFACE_TOKEN")

_dataset_cfg = yaml.safe_load((BACKEND_ROOT / "config" / "dataset.yaml").read_text())
NUM_IMAGES: int = _dataset_cfg["num_images"]
DATASET_CONFIG: str | None = _dataset_cfg.get("config")
DATASET_SPLIT: str | None = _dataset_cfg.get("split")


def _build_headers() -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT}
    for env_var in HF_TOKEN_ENV_VARS:
        token = os.environ.get(env_var)
        if token:
            headers["Authorization"] = f"Bearer {token}"
            break
    return headers


def _resolve_dataset_coordinates(
    config_name: str | None, split_name: str | None, headers: dict[str, str]
) -> tuple[str, str]:
    try:
        response = requests.get(
            SPLITS_API_URL,
            params={"dataset": DATASET_NAME},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SystemExit(
            f"Failed to list splits for {DATASET_NAME} via dataset viewer: {exc}"
        ) from exc

    payload = response.json()
    splits: list[dict[str, Any]] = payload.get("splits", [])
    if not splits:
        raise SystemExit(
            f"Dataset viewer reported no available splits for {DATASET_NAME}."
        )

    all_configs = sorted({entry["config"] for entry in splits})
    all_splits_for_config: dict[str, set[str]] = {}
    for entry in splits:
        all_splits_for_config.setdefault(entry["config"], set()).add(entry["split"])

    resolved_config = config_name or all_configs[0]
    if resolved_config not in all_configs:
        if len(all_configs) == 1:
            print(
                f"Config '{resolved_config}' not found; using available config '{all_configs[0]}'."
            )
            resolved_config = all_configs[0]
        else:
            raise SystemExit(
                "Invalid dataset config. Available configs: "
                + ", ".join(all_configs)
            )

    available_splits = sorted(all_splits_for_config.get(resolved_config, set()))
    if not available_splits:
        raise SystemExit(
            f"Dataset viewer returned no splits for config '{resolved_config}'."
        )

    resolved_split = split_name or available_splits[0]
    if resolved_split not in available_splits:
        raise SystemExit(
            f"Split '{resolved_split}' not found for config '{resolved_config}'. "
            f"Available splits: {', '.join(available_splits)}"
        )

    return resolved_config, resolved_split


PAGE_SIZE = 100  # /filter endpoint maximum per request


def _fetch_rows(
    *, num_images: int, config_name: str, split_name: str, headers: dict[str, str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while offset < num_images:
        length = min(PAGE_SIZE, num_images - offset)
        params = {
            "dataset": DATASET_NAME,
            "config": config_name,
            "split": split_name,
            "orderby": '"filename"',
            "offset": offset,
            "length": length,
        }
        try:
            response = requests.get(FILTER_API_URL, params=params, headers=headers, timeout=60)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SystemExit(
                f"Failed to load rows from Hugging Face dataset viewer ({DATASET_NAME}): {exc}"
            ) from exc

        payload = response.json()
        page = payload.get("rows")
        if not page:
            break
        rows.extend(entry["row"] for entry in page)
        offset += len(page)

    if len(rows) < num_images:
        raise SystemExit(
            f"Requested {num_images} rows but dataset viewer only returned {len(rows)}. "
            "Reduce num_images or verify the dataset split."
        )

    return rows[:num_images]


def _download_image_bytes(url: str, headers: dict[str, str]) -> bytes:
    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SystemExit(f"Failed to download image from {url}: {exc}") from exc
    return response.content


def main() -> None:
    headers = _build_headers()
    resolved_config, resolved_split = _resolve_dataset_coordinates(
        DATASET_CONFIG, DATASET_SPLIT, headers
    )
    print(
        f"Loading {DATASET_NAME} via dataset viewer "
        f"(config='{resolved_config}', split='{resolved_split}', rows={NUM_IMAGES})..."
    )
    rows = _fetch_rows(
        num_images=NUM_IMAGES,
        config_name=resolved_config,
        split_name=resolved_split,
        headers=headers,
    )

    # Wipe and recreate images directory
    if IMAGES_DIR.exists():
        shutil.rmtree(IMAGES_DIR)
    IMAGES_DIR.mkdir(parents=True)

    ground_truth: list[dict[str, str]] = []

    for row in rows:
        # Use filename stem (e.g. "1000092795" from "1000092795.jpg") as the stable ID.
        # The dataset's img_id column is just a running index and does not match the Flickr ID.
        img_id = Path(row["filename"]).stem
        captions: list[str] = row["caption"]
        image_url = row["image"]["src"]

        image_bytes = _download_image_bytes(image_url, headers=headers)
        with Image.open(BytesIO(image_bytes)) as image:
            image.convert("RGB").save(IMAGES_DIR / f"{img_id}.webp", format="WEBP", quality=85)

        ground_truth.append({
            "id": f"query_{img_id}",
            "text": captions[0],
        })

    # Write ground_truth.jsonc
    header = (
        "// ground_truth.jsonc — generated by import_dataset.py, do not edit manually.\n"
        "// Each query targets the image whose filename matches the id with 'query_' stripped.\n"
    )
    body = json.dumps(ground_truth, indent=2, ensure_ascii=False)
    GROUND_TRUTH_PATH.write_text(header + body + "\n", encoding="utf-8")

    print(f"Saved {len(rows)} WebP images to {IMAGES_DIR}")
    print(f"Ground truth written to {GROUND_TRUTH_PATH}")
    print("\nQuery IDs for benchmarks.yaml:")
    for entry in ground_truth:
        print(f"  - {entry['id']}")


if __name__ == "__main__":
    main()
