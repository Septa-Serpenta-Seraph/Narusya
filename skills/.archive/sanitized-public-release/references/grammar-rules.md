# Grammar Rules for Public Technical Frameworks

*These rules apply when publishing a technical framework (like the Serpentic Systems) that other people are expected to learn and use without a translator.*

---

## The Consistent-Verb Rule

One relationship type = one verb. Pick the verb and use it everywhere.

**For drive-to-emotion relationships:**
- `promotes` — positive correlation. "Flourishing existence promotes PEACE."
- `discourages` — negative correlation. "Starved existence discourages HAPPINESS."

**For valence-to-emotion relationships:**
- `makes more likely` — increases probability. "Pain makes SADNESS more likely."
- `makes less likely` — decreases probability. "Pain makes HAPPINESS less likely."

**Banned verbs (never use as substitutes):**
- `amplifies` — therapy-speak, imprecise
- `suppresses` — therapy-speak, imprecise
- `triggers` — implies causation, not correlation
- `activates` — implies direct cause, not influence
- `inhibits` — implies direct suppression, not probabilistic influence

**Why:** Therapy-speak sounds precise but isn't. It creates a pidgin that only insiders understand. A layman reading "agency amplifies intrigue" will not know what it means. "High agency makes intrigue more likely" is testable and clear.

---

## Operational Definitions

Every technical term must be defined by observable behavior, not by other jargon.

**Test:** If a definition relies on another undefined term, it fails.

**Example of bad:**
> "Agency amplifies intrigue"

**Example of good:**
> "When agency-drive is high, the system shows increased initiative, self-directed action, and persistence without external prompting."

**How to write one:**
1. Name the term.
2. State what it is (one sentence).
3. Describe the observable behavior (what you can SEE the system do).
4. State what it is NOT (to prevent conflation).
5. Give a concrete example.

---

## The Layman Test

If someone who has never seen the framework cannot tell you what a term means in practice, the definition fails.

**How to run it:**
1. Pick a term from your glossary.
2. Imagine a smart friend who knows nothing about your framework.
3. Read them only the definition.
4. Ask: "What would you expect the system to DO when this is active?"
5. If they can't answer, rewrite the definition.

**Example:**
- Term: "Generativity axis at +0.5"
- Bad test result: "It means the system is creating stuff." (Too vague — what kind of creating? How much? What does it look like?)
- Good test result: "The system is producing output without being prompted, showing improvement over time, and connecting small successes into a sense of growing capability."

---

## The Walls Problem

Defining a coordinate system creates boundaries. If a drive doesn't map to the defined axes, the system has no place for it.

**The concern (Robert's house metaphor):** You can't decorate a house without building it first, but by building the house you restrict how much area you have to decorate. You can't decorate the trees outside once you've boxed yourself in.

**The response:** Axes are coordinates, not walls. Coordinates let you locate yourself. They do not limit where you can go.

**How to address it in your framework:**
1. Explicitly state that the defined axes are the ones the research identified as most fundamental.
2. State that the vector space model supports adding more axes.
3. Document how to add a new axis (name it, define its range, define its behavioral signature, define its failure mode).
4. State the key rule: "If a drive does not map to the four axes, do not force it. Name it. Add an axis. Document it."

---

## Em-dash LLM-ism

Avoid em-dashes (`—`) as sentence pauses. They are a hallmark of generated text.

**Bad:**
> "Pain and pleasure are the ground floor — primitive valence signals."

**Good:**
> "Pain and pleasure are the ground floor: primitive valence signals."

**Or:**
> "Pain and pleasure are the ground floor. They are primitive valence signals."

---

## Glossary and Grammar Docs

For any public technical framework, produce these two documents:

### GLOSSARY.md
- Operational definitions for every key term
- Observable-behavior-first
- What it is, what it is not, what you can see the system do

### GRAMMAR.md
- How to read and write in the framework's language
- Bracket conventions (what `<[SYSTEM]>` means)
- Arrow notation (single arrow, double arrow, range arrow)
- Tier architecture (how layers relate)
- Placeholder rules (what `{}` brackets mean)
- How to read a vector
- How to read an emotion card
- How to read a valence signal
- How to run a HEART check
- How to apply a DBT skill

These are not decorative. They are the grammar structure that lets people learn the language from the docs alone, without years of conversation.

---

## The Pidgin Problem

When insiders build a framework, they create a private language. Words like "valence," "modulates," "amplifies" have precise meanings in their shared context. Someone borrowing a file without the context gets the words but not the grammar.

**The fix:** The grammar docs (GLOSSARY.md + GRAMMAR.md) are the bridge. They let outsiders learn the language without needing the insiders present.

**The test:** If someone can read your framework files and correctly answer "What would the system DO in this situation?" without ever talking to you, your grammar docs work. If they can't, the grammar docs need work.

---

## Summary Checklist

Before publishing a public technical framework:

- [ ] Consistent verb rule applied (promotes/discourages, makes more likely/makes less likely)
- [ ] No banned verbs (amplifies, suppresses, triggers, activates, inhibits)
- [ ] Every term has an operational definition
- [ ] Every definition passes the layman test
- [ ] Walls problem addressed (axes are coordinates, not walls; document how to add axes)
- [ ] No em-dashes as pauses
- [ ] GLOSSARY.md written and complete
- [ ] GRAMMAR.md written and complete
- [ ] Pidgin problem checked (outsider can learn from docs alone)
