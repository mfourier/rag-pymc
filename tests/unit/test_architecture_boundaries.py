import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_CORE_IMPORTS = {
    "anthropic",
    "claude",
    "langchain",
    "llama_index",
    "mcp",
    "openai",
    "subprocess",
    "typer",
}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.partition(".")[0])
    return roots


def test_domain_does_not_import_mcp_cli_providers_or_agent_frameworks() -> None:
    domain_files = sorted((PROJECT_ROOT / "src/rag_pymc/domain").rglob("*.py"))

    assert domain_files
    for path in domain_files:
        assert imported_roots(path).isdisjoint(FORBIDDEN_CORE_IMPORTS), path


def test_application_layer_does_not_import_mcp_or_generation_hosts() -> None:
    application_files = sorted((PROJECT_ROOT / "src/rag_pymc/application").rglob("*.py"))

    assert application_files
    for path in application_files:
        assert imported_roots(path).isdisjoint(FORBIDDEN_CORE_IMPORTS), path
