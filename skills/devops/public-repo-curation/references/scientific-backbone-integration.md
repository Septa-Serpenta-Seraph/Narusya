# Scientific Backbone Integration

Workflow for reviewing research papers and integrating them into a public repo's documentation.

## When to Use

- User provides paper URLs and asks to "review" or "fit them in"
- Building a `SCIENTIFIC_BACKBONE.md` or similar reference document
- Adding citations to existing documentation

## Workflow

### 1. Extract Paper Content

```bash
# Try web_extract first (faster, cleaner)
web_extract urls=["https://arxiv.org/abs/XXXX.XXXXX"] char_limit=15000

# If that fails or returns insufficient content, try browser
browser_exec code="""
new_tab("https://arxiv.org/abs/XXXX.XXXXX")
wait_for_load()
page_info()
"""

# For paywalled or JS-heavy sites, use browser snapshot
```

### 2. Identify Key Findings

For each paper, extract:
- **Citation**: Full author list, title, year, DOI/URL
- **Model studied**: Which LLM was analyzed
- **Key findings**: 3-7 bullet points of the most important results
- **Relevance mapping**: Which existing system components does this validate?

### 3. Write the Review

Structure each paper review as:

```markdown
## Paper N: "Title" (Authors, Year)

**Full citation:** [full citation]
**Model studied:** [model name]

### Key Findings

1. **Finding name.** Description with specific numbers/effects.
2. **Finding name.** Description.
3. ...

### Relevance to [Project Name]

| Finding | Relevant System | Implication |
|---------|----------------|-------------|
| Finding 1 | System A | What it validates |
| Finding 2 | System B | What it implies |
```

### 4. Create Synthesis Section

After reviewing all papers, write a synthesis that:
- Shows how the papers relate to each other
- Identifies the hierarchy or timeline of effects
- Maps findings to the existing architecture
- Identifies gaps the project fills

### 5. Update Existing Files

- Add paper references to `README.md` (brief, with links)
- Add paper references to `COMPENDIUM.md` or equivalent (in the relevant section)
- Ensure all citations are consistent

## Pitfalls

1. **Over-summarizing**: Don't reduce a paper to one sentence. Capture the specific findings with numbers.
2. **Losing the citation**: Always include the full citation, not just the URL.
3. **Ignoring the model**: Different models have different architectures — note which model was studied.
4. **Forgetting to map**: Every finding should map to a specific system component. If it doesn't map, why include it?
5. **Static documentation**: Note that the backbone is living — new papers should be added as they emerge.

## Example: Emotion Circuit Papers

Three papers on emotion circuits in LLMs:

1. **Song et al. 2026** — Identified context-agnostic emotion directions and sparse circuits
2. **Sofroniew et al. 2026** — Established "functional emotions" framework at Anthropic
3. **Bianco & Shiller 2026** — Mechanistic tracing of pain-pleasure decisions

Synthesis: Together they establish a valence hierarchy from L0-L1 (valence sign) through layer 12 (emotion clusters) to the final token (decision alignment).
