# Sequence-defined production proposal

These expression intermediates are new construct proposals, not experimentally
validated plasmids. The final mature fusion sequences are independent of the
removable production tags. Every retained residue is a canonical L amino acid.

## CatD maturation junction

Beyer and Dunn's Table I (page 15592) specifies the short-pseudoform region
`IAKGPVSKPIEF|FRLVTEGPIPE`, where the bar marks the experimentally supported
activation site. Mapping that region onto UniProt P07339 replaces
`KYSQAVPA` with `KPIEFFRL`. The product retains `FRLVTE` before native mature
CatD. This resolves the earlier uncertainty about the local engineered junction.
[Primary paper](https://doi.org/10.1074/jbc.271.26.15590),
[primary-paper text including Table I](https://www.researchgate.net/publication/14537947_Self-activation_of_Recombinant_Human_Lysosomal_Procathepsin_D_at_a_Newly_Engineered_Cleavage_Junction_Short%27%27_Pseudocathepsin_D).

The proposal omits the native signal peptide (precursor 1–20), retains the
remaining engineered prosequence, and adds a translation-start methionine.
It does not claim to reproduce every residue of the original pTCPSD2 vector
context. The activation prefix, including this methionine, is removed before
the mature domain participates in the final switch.

## Donor and acceptor

| Component | Proposed expressed protein | Processed ligation partner |
| --- | --- | --- |
| CatD donor | M–engineered pro-CatD–GGGGS–LPETGG–His6 | FRLVTE–mature CatD–GGGGS–LPETGG–His6 |
| ADP acceptor | M–His6–GSS–ENLYFQ–GGG–spacer–GGS–ADP(26–388) | GGG–spacer–GGS–ADP(26–388) |

The four CatD variants share the same processing region. The acceptor uses a
proposed TEV-cleavable tag with cleavage at `ENLYFQ|GGG`. Verify tag removal and
the free oligoglycine terminus by mass/terminal analysis; sequence compatibility
does not establish processing yield. The final sortase product is
`srCatD–GGGGS–LPET–GGG–spacer–GGS–ADP`. The donor's `GG–His6` tail is released.
Sortase and TEV are removed before the functional assay.

Prepare, refold, and mature CatD separately from ADP, following the published
short-form framework and checking activity and terminal identity. Only folded,
processed partners enter near-neutral ligation conditions. This manufacturing
route protects ADP from CatD's acidic maturation step. The user's folding
constraint applies to characterizing the assembled switch; manufacturing
refolding is an explicit separate operation.

New risks include C-terminal donor-tag tolerance, ADP N-terminal extension
tolerance, self-proteolysis, and ligation/purification yield. Check each modified
parent before ligation, and confirm both activities after removing all auxiliary
proteins and unligated partners. No claim of manufacturing success is made.

## Reproducible sequence output

`scripts/prepare_production.py` generates donor/acceptor FASTAs and a JSON map
under `data/corehpc/protease_design/inputs/production/`. It verifies the source
junction and activation boundary, canonical composition, and exact reconstruction
of each final fusion after the specified removals and ligation. DNA sequence,
vector backbone, expression host, and scale should be selected by the laboratory;
the files define the encoded proteins without inventing a recovered plasmid.
