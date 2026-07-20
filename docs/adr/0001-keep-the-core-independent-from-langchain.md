# ADR-0001: Keep the core independent from LangChain

- Status: Accepted
- Date: 2026-07-19

## Context

The project must make retrieval behavior observable and experimentally comparable. Early
work includes structure-aware chunking, sparse retrieval, metadata filters, ranking metrics,
and citation provenance. Hiding these decisions behind an orchestration framework would make
it harder to isolate variables, explain failures, and teach the underlying information
retrieval concepts.

LangChain and similar frameworks can accelerate provider integration, but their abstractions
and defaults may change independently of this project's domain. Domain contracts should not
encode framework-specific document, message, retriever, or callback types.

## Decision

The initial architecture will implement small project-owned interfaces and domain models for
parsing, chunking, indexing, retrieval, reranking, context construction, generation, and
evaluation as each capability becomes necessary.

LangChain and LlamaIndex will not be runtime dependencies during the first retrieval phases.
They may be introduced later as infrastructure adapters or experimental comparison systems.
Adapters must translate at the boundary and must not leak framework types into the domain.

## Alternatives considered

### Use LangChain as the primary orchestration layer

This would provide ready-made integrations and reduce initial adapter code. It would also
couple experiments to framework semantics, obscure important retrieval operations, and make
upgrades a source of unrelated behavioral change.

### Own the core contracts and add adapters later

This requires implementing a small amount of explicit orchestration. In return, ranking,
filtering, provenance, and evaluation remain inspectable and can be tested without external
services. This alternative was selected.

## Consequences

- Core tests remain deterministic and independent of external APIs.
- Retrieval experiments can compare algorithms through stable project-owned contracts.
- Framework integrations require explicit adapters.
- The project must avoid recreating broad framework features that are outside its learning
  and evaluation goals.
- This decision can be revisited after the sparse, dense, and hybrid baselines are measured.
