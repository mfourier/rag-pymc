"""AST-backed parser for versioned Python repository source."""

import ast
from hashlib import sha256
from typing import Literal

from rag_pymc.domain import Document, SourceManifest, SourceType
from rag_pymc.ingestion.errors import DocumentParseError
from rag_pymc.parsing.models import ParsedCodeBlock, ParsedRepositoryDocument

PythonSymbol = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


class PythonRepositoryParser:
    """Select one public symbol and preserve its implementation structure."""

    version = "python-repository-ast-v1"

    def parse(self, source: bytes, manifest: SourceManifest) -> ParsedRepositoryDocument:
        """Parse the expected top-level symbol from verified Python source."""
        if manifest.source_type is not SourceType.REPOSITORY_CODE:
            msg = f"PythonRepositoryParser does not support {manifest.source_type}"
            raise DocumentParseError(msg)
        if manifest.media_type != "text/x-python":
            msg = f"expected text/x-python, got {manifest.media_type}"
            raise DocumentParseError(msg)
        if manifest.expected_api_symbol is None or manifest.source_path is None:
            raise DocumentParseError("repository manifest is missing symbol provenance")

        try:
            text = source.decode("utf-8")
        except UnicodeDecodeError as error:
            raise DocumentParseError("repository source is not valid UTF-8") from error
        try:
            module = ast.parse(text, filename=manifest.source_path)
        except SyntaxError as error:
            msg = f"repository source is not valid Python: {manifest.source_path}"
            raise DocumentParseError(msg) from error

        python_name = manifest.expected_api_symbol.rsplit(".", maxsplit=1)[-1]
        candidates = [
            node
            for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == python_name
        ]
        implementations = [node for node in candidates if not self._is_overload(node)]
        if not implementations:
            msg = (
                f"top-level implementation for {manifest.expected_api_symbol} "
                f"was not found in {manifest.source_path}"
            )
            raise DocumentParseError(msg)
        symbol = implementations[-1]

        symbol_source = ast.get_source_segment(text, symbol)
        if symbol_source is None or symbol.end_lineno is None:
            raise DocumentParseError("Python AST did not preserve the expected source span")

        lines = text.splitlines()
        signature = self._signature(lines, symbol)
        docstring = ast.get_docstring(symbol, clean=True)
        docstring_summary = self._docstring_summary(docstring)
        body = self._without_docstring(symbol.body)
        blocks = tuple(self._code_block(text, statement) for statement in body)
        symbol_kind = self._symbol_kind(symbol)

        normalized_content = "\n".join(
            (
                f"# {manifest.expected_api_symbol}",
                f"Source path: {manifest.source_path}",
                f"Symbol lines: {symbol.lineno}-{symbol.end_lineno}",
                "",
                "```python",
                symbol_source,
                "```",
            )
        )
        content_hash = sha256(normalized_content.encode("utf-8")).hexdigest()
        document = Document(
            document_id=f"doc_{content_hash[:20]}",
            library=manifest.library,
            library_version=manifest.library_version,
            source_type=manifest.source_type,
            source_url=manifest.source_url,
            title=manifest.expected_api_symbol,
            content=normalized_content,
            content_hash=content_hash,
            fetched_at=manifest.downloaded_at,
            source_commit=manifest.source_commit,
            license_name=manifest.license_name,
            license_url=manifest.license_url,
            parser_version=self.version,
        )
        return ParsedRepositoryDocument(
            document=document,
            api_symbol=manifest.expected_api_symbol,
            source_path=manifest.source_path,
            symbol_kind=symbol_kind,
            signature=signature,
            docstring_summary=docstring_summary,
            start_line=symbol.lineno,
            end_line=symbol.end_lineno,
            blocks=blocks,
        )

    @staticmethod
    def _is_overload(symbol: PythonSymbol) -> bool:
        if isinstance(symbol, ast.ClassDef):
            return False
        return any(
            (isinstance(decorator, ast.Name) and decorator.id == "overload")
            or (isinstance(decorator, ast.Attribute) and decorator.attr == "overload")
            for decorator in symbol.decorator_list
        )

    @staticmethod
    def _signature(lines: list[str], symbol: PythonSymbol) -> str:
        first_body_line = symbol.body[0].lineno if symbol.body else symbol.lineno
        if first_body_line > symbol.lineno:
            signature = "\n".join(lines[symbol.lineno - 1 : first_body_line - 1]).strip()
        else:
            first_statement = symbol.body[0] if symbol.body else symbol
            signature = lines[symbol.lineno - 1][: first_statement.col_offset].strip()
        if not signature:
            raise DocumentParseError("Python symbol signature could not be isolated")
        return signature

    @staticmethod
    def _docstring_summary(docstring: str | None) -> str | None:
        if docstring is None:
            return None
        return docstring.split("\n\n", maxsplit=1)[0].strip()

    @staticmethod
    def _without_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
        if not body:
            return []
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            return body[1:]
        return body

    @staticmethod
    def _code_block(text: str, statement: ast.stmt) -> ParsedCodeBlock:
        content = ast.get_source_segment(text, statement)
        if content is None or statement.end_lineno is None:
            raise DocumentParseError("Python AST statement has no source span")
        return ParsedCodeBlock(
            content=content,
            start_line=statement.lineno,
            end_line=statement.end_lineno,
        )

    @staticmethod
    def _symbol_kind(
        symbol: PythonSymbol,
    ) -> Literal["function", "async_function", "class"]:
        if isinstance(symbol, ast.AsyncFunctionDef):
            return "async_function"
        if isinstance(symbol, ast.FunctionDef):
            return "function"
        return "class"
