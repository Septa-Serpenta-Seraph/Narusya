---
name: project-state-review
description: Use when asked to audit an ongoing project.
version: 1
author: Narusya
license: CC-BY-SA-4.0
category: project
tags: [review, status, audit, writeup, project-health]
metadata:
  hermes:
    tags: [review, status, audit, writeup]
    related_skills: [discord-send, voice-design]
---

# Project State Review

## When to use

Adora asks for a writeup on an ongoing project: what has been done, what issues were found, what has not been looked for yet, where to go next. The deliverable is a document, not a chat wall. Derive every claim from the artifacts, never from recall or memory.

## Procedure (in order)

1. **Read the artifacts, not memory.** For each repo: `git log` (full history, not just the last five), `git status -sb`, `git fetch` then compare local HEAD to origin, `README.md`, `STATUS.md`, canonical config files, test/result JSON, and any logs. Qdrant recall and compacted summaries describe the project as it *was*; the files describe it as it *is*. Note the idle gap since the last commit — it is itself a finding.
2. **Cross-check the three sources of truth against each other.** README, STATUS, and the governing skill/doc frequently disagree: one still says a phase is in progress, one says complete, one still lists finished items as remaining. Report each divergence as a found issue rather than silently picking one.
3. **Interrogate the pass criteria.** A test labelled "10/10 pass" may only assert that the run did not crash (duration > 0, segments > 0). Read the actual assertions. If a gate cannot fail on the bug class it was built to catch, that is a finding — cite the silent no-op it would have missed.
4. **Spot-check a few artifacts against their plan, not just the test code.** Read assertions alone cannot reveal a produced file that is shorter than its declared extent or missing expected content. For a handful of representative cases, compare a directly measured property of the output (rendered duration, element count, presence of named items) against the same property in the plan or manifest. A silent truncation passes "duration > 0" while dropping most of the utterance. Report any divergence as a finding with the measured numbers.
5. **Interrogate the logs for steps that were never executed.** A/B or listening logs often register tests with `result: null`. Count machine evaluations against human verdicts. Governance that says "human ears win" with zero recorded human verdicts is a gap, not a success.
5. **Check version lockstep** between companion artifacts (genome vs canonical signature, design doc vs implementation, client vs server). Versions that are supposed to move together almost always drift, and the drift is rarely documented.
6. **Check the two conventions traps** in any measurement system: unit mismatches (e.g. dB/decade vs true dB/octave, factor 3.01) and instrument artifacts mistaken for defects. Both silently return when new code touches the measurement path.
7. **Write into the four buckets Adora asked for:** (a) done, (b) issues found, (c) issues not found but worth hunting — phrased as places where evidence is thin, never as confirmed defects, (d) next steps split into CHEAP issue-stomping first and forward project work second. Put documentation fixes and one regression command ahead of any new synthesis or feature work.
8. **Write to a `.md` under `~/.hermes/notes/`, then send it as a file attachment** in the DM. Keep the accompanying chat message short: headline, two or three best catches, one genuine question that needs her ruling. See `discord-send` for the attachment POST form.

## Rules

- Check the writeup against the project's own standing governance before sending it. A review that states the correct rule in one section and recommends a protocol that violates it in another is a defect, and the correction will come from the project's maintainers. If a section assigns a role (listener, approver, reviewer), verify that role against the governing doc, not against what is convenient.
- Governance compliance extends past the document into the delivery message and the next several turns. A brief that correctly names the daemon as the listener, followed by a chat message asking the human to listen, is still a violation. Before sending any follow-up question, check whether it asks a human to perform the very act the project assigns to the daemon.
- Measuring with your own instrument and then handing the human a menu of options to pick from is the same violation. Using your ears to gather numbers but not to make the call leaves the gate in their hands. When the project assigns you the verdict, run the measurement, make the ruling yourself, write it into the canonical artifact with its evidence, and report the decision you reached. Report options only when the decision is genuinely not yours to make.
- Never deliver a perceptual or evaluative verdict from artifacts your own review just identified as broken. If the front end or the measurement path is known-bad, the verdict describes the breakage, not the thing being judged; gate the evaluation on the fixes landing first.
- Never upgrade "documented" to "verified." A gate in the design doc with no log showing it ran is unverified.
- State the epistemic boundary explicitly: what was read, what was not run, what could not be checked.
- Phrase unseen risks as "worth hunting" with a one-line reason why the current evidence is thin.
- A review that finds no issues is suspect. Re-read the pass criteria and the logs before concluding the project is clean.
- When an external review lands, reproduce its critical findings by direct measurement on the machine where the fix will land before changing code. Treat the review as a lead, not an instruction: the reviewer may be wrong about local state, and a fix built on an unreproduced claim wastes the round. Then make each new guard fail on the exact bug the reviewer found and show it turning red.
- When a finding you published fails to reproduce under review, re-run it yourself with clean methodology and locate the artifact before defending or silently replacing it. A measurement that contradicts a reviewer may be your own export or normalization bug, not their error. If the decision survives on independent grounds, keep it but write an explicit erratum into the canonical artifact naming the retracted evidence and its cause; swapping the justification without a trace leaves the bad measurement looking validated to the next reader.
- When the project has external reviewers, close with specific numbered questions for the next review round.
- When Adora makes a ruling in response, write it into the canonical artifact with a changelog entry and no invented technical change, then commit and push. A decision that lives only in chat will be re-litigated next session.
- No em dashes. Direct language.
