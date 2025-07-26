"""Table extraction utilities.

This module provides functions to extract tabular data from PDFs.  It
uses a multi-step pipeline with Camelot, Tabula and pdfplumber for PDF
table detection and extraction.  Each
extracted table is annotated with a ``table_type`` based on simple
keyword heuristics, making it easier for downstream code (or an AI
model) to identify what kind of information the table contains.

If Camelot is not installed, extraction will skip directly to the next
available method. Tabula support is optional and will be skipped if its
Java dependencies are missing. pdfplumber is used as a lightweight
fallback when other libraries fail to detect tables.
"""

from __future__ import annotations

from typing import Any, List, Dict
import logging

# Note: we will attempt to use multiple extraction engines (Camelot stream,
# Camelot lattice, Tabula and pdfplumber) in sequence.  The first engine that
# produces non-empty tables will be used.  This gives us flexibility
# across a wide variety of PDF layouts.  If none of the engines
# successfully extract any tables, an empty list will be returned.

logger = logging.getLogger(__name__)

try:
    import camelot  # type: ignore
except ImportError as exc:
    camelot = None  # type: ignore
    logger.debug("Camelot library not available: %s", exc)

# Tabula is an optional dependency for table extraction.  We import
# lazily within functions to avoid import errors when it isn't
# installed.  Tabula requires a working Java installation.

def _try_import_tabula():
    try:
        import tabula  # type: ignore
        return tabula
    except Exception as exc:  # noqa: B902
        # We catch a broad Exception here because tabula can raise
        # non-ImportError exceptions if Java is missing or misconfigured.
        logger.debug("Tabula library not available or misconfigured: %s", exc)
        return None


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


def _extract_tables_camelot(pdf_path: str, flavor: str) -> List[Dict[str, Any]]:
    """Extract tables using Camelot with the specified flavor.

    Args:
        pdf_path: Absolute path to the PDF file.
        flavor: Either "stream" or "lattice".

    Returns:
        A list of dicts with keys ``table_type`` and ``rows``.  Returns an
        empty list if Camelot is unavailable or an error occurs.
    """
    if camelot is None:
        return []
    try:
        tables = camelot.read_pdf(pdf_path, pages="all", flavor=flavor)
    except Exception as exc:
        logger.debug("Camelot (%s) failed: %s", flavor, exc)
        return []
    results: List[Dict[str, Any]] = []
    for table in tables:
        try:
            df = table.df
        except Exception:
            continue
        rows = [[str(cell) if cell is not None else "" for cell in row] for row in df.values.tolist()]
        table_type = infer_table_type(rows)
        results.append({"table_type": table_type, "rows": rows})
    return results


def _extract_tables_tabula(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract tables from a PDF using tabula-py.

    This function attempts to read all pages of the PDF using
    tabula.read_pdf(). It returns a list of tables as dicts with
    ``table_type`` and ``rows`` keys.  If Tabula is not installed or
    misconfigured (e.g. missing Java), the function returns an empty list.
    """
    tabula_lib = _try_import_tabula()
    if tabula_lib is None:
        return []
    try:
        dfs = tabula_lib.read_pdf(pdf_path, pages="all", multiple_tables=True, pandas_options={})
    except Exception as exc:
        logger.debug("Tabula failed: %s", exc)
        return []
    results: List[Dict[str, Any]] = []
    for df in dfs:
        try:
            values = df.values.tolist()
        except Exception:
            continue
        rows = [[str(cell) if cell is not None else "" for cell in row] for row in values]
        table_type = infer_table_type(rows)
        results.append({"table_type": table_type, "rows": rows})
    return results


def _extract_tables_pdfplumber(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract tables from a PDF using pdfplumber.

    This is a fallback extractor used if Camelot and Tabula fail to
    detect tables.  pdfplumber can extract simple tables without
    requiring external dependencies like Java or Ghostscript.  Each
    table is returned as a dict with ``table_type`` and ``rows`` keys.

    Returns:
        A list of tables.  If pdfplumber is not installed or no tables
        are found, an empty list is returned.
    """
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        logger.debug("pdfplumber is not installed; skipping pdfplumber extraction")
        return []

    results: List[Dict[str, Any]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                try:
                    tables = page.extract_tables() or []
                except Exception:
                    continue
                for table in tables:
                    if not table:
                        continue
                    rows = [
                        [str(cell) if cell is not None else "" for cell in row]
                        for row in table
                    ]
                    table_type = infer_table_type(rows)
                    results.append({"table_type": table_type, "rows": rows})
    except Exception as exc:
        logger.debug("pdfplumber failed: %s", exc)
        return []
    return results


def _filter_empty_tables(tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove tables that contain no non-empty cells.

    Args:
        tables: A list of table dicts produced by an extractor.

    Returns:
        A filtered list where every table has at least one cell with a
        non-whitespace value.
    """
    filtered: List[Dict[str, Any]] = []
    for tbl in tables:
        rows = tbl.get("rows", [])
        has_content = any(cell.strip() for row in rows for cell in row)
        if has_content:
            filtered.append(tbl)
    return filtered


def extract_tables(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract and classify tables using multiple extraction engines.

    This function attempts to extract tables from a PDF using several
    methods in order of preference.  It will return the first set of
    tables that contains at least one non-empty table.  The order is:
    1. Camelot with the 'stream' flavor.
    2. Camelot with the 'lattice' flavor.
    3. Tabula (Java-based) via the tabula-py wrapper.
    4. pdfplumber for simple heuristic extraction.

    Args:
        pdf_path: Absolute path to the PDF file.

    Returns:
        A list of dictionaries. Each dictionary has two keys:
            ``"table_type"``: the inferred type of the table based on
            simple keyword heuristics.
            ``"rows"``: a list of lists of strings representing the
            table's rows and columns.
        If no tables are found or an error occurs with all extractors,
        an empty list is returned.
    """
    extractors = [
        lambda: _filter_empty_tables(_extract_tables_camelot(pdf_path, "stream")),
        lambda: _filter_empty_tables(_extract_tables_camelot(pdf_path, "lattice")),
        lambda: _filter_empty_tables(_extract_tables_tabula(pdf_path)),
        lambda: _filter_empty_tables(_extract_tables_pdfplumber(pdf_path)),
    ]
    for extractor in extractors:
        try:
            tables = extractor()
            if tables:
                return tables
        except Exception as exc:
            logger.debug("Table extraction error: %s", exc)
            continue
    return []
