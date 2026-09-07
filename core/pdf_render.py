from __future__ import annotations
import logging
from typing import Tuple
import fitz

logger = logging.getLogger(__name__)

LARGE_PAGE_LIMIT_PT = 1500.0
LARGE_PAGE_DPI = 135
NORMAL_PAGE_DPI = 200
MAX_RENDER_PIXELS = 2200


def get_page_dimensions(page: fitz.Page) -> Tuple[float, float]:
    rect = page.rect
    return float(rect.width), float(rect.height)


def get_adaptive_dpi(
    page: fitz.Page,
    normal_dpi: int = NORMAL_PAGE_DPI,
    large_page_dpi: int = LARGE_PAGE_DPI,
    large_page_limit_pt: float = LARGE_PAGE_LIMIT_PT,
) -> int:
    w, h = get_page_dimensions(page)
    if max(w, h) > large_page_limit_pt:
        return large_page_dpi
    return normal_dpi


def render_page_adaptive(
    page: fitz.Page,
    normal_dpi: int = NORMAL_PAGE_DPI,
    large_page_dpi: int = LARGE_PAGE_DPI,
    max_pixels: int = MAX_RENDER_PIXELS,
) -> fitz.Pixmap:
    dpi = get_adaptive_dpi(page, normal_dpi=normal_dpi, large_page_dpi=large_page_dpi)
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False, colorspace=fitz.csRGB)
    largest = max(pixmap.width, pixmap.height)
    if largest <= max_pixels:
        return pixmap
    reduction = max_pixels / float(largest)
    reduced_matrix = fitz.Matrix(scale * reduction, scale * reduction)
    return page.get_pixmap(matrix=reduced_matrix, alpha=False, colorspace=fitz.csRGB)


def extract_clean_page_text(page: fitz.Page) -> str:
    from core.sanitizer import clean_cad_text
    return clean_cad_text(page.get_text("text") or "")


def iter_rendered_pages(document: fitz.Document):
    for i in range(len(document)):
        page = document.load_page(i)
        try:
            pixmap = render_page_adaptive(page)
            yield i, page, pixmap
        except Exception:
            logger.exception("Échec rendu page %s", i + 1)
            continue