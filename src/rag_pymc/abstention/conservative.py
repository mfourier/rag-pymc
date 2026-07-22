"""Fail-closed evidence assessment without a calibrated criterion."""

from rag_pymc.domain import ConstructedContext, EvidenceAssessment, EvidenceSufficiency


class ConservativeAbstentionPolicy:
    """Abstain unless a future calibrated policy establishes sufficiency."""

    name = "conservative-no-threshold-v1"

    def assess(self, context: ConstructedContext) -> EvidenceAssessment:
        """Classify empty context and leave nonempty sufficiency unestablished."""
        included = context.included_chunk_ids
        omitted = context.omitted_chunk_ids
        reason_codes: tuple[str, ...]

        if not included:
            sufficiency = EvidenceSufficiency.INSUFFICIENT
            reason_codes = (
                ("budget_excluded_all_evidence",) if omitted else ("no_retrieved_evidence",)
            )
        else:
            sufficiency = EvidenceSufficiency.NOT_ASSESSED
            reason_codes = ("no_calibrated_criterion",)
            if omitted:
                reason_codes = tuple(sorted(("budget_omitted_evidence", "no_calibrated_criterion")))

        return EvidenceAssessment(
            policy_version=self.name,
            sufficiency=sufficiency,
            should_abstain=True,
            reason_codes=reason_codes,
            context_chunk_ids=included,
            omitted_chunk_ids=omitted,
        )
