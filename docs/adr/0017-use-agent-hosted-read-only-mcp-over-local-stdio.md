# ADR-0017: Use agent-hosted read-only MCP over local STDIO

- Status: Accepted
- Date: 2026-08-02

## Context

`rag-pymc` owns a deterministic evidence pipeline but does not yet authorize answer generation.
Users already run authenticated Codex CLI or Claude Code sessions, so a first integration does not
need another chat UI, a provider API client, local model weights, or credential storage. It needs a
narrow way for those external hosts to inspect the evidence controlled by this repository.

RAG and MCP solve different problems. RAG owns corpus selection, provenance, BM25 retrieval,
context construction, sufficiency, grounding, citations, and validation. MCP is only a protocol by
which an external host can call those capabilities. MCP does not select evidence, prove grounding,
force a host to call a tool, or constrain the prose the host ultimately emits.

Treating Codex and Claude compatibility as multi-provider routing would conflate an interoperable
tool boundary with provider selection. The project has no basis for choosing between generators,
silently failing over, comparing costs, or merging provider behavior. When generation evaluation
becomes valid, Codex and Claude must be treated as separate generators.

## Decision

Adopt an **agent-hosted MCP MVP** as the first integration surface:

1. Run one local MCP server over STDIO with `rag-pymc serve-mcp`.
2. Treat Codex CLI and Claude Code as external MCP clients and conversational hosts.
3. Leave installation, authentication, plans, quotas, and credential storage entirely with each
   host CLI.
4. Never read, copy, import, log, or modify `~/.codex/auth.json`, Claude credentials, OAuth tokens,
   API keys, or provider configuration.
5. Keep OpenAI and Anthropic APIs, SDKs, and credentials out of the domain and application core.
6. Do not execute or download an LLM locally.
7. Do not implement provider selection, fallback, or automatic routing. Multi-client compatibility
   means both hosts can call the same provider-neutral evidence tools, not that `rag-pymc` chooses a
   host.
8. Expose only deterministic, read-only evidence operations over the controlled PyMC corpus.
9. Accept bounded query text, explicit supported versions, numeric limits, and opaque authorized
   chunk IDs. Do not accept filesystem paths, arbitrary URLs, shell commands, or code.
10. Reserve stdout exclusively for MCP protocol frames. Diagnostics and server logs go to stderr
    and must not include secrets or unnecessary local paths.
11. Keep the domain independent of MCP, Typer, Codex, Claude, subprocesses, and agent frameworks.
    The MCP adapter calls project-owned application services and translates values at the edge.
12. Defer a standalone web UI, direct provider APIs, and CLI generation adapters. A later local UI
    may use `CodexCliGenerator` through `codex exec` or `ClaudeCodeCliGenerator` through
    `claude -p`, but only after sufficiency and answer-validation gates are complete.

The first tools search PyMC evidence, inspect bounded PyMC context, and retrieve a chunk already in
the authorized corpus. They expose the active conservative assessment and never invoke
`AnswerGenerator`. There is no public `ask` command.

The transport uses the official Python SDK pinned exactly at `mcp==2.0.0`. Its low-level server
API adapts the project registry so strict validation, deterministic ordering, error sanitization,
and output contracts remain project-owned rather than inherited from permissive SDK defaults.

The integration boundaries are deliberately distinct:

```text
agent-hosted MCP MVP
        != CLI generation adapter
        != standalone local interface
        != direct provider API
```

## Security and provenance invariants

- The server is local, read-only, and network-free at runtime.
- The server can open only its operator-configured, project-owned corpus snapshot and provenance
  freeze; model-supplied paths are not part of any tool schema.
- `get_pymc_chunk` resolves only an ID present in that already validated corpus.
- Every startup revalidates the atomic corpus against the provenance-complete v2 freeze, including
  document/chunk identities, release, commit, official URLs, source type, and hashes.
- Tool inputs use strict schemas with bounded lengths and counts; extra fields fail closed.
- Tool output is structured, schema-versioned, deterministically ordered, and explicitly says that
  generation remains prohibited.
- Errors crossing the protocol boundary use bounded reason codes and omit raw exception text,
  credentials, query contents, and local paths.
- No tool offers generic filesystem access, network access, subprocess execution, Python
  execution, ingestion, mutation, configuration changes, or credential operations.

## Alternatives considered

### Build a standalone local chat first

Rejected for the first integration because it would add conversation state, process management,
streaming, UX, and provider-specific CLI adapters before the evidence boundary can authorize an
answer. The user's existing host already supplies the conversational surface.

### Call OpenAI or Anthropic APIs directly

Rejected because it would duplicate host authentication, introduce secrets and billing concerns,
and couple the project to provider SDKs before generation is evaluable.

### Implement JSON-RPC manually

Rejected. STDIO framing, lifecycle, capability negotiation, errors, and schema behavior should use
the official MCP SDK with an exact dependency pin. Project-owned code remains independently
testable so the transport dependency stays at the edge.

### Let MCP replace the RAG layer

Rejected because protocol interoperability cannot enforce corpus authority, retrieval quality,
sufficiency, citation validity, or grounded generation.

## Consequences

- Users converse in their chosen authenticated host while `rag-pymc` remains credential-free.
- One evidence implementation can serve multiple MCP clients without provider coupling.
- The first useful slice is inspectable and safe even while all answers remain unauthorized.
- The official MCP SDK becomes a presentation dependency and brings a broader transitive HTTP,
  ASGI, authentication, and telemetry stack than this STDIO-only slice actively uses. Exact
  pinning and lockfile review contain that supply-chain cost independently from PyMC scientific
  dependencies.
- The local Conda Python 3.13 build needs a bounded scheduler tick for reliable AnyIO STDIO file
  callbacks. This costs at most 20 idle wake-ups per second and remains isolated in the transport
  adapter; it neither parses nor changes protocol frames.
- MCP cannot guarantee that Codex or Claude invokes the tools, includes every limitation, cites the
  evidence, or makes its final message match a future validated draft. Those properties require
  host-specific evaluation and, later, `prepare_pymc_answer`/`validate_pymc_answer` gates.
- Live host smoke tests remain explicit opt-in checks because they can consume network, tokens, and
  plan quota. Offline tests own the default CI contract.
