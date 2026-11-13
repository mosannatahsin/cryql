# CryQL architecture

CryQL is a standalone package with a blind-introspection engine. It separates configuration,
network safety, protocol parsing, an evidence-preserving `SchemaGraph`,
artifact ingestion, deterministic planning, exports, and orchestration.

Introspection results are marked `CONFIRMED`; artifact and heuristic results
remain `CANDIDATE` until independently verified. Conflicting type or field
evidence is retained and marked `CONTRADICTED` rather than overwritten.

The planner's score is an explainable expected-information-gain/cost heuristic,
not a calibrated probability. Network work is bounded by URL safety checks,
timeouts, retries, rate limiting, response-size limits, and a request budget.

Validation recovery currently reconstructs required arguments, nested object
fields, enum values exposed through suggestions, and required input-object
fields. Abstract-type `possibleTypes` are preserved from introspection; blind
union/interface discovery is intentionally not guessed without explicit
server evidence.
