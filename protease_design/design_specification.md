# Initial computational design specification

Status: prospective screen, defined before generating or scoring candidates.
The initial literature review is in `literature_review.md`.

## Architecture and production rationale

Evaluate an N-terminal short recombinant cathepsin-D domain followed by a
spacer and the experimentally supported ADP construct lacking precursor residues
1–25. Preserve ADP's sequence and catalytic machinery. Compare the cathepsin-D
parent with the characterized E180Q, D187N, and Y10F substitutions (native
mature numbering). These offer different activity/conformation tradeoffs without
inventing a new catalytic center. They are not assumed to improve switching.

The final product is a single polypeptide containing only canonical residues.
The preferred initial manufacturing route prepares the two domains separately
and joins them with sortase. The final junction is:

`srCatD–GGGGS–LPET–GGG–spacer–GGS–ADP(26–388)`.

The cathepsin-D donor has a C-terminal `GGGGS–LPETG` recognition site with a
removable downstream purification tail. The acceptor begins at the free
`GGG–spacer–GGS–ADP` amino terminus. Sortase creates the Thr–Gly peptide bond;
remove sortase, released tail, and unligated domains before characterization.
The required oligoglycine N terminus must be exposed by verified tag removal,
not assumed to result from translation of a methionine-starting gene.

This route separates cathepsin-D refolding/maturation from ADP preparation. ADP
is added only after the L domain is folded, processed, and in a compatible
near-neutral buffer. Refolding during manufacture is not the switching input.
The already folded final enzyme is assayed only in a qualified mild-pH window.
Sortase compatibility, purification yield, and retention of each domain's
activity remain experimental requirements. A directly expressed fusion is a
later simplification if maturation can be demonstrated without damaging ADP.
The subsequently verified maturation junction and sequence-defined production
intermediates are documented in `production_design.md`; they do not change the
mature fusion sequences used in the prospective screen.

Screen six spacers: `(GGGGS)n` for n = 1, 3, 5, and `(EAAAK)n` for n = 2, 4, 6.
This gives 24 fusion proposals across four cathepsin-D sequences. These are
controlled spacer and switch-residue variations, not 24 independent catalytic
inventions. Avoid aromatic residues in the spacers to reduce obvious cathepsin-D
cleavage motifs, without claiming proteolytic resistance.

## Numbering and provenance

- ADP: UniProt P94288 has 388 residues. The experimentally tested deletion of
  the first 25 residues is described in Nakano et al., 2015. PDB 4Y7P author
  residue numbers are offset by 30 from the precursor sequence; that offset
  must not be used as a signal-peptide cleavage rule. Preserve unresolved
  residues 26–46 in the proposed construct. Catalytic Ser74 in the paper is
  precursor Ser104 and residue 79 of this ADP construct.
- Cathepsin D: UniProt P07339 residues 65–412 form the 348-residue mature
  single-chain sequence, including the region removed during two-chain
  maturation. Prefix the experimentally identified `FRLVTE` extension for the
  short recombinant form. Native mature positions are consequently offset by
  six in the 354-residue design domain. Sequence-align each experimental chain
  separately; do not concatenate crystal chains and assume continuous numbering.
- Keep source URLs and checksums. Do not infer a missing sequence from the first
  resolved atom or silently delete unmodeled residues.

## Computational evaluation

Predict isolated domains as method controls and then the intact ligated
sequences with ESMFold. Preserve complete coordinates, per-residue confidence,
PAE where available, environment/model versions, input hashes, and job commits.
The predictor does not accept pH: these predictions are fold plausibility
checks, not predictions of the two functional states.

Evaluate each domain independently against experimental structures. Report
aligned C-alpha RMSD, catalytic-residue geometry, disulfide geometry, and
confidence over structured domains separately from linkers and unresolved
termini. Examine both experimental cathepsin-D conformations for steric
interference from the partner; transferring a known conformation into a fusion
is a geometric compatibility test, not an equilibrium population prediction.

The fixed CatD framework fit excludes native residues 1–16, its experimentally
identified moving gate; it otherwise retains all resolved C-alpha positions,
including loops. The ADP fit includes all resolved C-alpha positions. There is
no score-dependent outlier rejection. This operational framework mask is more
inclusive than a secondary-structure-only core. Compare the complete resolved
CatD domain on that same fit separately, so gate deviations remain visible.
Reference numbering uses RCSB's SIFTS-to-UniProt mappings, not concatenated
two-chain residue indices. Side-chain RMSDs are diagnostic: rotamer errors in
unrelaxed predictions are not synonymous with a lost catalytic mechanism.

Initial triage targets (author-chosen, not validated success probabilities):

- Mean confidence at least 80/100 for each structured catalytic domain, with
  no collapse relative to the isolated-domain control.
- Experimental core C-alpha RMSD approximately 2.5 Å or below, and no increase
  greater than 0.75 Å relative to the corresponding isolated-domain prediction.
- No severe new interdomain overlap or partner occupation of either active
  pocket. Preserve catalytic geometry and the four cathepsin-D disulfides;
  inspect exceptions directly rather than hiding them in an aggregate score.
- Low linker confidence alone is not grounds for rejection. Global pTM also
  reflects uncertain relative domain orientation in a flexible fusion.

Use an orthogonal predictor or structural sampling to investigate shortlisted
constructs and discrepancies. Docking, if used, is a calibrated pose-generating
check against known parent specificity. Explicitly encode all substrate
stereocenters and verify them after preparation. Neither docking scores nor
static protonation estimates will be reported as catalytic selectivity.

Select ten only after reviewing actual results, retaining diversity in spacer
geometry and cathepsin-D variant among structurally plausible candidates.
Report shared failure modes: all constructs still depend on sufficient
reciprocal activity within a fold-preserving pH interval. There is no guarantee
that ten proposals will pass, and no computational result establishes enzyme
activity. The four state/chirality assays and folding controls in
`characterization_plan.md` remain necessary.

## Second-round amendment, after the initial ESMFold screen

Recorded before generating second-round predictions. All four GS5 constructs
accommodated both transferred native CatD states without sub-2 Å interdomain
contacts; the shorter flexible and initial helical spacers did not. Because
relative domain PAE remains about 25 Å, this is a geometric triage observation,
not evidence that the fusion adopts that orientation in solution.

Add `(GGGGS)7` and `(GGGGS)9` for each of the four CatD variants: eight further
constructs, 767 or 777 residues. This tests whether additional separation reduces
steric interference while preserving both domains. Longer flexible spacers can
increase heterogeneity and proteolysis risk, so greater length is not assumed
to be superior. Keep the original 24 sequences and results intact, identify
this adaptive second round separately, and retain the original evaluation
criteria. No selectivity claim follows from satisfying the geometry screen.
