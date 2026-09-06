from app.config import get_settings

_settings = get_settings()


def needs_review(confidence: float, validation_failed: bool) -> tuple[bool, str]:
    """Confidence alone never clears a field - a validation failure always
    forces review even at 99% confidence."""
    if validation_failed:
        if confidence < _settings.confidence_auto_accept_threshold:
            return True, "both"
        return True, "validation_failure"
    if confidence < _settings.confidence_auto_accept_threshold:
        return True, "low_confidence"
    return False, ""
