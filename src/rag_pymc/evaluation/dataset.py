"""JSONL loading for manually curated retrieval datasets."""

from pathlib import Path

from pydantic import ValidationError

from rag_pymc.evaluation.errors import EvaluationDatasetError
from rag_pymc.evaluation.models import EvaluationQuery


def load_evaluation_queries(path: Path) -> tuple[EvaluationQuery, ...]:
    """Load and validate unique evaluation queries from JSON Lines."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        msg = f"unable to read evaluation dataset: {path}"
        raise EvaluationDatasetError(msg) from error

    queries: list[EvaluationQuery] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            query = EvaluationQuery.model_validate_json(line)
        except ValidationError as error:
            msg = f"invalid evaluation query at {path}:{line_number}"
            raise EvaluationDatasetError(msg) from error
        if query.question_id in seen_ids:
            msg = f"duplicate question_id at {path}:{line_number}: {query.question_id}"
            raise EvaluationDatasetError(msg)
        seen_ids.add(query.question_id)
        queries.append(query)

    if not queries:
        msg = f"evaluation dataset is empty: {path}"
        raise EvaluationDatasetError(msg)
    return tuple(queries)
