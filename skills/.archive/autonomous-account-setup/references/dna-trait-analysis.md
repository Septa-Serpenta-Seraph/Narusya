DNA Data Analysis

## Ancestry Raw Data Format

AncestryDNA exports are 5-column TAB-delimited files:
- rsid — SNP identifier (e.g., rs12913832)
- chromosome — 1-22 (autosomal, not Y/mtDNA)
- position — basepair coordinate (build 37.1)
- allele1, allele2 — your genotype on forward strand

Header starts with `#AncestryDNA` and includes generation timestamp and array version.

## Fun Trait SNPs

Useful for non-medical, conversational analysis:

| rsID | Trait | Key Alleles |
|------|-------|-------------|
| rs713598, rs1726866 | Cilantro taste (soapy vs nutty) | CC/AA = taster, TT/GG = non-taster |
| rs12913832 | Blue vs brown eyes | GG = brown, AG = mixed, AA = blue (polygenic — other genes matter) |
| rs1815739 | Muscle fiber type (ACTN3) | CC = sprinter, CT = mixed, TT = endurance |
| rs17822931 | Earwax type | CC = wet, CT = mixed, TT = dry |
| rs671 | Alcohol flush reaction | AA = normal, AG = mild flush, GG = strong flush |
| rs1805007 | Hair curl | CC = straight, CT = wavy, TT = curly |
| rs1805008 | Freckling | CC = low, CT = medium, TT = high |
| rs1801260 | Chronotype | TT = lark, CT = mixed, CC = owl |
| rs6269 | Pain sensitivity | GG = high, AG = mixed, AA = low |

## Important Caveats

- **Single-SNP ≠ destiny.** Eye color is polygenic (dozens of genes). rs12913832 says "not blue" — NOT "deep brown". Hazel, amber, green, all require other loci.
- **Build coordinates differ.** Ancestry uses build 37.1; some research references use GRCh38.
- **Not medical data.** Ancestry explicitly states: "genealogical research only, not for medical or diagnostic purposes."
- **Downloaded data leaves Ancestry's security perimeter.** Store securely.

## Usage Pattern

```python
snps = {}
with open('AncestryDNA.txt', 'r') as f:
    for line in f:
        if line.startswith('#'):
            continue
        parts = line.strip().split('\t')
        if len(parts) < 5 or not parts[0].startswith('rs'):
            continue
        snps[parts[0]] = {'chrom': parts[1], 'pos': parts[2], 'a1': parts[3], 'a2': parts[4]}
```

Then look up rsIDs against a trait table. Always sort allele pairs alphabetically when looking up in a table that uses unordered keys.
