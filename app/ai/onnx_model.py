"""Lightweight ONNX classifier loader for trading signals.

This wrapper is optional and only used if an ONNX model path is provided.
Expected model output: probabilities or scores for classes [SELL, HOLD, BUY].
"""

from typing import List, Optional, Tuple
import numpy as np

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except Exception:  # pragma: no cover
    ONNX_AVAILABLE = False


class OnnxClassifier:
    """Simple ONNX runtime wrapper for 3-class classification."""

    def __init__(self, session: "ort.InferenceSession"):
        self.session = session
        self.input_name = session.get_inputs()[0].name
        # Use first output
        self.output_name = session.get_outputs()[0].name

    def predict(self, features: List[float]) -> Tuple[str, List[float]]:
        """Return (signal, scores) where signal in {BUY, SELL, HOLD}."""
        if not features:
            return "HOLD", []
        inputs = {self.input_name: np.asarray([features], dtype=np.float32)}
        outputs = self.session.run([self.output_name], inputs)
        scores = outputs[0].flatten().tolist()

        # Map to signal: assume order [SELL, HOLD, BUY]
        if not scores:
            return "HOLD", scores
        idx = int(np.argmax(scores))
        if idx == 0:
            return "SELL", scores
        if idx == 2:
            return "BUY", scores
        return "HOLD", scores


def load_onnx_classifier(path: str) -> Optional[OnnxClassifier]:
    """Load ONNX model if runtime is available; otherwise return None."""
    if not path:
        return None
    if not ONNX_AVAILABLE:
        return None
    try:
        sess = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        return OnnxClassifier(sess)
    except Exception:
        return None

"""
Usage example:

from app.ai.onnx_model import load_onnx_classifier
clf = load_onnx_classifier("model.onnx")
if clf:
    signal, scores = clf.predict([close, ema_fast, ema_slow, rsi, atr])
"""
