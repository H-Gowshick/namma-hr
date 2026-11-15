"""Query embeddings for all-MiniLM-L6-v2.

This is the same model that built the Chroma index. The ONNX file is used
so the API does not have to load PyTorch before it can accept requests.
"""

from __future__ import annotations

import threading

import numpy as np

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MAX_LENGTH = 256

_lock = threading.Lock()
_session = None
_tokenizer = None


def _load():
    global _session, _tokenizer
    if _session is not None and _tokenizer is not None:
        return _session, _tokenizer

    with _lock:
        if _session is not None and _tokenizer is not None:
            return _session, _tokenizer

        import onnxruntime as ort
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer

        onnx_path = hf_hub_download(MODEL_ID, "onnx/model.onnx")
        tokenizer_path = hf_hub_download(MODEL_ID, "tokenizer.json")
        tokenizer = Tokenizer.from_file(tokenizer_path)
        tokenizer.enable_truncation(max_length=MAX_LENGTH)
        tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        session = ort.InferenceSession(
            onnx_path,
            providers=["CPUExecutionProvider"],
        )
        _session = session
        _tokenizer = tokenizer
        return session, tokenizer


def encode(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)

    session, tokenizer = _load()
    encodings = tokenizer.encode_batch(list(texts))
    input_ids = np.array([item.ids for item in encodings], dtype=np.int64)
    attention_mask = np.array(
        [item.attention_mask for item in encodings],
        dtype=np.int64,
    )
    type_ids = []
    for item in encodings:
        ids = item.type_ids if item.type_ids else [0] * len(item.ids)
        type_ids.append(ids)
    token_type_ids = np.array(type_ids, dtype=np.int64)

    feeds = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
    }
    input_names = {item.name for item in session.get_inputs()}
    if "token_type_ids" in input_names:
        feeds["token_type_ids"] = token_type_ids

    token_embeddings = session.run(None, feeds)[0]
    mask = attention_mask.astype(np.float32)[..., None]
    summed = (token_embeddings * mask).sum(axis=1)
    counts = np.clip(mask.sum(axis=1), a_min=1e-9, a_max=None)
    pooled = summed / counts
    norms = np.linalg.norm(pooled, axis=1, keepdims=True)
    pooled = pooled / np.clip(norms, a_min=1e-12, a_max=None)
    return pooled.astype(np.float32)


def encode_one(text: str) -> list[float]:
    return encode([text])[0].tolist()
