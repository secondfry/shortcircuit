# Why an owned Short Circuit service would do things differently

Short Circuit is a desktop client. It reads wormhole connections from third-party
mappers (Tripwire, Eve Scout, eventually Pathfinder / eve-whmapper) and runs a
shortest-path search over the combined graph. It is fundamentally a *consumer*
of other people's maps.

That shape constrains what we can do about trust, deduplication, and confidence.
This document tracks the things that would be different — or newly possible — if
Short Circuit were run as an owned web service that is itself a first-class
mapper.

This is a "note to future self" file, not a roadmap. Ideas land here when we
deliberately decide *not* to do something in the client because it only makes
sense server-side.

## Trust and "fake" connections

### Client reality

One bad actor on any upstream mapper can poison the graph for everyone who
consumes that mapper. Short Circuit has no way to mark a connection as fake,
and no way to share that judgment with anyone else. The desktop client sees
only its own user's data (Tripwire chain, Eve Scout feed) and cannot
cross-reference against other users' observations of the same chain.

A "confidence" score computed from "how many of my configured mappers report
this same connection" is not actually meaningful here, because:

- The same user typically consumes only one or two mappers, and those mappers
  often share upstream feeds (public Tripwire already ingests Eve Scout Thera
  data). Two sources reporting the same connection usually means the same
  physical observation traveling through two pipes, not two independent
  confirmations.
- A malicious signature added to one mapper will look identical to a
  legitimate one to every downstream consumer.
- There is no in-game API to "prove" a wormhole exists, so no amount of
  client-side logic can promote an observation into a verified fact.

So we don't compute a confidence score. We just list *which mappers reported
each connection* — that's ground truth the user can act on (and it at least
lets a user notice when a connection is only coming from the one mapper they
don't trust).

### Service-side possibilities

A hosted Short Circuit that is itself a mapper — i.e. runs its own signature
database that corp members post to, and ingests Tripwire / Eve Scout / etc.
as additional feeds — could:

- Let users flag specific connections (by chain, sig, reporter, timestamp) as
  fake. Flags attach to a user identity, so bad flaggers become as filterable
  as bad reporters.
- Compute *reporter* reputation instead of *connection* confidence. A
  signature reported by a historically-accurate character, freshly scanned,
  with a consistent sig ID across updates, is materially different from one
  typed in by a newly-registered account with no prior matches.
- Cross-reference observations of the same physical wormhole across feeds —
  "Tripwire corp A and Eve Scout both reported this signature within 10
  minutes of each other" is a genuine independent-confirmation signal that a
  single-user client cannot observe.
- Propagate "fake" markers across consumers (so one user's discovery that a
  connection is bogus benefits everyone on the service).

None of this is useful in a single-player desktop client. It all requires
shared state, identity, and a corpus of observations the client does not have.

## Deduplication

### Client reality

Dedup is sig-ID-keyed, not just (A, B)-keyed. Two reports refer to the same
wormhole iff at least one sig slot concretely matches (a sig ID uniquely
identifies a wormhole endpoint within a system, so a concrete match on
either side is decisive); two concrete-but-different sig pairs become
parallel edges in the graph. One-sided concrete matches with the other side
disagreeing are treated as scan errors (fresher report wins, warning logged)
rather than split into parallel edges. Placeholder slots are upgraded to
concrete when a report with better data arrives.

This means the router can now handle the rare case of two physically
distinct wormholes connecting the same pair of systems at the same time —
Dijkstra iterates parallel edges per neighbor and picks the cheapest
traversable one, so size/life/mass restrictions on one parallel edge can
route the user via the other.

### Service-side possibilities

A service could keep sig-level history even when the live graph only shows
the current state:

- Store each upstream report as its own row with (sig_from, sig_to,
  reported_at, reported_by_mapper, reported_by_user). Dedup at query time
  rather than at ingestion — useful for retroactive "show me what this chain
  looked like five minutes ago" queries.
- Treat "same sig, different reports" as a genuine cross-mapper confirmation
  signal and surface scan-disagreement cases (same-sig on one side but
  disagreeing on the other) as a user-visible "possible scan error" flag
  rather than just a log warning.
- Let users pick a canonical sig when mappers disagree, and propagate that
  choice.

The client only sees the post-collapse graph — it can't distinguish "two
mappers independently confirming" from "the same report reached us by two
paths", and it can't keep historical state.

## Caching and freshness

Each client instance hits each configured mapper on every refresh. N users
with the same corp Tripwire credentials = N identical API calls. A service
could:

- Maintain a single shared fetch loop per upstream mapper, serve cached data
  to clients, and honor the mapper's rate limits centrally.
- Coalesce concurrent scanning: two corp members scanning the same hole at
  the same time produce one canonical edge rather than a race between two
  writes.
- Serve historical state — "what did this chain look like 10 minutes ago"
  is trivial server-side, impossible client-side.

## Identity and multi-character routing

ESI is currently per-user, implicit-flow, 20-minute sessions. A service
could:

- Maintain persistent refresh tokens for each character.
- Route-plan across characters ("fastest of my alts that is already in
  jump range of X").
- Share "I scanned this" events so the corp sees each other's sigs without
  configuring the same Tripwire.

## What this means for the current codebase

- Don't build a confidence score in the client. It's not meaningful at this
  scope. List source mappers instead.
- Don't build moderation UI ("flag as fake") in the client — it has nowhere
  to send the flag.
- Keep the mapper interface narrow: fetch, report, done. Anything richer
  (reputation, cross-reference, history) belongs server-side and would only
  create dead code here.
