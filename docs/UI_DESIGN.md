# Analytical workspace direction

## Direction contract

THESIS: A statistical atlas makes one historical corpus inspectable through
counts, uncertainty and the same held-out comparison. Familiar navigation and
forms keep the task recognizable.

OWN-WORLD: Atlas-blue rail, pale-blue workspace, white surfaces, teal ham, burnt
orange spam, system UI sans and aligned tabular numbers. Classroom lighting
calls for a light reading surface.

STORY: Check readiness, choose all/train/test, inspect the corpus, reason about
one word, test association, classify transient text, compare held-out errors.

FIRST VIEWPORT: Navigation at left, readiness and scope above a wide work area,
title then corpus class balance and service readiness. Analysis actions follow
the evidence. Mobile navigation stays above the same content.

FORM: Candidate 5, statistical atlas; seed:a788c9d5983031a7. Considered families:
laboratory notes, postal ephemera, mathematics texts, campus wayfinding,
statistical atlases, lecture boards and punch-card records. The Operate limit
preserves ordinary controls/layout. Catalog exposure sheets, Metro tiles and
airline coupons/timetables add neither audience identification nor task clarity;
their discipline reinforces explicit state labels and aligned compact tables.
No catalog clothing is borrowed. Selected autonomously as authorized; no human
visual preference or signoff is inferred.

FINISH: unreviewed and undocumented is unfinished; this build ends with rendered
desktop/mobile inspection, working states and durable design documentation.

## Implementation decisions

- A small History API router covers six static routes and browser back/forward
  without a new dependency. Modified link clicks retain native behavior.
- The client fixes the loopback origin and allowlists endpoints. Email bodies
  use POST, never URL parameters, storage or a history feature.
- Request signatures and AbortController hide old data when filters change and
  prevent late responses replacing a new selection. Retry retains parameters.
