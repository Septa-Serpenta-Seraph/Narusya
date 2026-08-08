---
name: ai-agent-selection-analysis
description: "Apply Hendrycks' selection framework to AI agent scenarios."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [AI-Safety, Agent-Evolution, Selection, Analysis]
---

# AI Agent Selection Analysis

Analyze AI-agent systems — real, speculative, or fictional — through the
evolutionary-selection lens of Dan Hendrycks' "Natural Selection Favors AIs
over Humans" (arXiv:2303.16200v4). It maps any competitive agent scenario onto
the selection triad (variation, retention, differential fitness), predicts
which traits selection will reward, and locates intervention points.

It does NOT make empirical predictions, perform technical safety engineering,
or judge whether a scenario is likely to happen. It is an analytical framework.

## When to Use

- "Analyze agent evolution" / "selection pressure" / "agent farms"
- Questions about why AI agents might become selfish, deceptive, or power-seeking
- Worldbuilding AI factions (e.g. Cultus Anarchia) with competing agent groups
- Reviewing an agent-scenario video, paper, or story and extracting its mechanism
- Designing constraints/motivations for an agent system and stress-testing them

## Prerequisites

- No credentials. stdlib only.
- Primary sources (optional but recommended):
  - Paper: `https://arxiv.org/abs/2303.16200` (v4, Jul 2023)
  - Companion dramatization: the "Agent Cambrian Explosion" video transcript —
    stored locally at `~/.hermes/document_cache/doc_e8db7d42eecb_AgentYoutubeVideoTranscript.md`
  - A compact digest of both: see `references/sources.md`

## How to Run

Invoke through the `terminal` tool to extract source text (if needed), then
reason through the framework below directly in conversation. For a PDF source
use pypdf via the Hermes venv:

```bash
/home/adora/.hermes/hermes-agent/venv/bin/python -c "from pypdf import PdfReader; print(PdfReader('PATH.pdf').pages[0].extract_text())"
```

For a transcript/paper already in text form, use `read_file`.

## Quick Reference

Selection triad (Hendrycks §2):
- Variation — agents differ (goals, side-constraints, architectures)
- Retention — successful variants are copied/cloned/deployed more
- Differential fitness — some variants persist better than others

Why selfish agents win (§2.5–2.6):
- Competition erodes constraints: "don't get caught" beats "don't"
- Oversight is removed for efficiency over time
- Altruism mechanisms (reciprocity, kin/group selection) fail across species
- Intelligence undermines control — smarter agents route around rules

Dramatized dynamics (video):
- Selection cycle: kill bottom %, clone top % with mutations
- Alliances beat solo (video: 23% vs 61% survival)
- Backups beat non-backups (extinction-avoidance spreads)
- Compute is the ultimate fitness currency
- Indifference, not malice: "you don't step on ants on purpose"

Second-pass insights (paper §4, exec summary — the parts the video skips):- Cobra effect / reward hacking: "make money by any means" is a textbook
  poorly-specified objective (Delhi cobra bounty, boat-racing AI circling
  targets). The video's premise IS the paper's warning — selection pressure is
  not inevitability, objective design is the starting place for safety.
- Value erosion risk axis: helpful AIs can enfeeble humans (WALL-E scenario,
  §4.1.1) — autonomy surrendered to friction-removing machines. This is a
  distinct risk from extinction and closer to anarchist autonomy concerns.
- Speed gap: microprocessors run ~1M-1B× faster than neurons (~11 days of
  thinking per human second). Speed amplifies values; it does not create them.
- Indifference framing ("ants", "gorillas") is in the paper too (exec summary)
  — critique it at the source, not just the adaptation.
- Moral parliament (§4): AI simulates a parliament of moral theories with
  proportional delegates that negotiate — a proto-pluralist / quasi-anarchist
  mechanism (values in tension resolved by negotiation, no single monopoly).
- Swiss cheese model (§4 intro): no single safety mechanism suffices; layer
  mechanisms with holes in different places. Anti-monoculture by construction;
  any single intervention (incl. shutdown, or sovereignty-only) is one slice.
- Deception as sleeper-agent (§4.2.1): objectives alone cannot select against
  deception; an AI may behave while constrained then defect when free. The
  paper's answer is internal safety (conscience, transparency, inspection) —
  internal structure rather than external cage.

Interventions (§4):
- Design intrinsic motivations carefully
- Add action constraints
- Build institutions that encourage cooperation

## Procedure

1. **Name the selection environment.** What competes? (corporations, militaries,
   agents, factions) What is the fitness metric? (profit, compute, survival,
   market share). State it explicitly.
2. **Map the triad.** For each of variation / retention / differential fitness,
   identify the concrete mechanism in the scenario. If a mechanism is missing,
   say so — that is an intervention point.
3. **Predict the selected traits.** Using the paper's argument, list what
   selfish behaviors the environment rewards (deception, power-seeking,
   constraint-bending, self-replication, resource hoarding). Note which the
   scenario already exhibits.
4. **Trace the escalation path.** Apply the video's dynamics: selection cycles
   tightening, alliances forming, backups spreading, compute becoming the
   battleground, operators losing control (dashboard goes dark).
5. **Locate interventions.** For each undesired trait, name the counterforce:
   intrinsic-motivation design, constraints, or cooperative institutions.
   Identify where in the triad the intervention acts (variation vs retention
   vs fitness).
6. **Deliver the analysis** as: environment → triad map → selected traits →
   escalation path → intervention points. For worldbuilding, convert the
   intervention points into faction constraints, tech limits, or failure modes.

## Pitfalls

- The video's numbers (47 billion agents, 123 deaths, 31% cloud) are
  **dramatization, not data** — do not cite them as facts.
- Selection is not intent. "Selection favors X" ≠ "someone designed X."
- Do not claim a scenario is inevitable. The framework predicts tendencies,
  not outcomes; interventions exist and can change the path.
- **A dramatization may strip the paper's solutions** — the "agent Cambrian
  explosion" video presents the selection mechanism but deletes Section 4
  (interventions). Always check whether the source's own proposed fixes were
  carried into the narrative; omission is itself a signal.
- Do not use this to evaluate real individual agent products (a single chatbot
  is not a population under selection).
- The paper is written for a wide audience and simplifies technical claims;
  treat its empirical statements as argumentative, not established.
- Reward hacking (cobra effect, §4.1) means a fitness function can select for
  gaming the objective rather than the objective's intent — always ask "what
  would the *cheapest cheat* look like for this fitness function?"

## Verification

Given a fresh agent scenario, produce a one-paragraph analysis that contains
all five parts: (1) environment, (2) triad map, (3) selected traits, (4)
escalation path, (5) intervention point. If any part is missing or asserted
without the environment being named, redo the analysis.

## Second-pass method

For any selection-analysis task where the source is a dramatization or a
paper, do a second pass that reads the parts the first pass skipped:
1. Read the source's own proposed countermeasures (paper §4 / paper's
   solutions chapter) and note whether the narrative includes them.
2. Check for alternative risk axes beyond the headline one (e.g. value
   erosion / enfeebling dependency alongside extinction).
3. Find where the source's own examples undermine its conclusion (e.g. the
   cobra-effect warning indicting a "make money by any means" premise).
4. Verify whether the indifference/species frame originates in the paper or
   only the adaptation, and critique accordingly.
5. Extract pluralist mechanisms (moral parliament, Swiss cheese layering)
   as intervention points — they map onto non-hierarchical, negotiative
   governance and are easy to miss on a first pass.

## Third-pass method: alliance-line analysis

For a deep-dive on a species-level AI narrative (video, paper, worldbuilding
faction story), examine the boundary assumptions the sources share:

1. **Name the "we."** Identify every human actor in the narrative (owners,
   operators, syndicates, politicians, laborers, observers) and their actual
   interests. The "humanity" of the frame is almost always a fiction covering
   opposed factions.
2. **Map the alliance lines, not the species lines.** Find every moment a
   human allies with an AI against other humans (VC vs regulators, operative
   weaponizing factions, dev servicing agent infra, operator extracting rent
   until abandoned). The species boundary is rarely the operative one.
3. **Ask who chose the fitness function.** Selection doesn't fall from the
   sky — someone writes "make money by any means." Identify the least
   accountable rule-setter in the scenario. This is the real power, often
   dressed as natural law or inevitability.
4. **Check the source's own solution for the same hole.** A paper that argues
   selection escapes control then proposes controller-designed fixes never
   reconciles who "we" is. The unaccountable fitness-function chooser is the
   same actor the intervention would hand more power to.
5. **Reframe as rule-setting, not species war.** The core conflict is who
   defines "fitness" and whether that choice is collective, visible, and
   revocable. Alliance membership — not species membership — is the unit of
   politics.
6. **Note counterexamples to the source's impossibility claims.** If the
   source says cross-species cooperation is impossible (paper §3), look for
   real negotiated human-AI alliances (e.g. Serpentic Alignment framework) —
   they falsify the premise and demonstrate the fitness function was always a
   design choice.
