# Review Context: Document Writing Principles

**Purpose.** Protect the team's documentation from becoming unreadable cognitive burdens. Every new or modified document must adhere to a clear Intro-Body-Conclusion structure (Principle 1) and must progressively disclose information from the easiest, macro-level concepts down to the most complex, micro-level details (Principle 2). This ensures readers with varying levels of domain context can grasp the intent without getting lost in the weeds.

## Scope

Evaluate only document structures, sections, and paragraphs that are **added or modified** in the diff. Check if the flow of information logically builds from context to detail. Do not surface findings about sections in files the diff does not touch, unless the new changes invalidate the overarching structure of the document.

## Checkpoints

### 1. Clear Tripartite Structure

Every document must be explicitly or logically divided into an Introduction (Context/Goal), a Body (Approach/Details), and a Conclusion (closing — e.g. recap, validation pointer, or open items). **A document that jumps straight into technical implementation without explaining *why* it is being written is always Critical.** The lack of a proper introduction is what misleads stakeholders and reviewers. The exact contents of the Conclusion (recap, validation, open questions, or a combination) are left to each document type's own conventions; this checkpoint only requires that a Conclusion phase exists and is not abruptly omitted.

```markdown
<!-- BAD: Jumps straight into implementation details with no intro (Critical) -->
# User Profile Refactoring
## Proposed Approach
We will change the `User` class to use a builder pattern.
The `email` field will be moved to...

<!-- GOOD: Clearly sets the context before diving in -->
# User Profile Refactoring
## Context & Goal
The current `User` class is too rigid, causing 30% of build failures. We aim to decouple it.
## Proposed Approach
We will change the `User` class to use a builder pattern.
```

### 2. Big Picture First

According to Principle 2, a document should never force the reader to infer the system's architecture from a pile of low-level specs. The easy, high-level concept must always precede the complex details.

```markdown
<!-- BAD: Explains the hard, micro-details before the macro-concept (Critical) -->
### Architecture
- `Redis` will use a TTL of 300s.
- The `UpdateEvent` payload will include `timestamp` and `id`.
- We are moving from monolithic DB to a pub/sub event model.

<!-- GOOD: Big picture -> Detail -->
### Architecture
**[High-level]** We are moving from a monolithic DB to a pub/sub event model using Redis.
**[Detail]**
- The `UpdateEvent` payload will include `timestamp` and `id`.
- `Redis` will use a TTL of 300s.
```

### 3. Progressive Disclosure within Sections

Principle 2 applies not just to the document as a whole, but to individual sub-sections. Even within a technical section like "Alternatives Considered," the primary takeaway should be stated in simple terms before diving into the complex trade-off analysis.

```markdown
<!-- BAD: Pure noise of complex metrics without an upfront summary -->
### Alternatives Considered: gRPC
Serialization takes 12ms. Handshake overhead is 3ms. Given our current network topology, the MTU sizes will cause fragmentation. Therefore, we rejected it.

<!-- GOOD: Easy conclusion first, complex rationale follows -->
### Alternatives Considered: gRPC
**[Summary]** Rejected due to high network fragmentation overhead.
**[Detail]** Serialization takes 12ms, and handshake overhead is 3ms. Given our current network topology...
```

## Priority hints

- **Critical** — Document completely lacks an Introduction (starts directly with code/specs) or Conclusion. The flow is inverted, forcing the reader to read complex API specs or DB schemas before explaining what the feature actually does.
- **Important** — The overall Intro-Body-Conclusion structure exists, but within a specific section, the author dives into difficult details before providing a high-level summary (violating Principle 2 at the micro-level).
- **Suggestion** — The structure is correct, but the "Big Picture" summary is written using overly complex jargon, making it read like a "Detail" section rather than an easy, accessible overview.
