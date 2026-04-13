from __future__ import annotations

import re

import fitz

from docustruct_ai.core.types import BoundingBox, ParsedDocument, ParsedPage, Region, TableRegion
from docustruct_ai.models import Document
from docustruct_ai.parsing.interfaces import ParsingBackend
from docustruct_ai.utils.normalization import normalize_whitespace


class HeuristicParser(ParsingBackend):
    engine_name = "heuristic-layout-parser"

    def parse(self, document: Document) -> ParsedDocument:
        parsed_pages: list[ParsedPage] = []
        source = fitz.open(document.source_path)
        try:
            for index, page in enumerate(source):
                blocks = page.get_text("blocks")
                regions: list[Region] = []
                tables: list[TableRegion] = []
                kv_regions: list[Region] = []
                reading_order: list[str] = []

                for order, block in enumerate(blocks):
                    x1, y1, x2, y2, text, *_ = block
                    cleaned = normalize_whitespace(text)
                    if not cleaned:
                        continue
                    region = Region(
                        id=f"page-{index + 1}-region-{order}",
                        page=index + 1,
                        kind=self._classify_region(cleaned),
                        bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                        text=cleaned,
                        reading_order=order,
                        metadata={"token_count": len(cleaned.split())},
                    )
                    regions.append(region)
                    reading_order.append(region.id)
                    if ":" in cleaned:
                        kv_regions.append(region)
                    if self._looks_like_table_line(cleaned):
                        tables.append(
                            TableRegion(
                                **region.model_dump(),
                                rows=[[part for part in re.split(r"\s{2,}", cleaned) if part]],
                            )
                        )

                parsed_pages.append(
                    ParsedPage(
                        page_number=index + 1,
                        width=float(page.rect.width),
                        height=float(page.rect.height),
                        regions=regions,
                        tables=tables,
                        key_value_candidates=kv_regions,
                        reading_order=reading_order,
                        metadata={"block_count": len(blocks)},
                    )
                )
        finally:
            source.close()

        return ParsedDocument(
            document_id=document.id,
            pages=parsed_pages,
            metadata={"engine_name": self.engine_name, "page_count": len(parsed_pages)},
        )

    def _classify_region(self, text: str) -> str:
        lowered = text.lower()
        if ":" in text:
            return "key_value"
        if self._looks_like_table_line(text):
            return "table_candidate"
        if any(token in lowered for token in ["итого", "total", "subtotal", "ндс", "vat"]):
            return "summary"
        return "text"

    def _looks_like_table_line(self, text: str) -> bool:
        has_many_spaces = bool(re.search(r"\s{2,}", text))
        has_amount = bool(re.search(r"\d+[.,]\d{2}", text))
        return has_many_spaces and has_amount
