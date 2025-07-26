"""Parsers package for datasheet processing.

This package contains helper modules for extracting structured data from
PDFs, such as tables. Having a separate module for table extraction
allows us to swap out different libraries (e.g. Camelot, Tabula) without
cluttering the main file_service logic. Additional parsers (e.g.
OCR, form recognition) can be added here in future.
"""

__all__ = ["table_extractor"]

