"""Motor de diapositivas HTML: modelo (``model``), render (``renderer``), reglas (``validate``) y Chrome (``browser``)."""

from .browser import BrowserError, check_layout, export_pdf, find_chrome, layout_problems
from .model import Deck, DeckError, LAYOUTS, load_deck, validate_slides
from .renderer import available_themes, render_deck, theme_css
from .validate import check_theme, contrast_ratio, lint_html

__all__ = [
    "BrowserError", "Deck", "DeckError", "LAYOUTS", "available_themes", "check_layout", "check_theme",
    "contrast_ratio", "export_pdf", "find_chrome", "layout_problems", "lint_html", "load_deck", "render_deck",
    "theme_css", "validate_slides",
]
