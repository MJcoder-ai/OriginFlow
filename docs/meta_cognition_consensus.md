# Meta‑Cognition & Consensus (Phase 15)

OriginFlow introduces a meta‑cognitive layer and a consensus mechanism to
improve agent reliability and user experience.  These features empower
agents to introspect their reasoning, ask clarifying questions when
information is missing, and reconcile multiple competing designs.

## Meta‑Cognition Agent

The `MetaCognitionAgent` is invoked whenever a design task is blocked due to
incomplete or ambiguous inputs.  It analyses the context (such as a list
of missing fields or a reason string) and returns a design card with:

- **questions** – one per missing item or a general question about the
  issue, prompting the user to provide additional information.
- **recommended_actions** – guidance when no specific questions can be
  formulated, encouraging the user to review and complete the design
  requirements or attach missing datasheets.

The agent returns an ADPF‑compliant envelope with status `blocked` and
no patch, signalling that the workflow should pause until the user
responds.

## Consensus Agent

When multiple domain agents produce alternative designs for the same task,
the `ConsensusAgent` aggregates these candidate outputs and selects a
single consensus design.  It examines each candidate’s design card for a
`confidence` field (defaulting to 0.5 if absent) and picks the one with
the highest confidence.  The consensus decision is summarised in a
design card that includes the selected card and patch and explains how
many candidates were considered.

Future iterations may implement more advanced consensus algorithms,
including weighted voting, intersection of graph patches, or user‑driven
choice.

## Usage

- The planner or orchestrator should call `MetaCognitionAgent` whenever an
  agent returns `status='blocked'` due to missing context.  Pass a
  ``missing`` list or ``reason`` string to generate appropriate
  questions.
- After multiple agents complete similar tasks, call `ConsensusAgent`
  with a ``candidates`` list of ADPF envelopes to select a final
  design.  The agent returns a single envelope ready for application.

These mechanisms enhance the transparency and reliability of OriginFlow by
ensuring agents surface their uncertainty, solicit necessary input from
users, and converge on a unified design when multiple opinions are
available.

## Developer Guidance

To implement your own meta‑cognitive or consensus mechanisms—or to extend
the existing agents—refer to the [developer onboarding guide](developer_guide.md).
The guide provides a walkthrough on creating new agents, integrating them
into the task registry and documenting their behaviour.
