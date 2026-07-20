"""Parser for Sphinx-generated API reference pages."""

from collections.abc import Iterable
from hashlib import sha256

from bs4 import BeautifulSoup
from bs4.element import NavigableString, PageElement, Tag

from rag_pymc.domain import Document, SourceManifest, SourceType
from rag_pymc.ingestion.errors import DocumentParseError
from rag_pymc.parsing.models import ParsedApiDocument, ParsedSection


class SphinxApiParser:
    """Parse one Sphinx Python API object into semantic sections."""

    version = "sphinx-api-v1"

    def parse(self, source: bytes, manifest: SourceManifest) -> ParsedApiDocument:
        """Parse an API page while preserving code and source provenance."""
        if manifest.source_type is not SourceType.API_REFERENCE:
            msg = f"SphinxApiParser does not support {manifest.source_type}"
            raise DocumentParseError(msg)
        if manifest.media_type != "text/html":
            msg = f"expected text/html, got {manifest.media_type}"
            raise DocumentParseError(msg)

        soup = BeautifulSoup(source, "html.parser")
        signature_node = soup.select_one("article.bd-article dt.sig[id]")
        if not isinstance(signature_node, Tag):
            raise DocumentParseError("Sphinx API signature was not found")

        symbol_value = signature_node.get("id")
        if not isinstance(symbol_value, str):
            raise DocumentParseError("Sphinx API signature has no string identifier")
        expected_symbol = manifest.expected_api_symbol
        if expected_symbol is None or symbol_value != expected_symbol:
            msg = f"expected API symbol {expected_symbol}, found {symbol_value}"
            raise DocumentParseError(msg)

        details = signature_node.find_next_sibling("dd")
        if not isinstance(details, Tag):
            raise DocumentParseError("Sphinx API details were not found")

        signature = self._signature_text(signature_node)
        sections = self._extract_sections(details)
        if not sections:
            raise DocumentParseError(f"no semantic sections found for {symbol_value}")

        normalized_content = self._document_content(symbol_value, signature, sections)
        content_hash = sha256(normalized_content.encode("utf-8")).hexdigest()
        document = Document(
            document_id=f"doc_{content_hash[:20]}",
            library=manifest.library,
            library_version=manifest.library_version,
            source_type=manifest.source_type,
            source_url=manifest.source_url,
            title=symbol_value,
            content=normalized_content,
            content_hash=content_hash,
            fetched_at=manifest.downloaded_at,
            source_commit=manifest.source_commit,
            license_name=manifest.license_name,
            license_url=manifest.license_url,
            parser_version=self.version,
        )
        return ParsedApiDocument(
            document=document,
            api_symbol=symbol_value,
            signature=signature,
            sections=tuple(sections),
        )

    def _extract_sections(self, details: Tag) -> list[ParsedSection]:
        sections: list[ParsedSection] = []
        field_list = details.find("dl", class_="field-list", recursive=False)

        description_nodes: list[PageElement] = []
        for child in details.children:
            if child is field_list or self._is_rubric(child):
                break
            description_nodes.append(child)

        description = self._render_blocks(description_nodes)
        if description:
            sections.append(
                ParsedSection(
                    name="Overview",
                    content=description,
                    contains_code=self._contains_code(description_nodes),
                )
            )

        if isinstance(field_list, Tag):
            sections.extend(self._field_sections(field_list))
        sections.extend(self._rubric_sections(details))
        return sections

    def _field_sections(self, field_list: Tag) -> list[ParsedSection]:
        sections: list[ParsedSection] = []
        for heading in field_list.find_all("dt", recursive=False):
            body = heading.find_next_sibling("dd")
            if not isinstance(body, Tag):
                continue
            name = self._inline_text(heading).removesuffix(":")
            content = self._render_definition_body(body)
            if name and content:
                sections.append(
                    ParsedSection(
                        name=name,
                        content=content,
                        contains_code=body.find("pre") is not None,
                    )
                )
        return sections

    def _rubric_sections(self, details: Tag) -> list[ParsedSection]:
        sections: list[ParsedSection] = []
        for rubric in details.find_all("p", class_="rubric", recursive=False):
            nodes: list[PageElement] = []
            for sibling in rubric.next_siblings:
                if self._is_rubric(sibling):
                    break
                nodes.append(sibling)
            content = self._render_blocks(nodes)
            if content:
                sections.append(
                    ParsedSection(
                        name=self._inline_text(rubric),
                        content=content,
                        contains_code=self._contains_code(nodes),
                    )
                )
        return sections

    def _render_definition_body(self, body: Tag) -> str:
        definition_list = body.find("dl", recursive=False)
        if isinstance(definition_list, Tag):
            return self._render_definition_list(definition_list)
        return self._render_blocks(body.children)

    def _render_definition_list(self, definition_list: Tag) -> str:
        entries: list[str] = []
        for term in definition_list.find_all("dt", recursive=False):
            description = term.find_next_sibling("dd")
            if not isinstance(description, Tag):
                continue
            heading = self._inline_text(term)
            body = self._render_blocks(description.children)
            if heading and body:
                entries.append(f"{heading}\n{body}")
        return "\n\n".join(entries)

    def _render_blocks(self, nodes: Iterable[PageElement]) -> str:
        parts: list[str] = []
        for node in nodes:
            if isinstance(node, NavigableString):
                text = " ".join(str(node).split())
                if text:
                    parts.append(text)
            elif isinstance(node, Tag):
                rendered = self._render_block(node)
                if rendered:
                    parts.append(rendered)
        return "\n\n".join(parts)

    def _render_block(self, element: Tag) -> str:
        if element.name == "pre":
            code = element.get_text("", strip=False).strip("\n")
            fence = "`" * 3
            return f"{fence}python\n{code}\n{fence}"
        if element.name in {"p", "dt"}:
            return self._inline_text(element)
        if element.name in {"ul", "ol"}:
            items: list[str] = []
            for item in element.find_all("li", recursive=False):
                rendered = self._render_blocks(item.children) or self._inline_text(item)
                if rendered:
                    items.append(f"- {rendered}")
            return "\n".join(items)
        if element.name == "dl":
            return self._render_definition_list(element)

        nested = self._render_blocks(element.children)
        return nested or self._inline_text(element)

    @staticmethod
    def _inline_text(element: Tag) -> str:
        fragment = BeautifulSoup(str(element), "html.parser")
        for code in fragment.find_all("code"):
            value = code.get_text("", strip=True)
            marker = "`"
            code.replace_with(fragment.new_string(f"{marker}{value}{marker}"))
        return " ".join(fragment.get_text(" ", strip=True).split())

    @staticmethod
    def _signature_text(signature_node: Tag) -> str:
        fragment = BeautifulSoup(str(signature_node), "html.parser")
        for link in fragment.find_all("a"):
            link.decompose()
        return "".join(fragment.stripped_strings)

    @staticmethod
    def _contains_code(nodes: Iterable[PageElement]) -> bool:
        return any(
            isinstance(node, Tag) and (node.name == "pre" or node.find("pre") is not None)
            for node in nodes
        )

    @staticmethod
    def _is_rubric(node: PageElement) -> bool:
        if not isinstance(node, Tag) or node.name != "p":
            return False
        classes = node.get("class")
        return classes is not None and "rubric" in classes

    @staticmethod
    def _document_content(
        api_symbol: str,
        signature: str,
        sections: list[ParsedSection],
    ) -> str:
        marker = "`"
        parts = [f"# {api_symbol}", f"Signature: {marker}{signature}{marker}"]
        parts.extend(f"## {section.name}\n{section.content}" for section in sections)
        return "\n\n".join(parts)
