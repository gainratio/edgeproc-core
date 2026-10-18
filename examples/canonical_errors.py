"""End-to-end demo: turn messy real-world failures into one stable error code.

The problem: the same outage arrives in a dozen shapes. An HTTP 402, a thrown
`TimeoutError`, a browser's "Failed to fetch" — each one is a different object,
and every layer of an app ends up re-writing the same fragile `if` ladder to
decide what to tell the user.

`edgeproc_core.errors` does that once. You register a **catalog** of stable
codes (or reuse the bundled `starter_pack` of 18 universal ones), then:

- `classify(raw)`  — any raw failure  -> a stable code such as `net.unreachable`
- `describe(code)` — a code -> human text, through your own i18n if you have one
- `to_problem_details(code).to_dict()` -> the RFC 9457 JSON shape for an API

The codes are identical to the TypeScript `@gainratio/errors` package, so a
failure keeps the same identity on both sides of a stack.
"""

from __future__ import annotations

from edgeproc_core.errors import define_errors, starter_pack


def main() -> None:
    """Register the starter catalog, classify raw failures, serialize one."""
    registry = define_errors(starter_pack)

    print(f"registered {len(registry.codes)} codes, e.g.:")
    for code in registry.codes[:4]:
        print(f"  {code}")

    # Every one of these is a different Python object; all become stable codes.
    raw_failures: list[tuple[str, object]] = [
        ("an HTTP 402 response", {"status": 402}),
        ("an HTTP 429 response", {"status": 429}),
        ("a browser fetch failure", {"message": "Failed to fetch"}),
        ("a thrown TimeoutError", TimeoutError("deadline exceeded")),
        ("an upstream HTTP 500", {"status_code": 500}),
        ("something nobody predicted", Exception("???")),
    ]

    print("\nclassify — raw failure -> stable code:")
    for label, raw in raw_failures:
        code = registry.classify(raw)
        print(f"  {label:<28} -> {code}")
        print(f"  {'':<28}    {registry.describe(code)}")

    # Serialize one to the RFC 9457 Problem Details shape an API would return.
    problem = registry.to_problem_details("ai.provider.rate_limited")
    print("\nto_problem_details(...).to_dict() — the RFC 9457 wire object:")
    for key, value in sorted(problem.to_dict().items()):
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
