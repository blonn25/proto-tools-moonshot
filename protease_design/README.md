# Switchable protease design

This project investigates genetically expressible proteins that switch between
cleaving L-peptides and entirely D-peptides, while minimizing cleavage of the
opposite chirality in each state. The target deliverable is ten candidates
supported by an extensive literature review and reproducible computational
evaluation, together with an ICLR-format manuscript and figures. Experimental
activity is not established by computational predictions.

All protein components must use the 20 canonical L-amino acids. Architecture,
substrate sequence, trigger, and reversibility will be selected from the evidence.
Purified in-vitro characterization is the initial application unless the review
supports another choice. CoreHPC GPU use is capped at two concurrently across
this campaign. Bulk downloaded structures, model weights, environments, and run
outputs belong in ignored `data/corehpc/protease_design/`; logs belong in `logs/`.

- [Progress manifest](manifest.md)
- [Literature review](literature_review.md)
- [Design specification](design_specification.md)
- [Fold-preserving characterization plan](characterization_plan.md)
- [Quantitative selectivity requirements](selectivity_framework.md)

The review must establish a feasible D-peptide catalyst and switching mechanism
before candidate generation. Designs are experimental proposals, not validated
enzymes, until biochemical measurements exist.
