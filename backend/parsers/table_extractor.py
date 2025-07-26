"""Table extraction utilities.

This module provides functions to extract tabular data from PDFs.  It
uses the Camelot library for PDF table detection and extraction.  Each
extracted table is annotated with a ``table_type`` based on simple
keyword heuristics, making it easier for downstream code (or an AI
model) to identify what kind of information the table contains.

If Camelot is not installed, an ImportError will be raised when
attempting to call the extraction function.  Install Camelot via
``pip install camelot-py`` and ensure that dependencies such as
ghostscript are available on your system.  See Camelot's
documentation for platform-specific installation notes.
"""

from __future__ import annotations

from typing import Any, List, Dict
import logging

logger = logging.getLogger(__name__)

try:
    import camelot  # type: ignore
except ImportError as exc:
    camelot = None  # type: ignore
    logger.debug("Camelot library not available: %s", exc)


def infer_table_type(rows: List[List[str]]) -> str:
    """Infer the type of a table based on its contents.

    The function scans the concatenated text of all cells for keywords
    that indicate what the table represents.  This is a simple
    heuristic and can be extended to handle additional table types.

    Args:
        rows: The raw table data as a list of lists of strings.

    Returns:
        A lowercase snake-case string representing the inferred type,
        e.g. ``"mechanical_characteristics"`` or ``"packaging_configuration"``.
    """
    text = " ".join(" ".join(cell.lower() for cell in row) for row in rows)
    if "mechanical characteristics" in text or "cell type" in text:
        return "mechanical_characteristics"
    if "packaging configuration" in text or "pallet" in text:
        return "packaging_configuration"
    if "electrical" in text and ("performance" in text or "parameter" in text):
        return "electrical_parameters"
    if "absolute" in text and "rating" in text:
        return "absolute_maximum_ratings"
    return "unknown"


def extract_tables(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract and classify tables from a PDF using Camelot.

    Args:
        pdf_path: Absolute path to the PDF file.

    Returns:
        A list of dictionaries.  Each dictionary has two keys:
            ``"table_type"``: a string describing the inferred type (see
            :func:`infer_table_type`).
            ``"rows"``: a list of lists of strings representing the
            table's rows and columns.
    Raises:
        ImportError: If Camelot is not installed.
    """
    if camelot is None:
        raise ImportError(
            "Camelot is required for table extraction. Please install it via 'pip install camelot-py'"
        )

    try:
        tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
    except Exception as exc:
        logger.warning("Failed to extract tables with Camelot: %s", exc)
        return []

    parsed_tables: List[Dict[str, Any]] = []
    for table in tables:
        df = table.df
        rows = [[str(cell) if cell is not None else "" for cell in row] for row in df.values.tolist()]
        table_type = infer_table_type(rows)
        parsed_tables.append({"table_type": table_type, "rows": rows})
    return parsed_tables
