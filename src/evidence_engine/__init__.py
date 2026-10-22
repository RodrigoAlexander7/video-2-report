"""Evidencia reproducible: comandos reales -> log + figura + manifiesto verificable."""
from .capture import capture_commands, capture_vdmj, register_image
from .manifest import load_manifest
from .verify import verify_manifest, verify_claims

__all__ = ["capture_commands", "capture_vdmj", "register_image", "load_manifest",
           "verify_manifest", "verify_claims"]
