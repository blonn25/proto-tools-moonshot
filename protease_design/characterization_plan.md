# Fold-preserving characterization plan

Status: proposed experiments, not performed. The trigger and final constructs
remain under evaluation. This plan incorporates the user's requirement that
pH-based switching preserve the protease and any necessary assay proteins.

## Assay design

Use purified enzyme and short synthetic peptides with LC-MS/HPLC product
quantification. No fluorescent reporter protein, coupled enzyme, or protein
carrier is required, so no additional protein must withstand the pH change.
Keep reactions near 25 °C. Begin with separately prepared buffers at pH 5.0,
5.5, 6.0, 6.5, 7.0, and 7.5. Match ionic strength and vehicle concentration,
and confirm pH at the assay temperature. Compare overlapping buffer systems
at a shared pH to identify buffer-specific effects.

Introduce protein by dilution into equilibrated buffer or exchange with a
small desalting column. Do not titrate a concentrated acid or base directly
into a protein stock: local pH excursions could damage an otherwise stable
protein. Confirm the resulting concentration and final pH.

## Check stability before interpreting switching

1. On small aliquots, record far-UV circular dichroism at the assay temperature
   before and after a hold spanning the planned assay duration. Include buffer
   blanks. Modest reversible spectral changes can reflect switching; loss of
   folded secondary structure disqualifies that condition.
2. Use analytical size-exclusion chromatography and soluble recovery to detect
   aggregation, with SDS-PAGE or intact-mass analysis to detect fragmentation.
   Global CD alone can miss damage to one domain of a fusion.
3. Exchange the same protein through a 7.5 → 5.0 → 7.5 cycle and the reverse
   cycle, then measure each module's activity at its own reference condition
   using freshly added substrate. Include matched samples held at a fixed pH
   and passed through the same exchange procedure. Activity recovery is needed
   for both domains, not merely the initially active domain.

Use at least three independently handled aliquots initially. Advance only
conditions with no detectable unfolding, aggregation, or proteolytic loss at
the precision of these measurements. An initial practical recovery target is
at least 90% relative to the handling-matched control; this is an author-chosen
screening criterion, not a published guarantee. Replicate expression batches
are necessary before making a robust stability claim. The preliminary pH
window is supported by parent-enzyme evidence, but no sequence-only calculation
can guarantee fold retention of a new fusion.

If another protein later becomes necessary, qualify it independently with the
same time, temperature, buffer, and recovery checks before including it. The
main reaction contains neither denaturants nor a thermal ramp. A separate
thermal-stability experiment, if useful later, consumes a sacrificial aliquot.

## Measure specificity after stability qualification

Use matched all-L and all-D peptides with identical sequences and terminal
chemistry. Begin with the experimentally supported ADP substrate D-Phe4 and
its L enantiomer, while checking parent cathepsin D cleavage of the exact
L substrate. Screen alternative aromatic sequences if necessary; do not assume
that a chromogenic cathepsin-D substrate establishes cleavage of unmodified
Phe4. Measure peptide solubility rather than interpreting precipitation as
conversion. Quantify intact peptide plus expected hydrolysis fragments using
standards; both desired and opposite-chirality reactions need initial-rate
measurements at each selected pH.

Run the enantiomers separately unless a validated chiral separation is used:
ordinary mass spectrometry cannot distinguish an L peptide from its D mirror.
After this calibration, examine a mixed-substrate reaction using validated
chiral analysis to reveal competitive inhibition or altered rates. Literature
reports that some D peptides inhibit cathepsin-D cleavage of L substrates;
resistance to cleavage does not imply absence of binding. An optional matched
Phe4 methyl-ester panel has more direct cathepsin-D precedent, but terminal
ester hydrolysis must be resolved from peptide-bond cleavage and cannot itself
count as peptide degradation.
Use substrate-only, isolated-parent, unfused-mixture, and catalytic-knockout
controls. Match enzyme concentration, reaction time, handling, and vehicle.
Quench only withdrawn aliquots after the defined reaction time; quenching is
not the switching input. Verify that sample processing does not cause apparent
chemical cleavage or changes in analytical response.

Report desired/opposite-chirality rate ratios with uncertainty and detection
limits. Undetectable off-target cleavage gives a lower bound on selectivity.
Retained structure with lost activity, or recovered global CD with one damaged
domain, does not establish the intended reversible switch.
