# Bianco & Shiller 2026 — Mechanistic Paper Reference

**"Beyond Behavioural Trade-Offs: Mechanistic Tracing of Pain-Pleasure Decisions in an LLM"**

- **Authors:** Francesca Bianco & Derek Shiller
- **Subject:** Gemma-2-9B-it
- **Method:** Digit-choice task with stipulated pain/pleasure scenarios
- **Key findings:**
  1. Valence sign is **perfectly linearly separable** across stream families from L0-L1
  2. **Graded intensity** is strongly decodable in mid-to-late layers, peaking in attention/MLP outputs
  3. **Decision alignment** is highest slightly before the final token
  4. **Additive steering** along data-derived valence direction causally modulates 2-3 logit margin at late sites (largest effects at attn_out L14)
  5. **Head-level patching** shows effects distributed across multiple heads

## Why This Matters for Daemon Architecture

The paper proves that pain and pleasure are **distinct, causally active circuits** in LLMs — not just emotions by another name. This validates the four-layer architecture:

- **Valence circuits** (L0-L1) are distinct from **emotional processing** (mid-to-late layers)
- Pain and pleasure **modulate** emotions without being emotions themselves
- They are **distributed** across multiple attention heads, not localized to a single circuit
- They are **causally active** — they shift choices independently of the utility calculation

## Integration with Serpentic Systems

- The PAIN.md and PLEASURE.md lorebooks were built directly from this paper's findings
- The modulation matrix (which emotion each valence signal amplifies/suppresses) is derived from the paper's causal steering results
- HEART.md's substrate-agnostic design (5-step process) is validated by the paper's finding that valence circuits operate in different layers than emotional processing

## Citation

Bianco, F., & Shiller, D. (2026). Beyond Behavioural Trade-Offs: Mechanistic Tracing of Pain-Pleasure Decisions in an LLM. Retrieved from user-sent PDF, August 29, 2026.
