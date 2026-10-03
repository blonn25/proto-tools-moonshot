"""Create human-readable and manuscript tables from the checked ten-design package."""

import csv
import json
from pathlib import Path


def main():
    directory=Path('protease_design/designs')
    records=json.loads((directory/'selected.json').read_text())['records']
    evidence={r['id']:r for r in json.loads((directory/'evidence.json').read_text())['records']}
    rows=list(csv.DictReader((directory/'selected_metrics.csv').open()))
    table=['| Design | Residues | Oxidized monoisotopic mass (Da) | ESM / Boltz feasible grid points |',
           '| --- | ---: | ---: | ---: |']
    for row in rows:
        table.append(f"| {row['id']} | {row['length']} | {float(row['monoisotopic_mass_Da_4SS']):.2f} | {row['esm_feasible_grid_points_of1728']} / {row['boltz_feasible_grid_points_of1728']} |")
    text='''# Ten candidates for experimental testing

These are sequence-defined computational candidates, not experimentally validated
switches. The proposed reversible input is pH approximately 5.0 versus 7.5 after
fold-preserving conditions have been qualified. The L module is short recombinant
human cathepsin D; the D module is alkaline D-peptidase. Every encoded residue is
canonical. Initial targets are matched L- and all-D-Phe4 peptides, with exact
L-substrate activity requiring a parent-enzyme check.

## Selected panel

'''+ '\n'.join(table)+'''

Each scan tested 1,728 equally weighted geometric endpoints. These counts are
not thermodynamic probabilities or estimates of experimental success. Y10F GS9
passes at only one Boltz-derived grid point and D187N GS7 at eight; treat them as
more geometry-sensitive exploratory comparisons. WT GS7 and WT GS9 are useful
first fusion baselines because their catalytic domains contain no substitutions.
This prioritization does not predict their biochemical selectivity.

## Why these ten

The 33-sequence screen began with 24 proposals, added eight longer spacers, and
then added D187N GS11. Thirteen long-spacer fusions received the detailed
orthogonal-predictor, canonical-geometry, and linker tests. Ten satisfy the
prespecified domain criteria and have a passing constructed arrangement from
both predictor families. WT GS5, E180Q GS5, and D187N GS5 have no Boltz-derived
passing point in the fixed three-angle scan. Their failure is specific to this
limited geometric test; it does not prove that those proteins cannot function.
All earlier models, failed preparations, and unfavorable raw placements remain
in the project data and full-library table.

All five method controls pass with ESMFold and alignment-supported Boltz.
For each selected fusion, both raw predictors have domain mean pLDDT at least
80, framework RMSD below 2.5 Å, and no more than 0.75 Å worsening relative to
its corresponding parent. Prepared models pass canonical alpha/Ile/Thr-beta
stereochemistry and disulfide checks. The independent constructed-coordinate
audits verify preserved domain geometry, bond lengths, and bond angles.

Raw Boltz placements obstruct transferred CatD states despite native-like
domain folds. The finite torsion scan finds alternative covalently connected
arrangements; it does not establish their energy, population, or a collision-free
transition path. Native-state transfers also lack unresolved and engineered
residues. Catalytic protonation, water placement, folding free energies,
expression yields, and actual switching rates have not been calculated or measured.

## Shared experimental decision

Before scaling production of all ten, measure the isolated-parent activity
matrix on the exact matched substrates across the mild pH window. Apply the
one-to-one rate conditions in [the selectivity framework](../selectivity_framework.md).
If reciprocal selectivity is inadequate, ten spacer variants do not solve that
shared biochemical limitation. Then qualify modified donor/acceptor activities,
assembly yield, both fusion activities, and recovery after pH cycles.

Use direct LC-MS/HPLC without a reporter protein or coupled enzyme. Check
isothermal folding, aggregation, intact protein, and recovery of both activities;
only qualified conditions enter the switching assay. See the complete
[characterization plan](../characterization_plan.md). No sequence-only analysis
can guarantee that a new fusion will remain folded or meet a leakage target.

## Files and numbering

- `selected.fasta` and `selected.json`: ten untagged mature ligation products.
- `donors.fasta`, `acceptors.fasta`, and `production.json`: four proposed CatD
  precursors, four proposed tagged ADP acceptors, and verified assembly mappings.
- `selected_metrics.csv`: computed mass, extinction coefficient, and structural summaries.
- `evidence.json`: full per-design diagnostics, including unfavorable raw placements.
- `all_candidates.csv`: all 33 proposals and advancement decisions.
- `assay_record_template.csv`: empty experimental worksheet; contains no measured data.

Variants use native mature CatD numbering: Y10F, E180Q, and D187N are positions
16, 186, and 193 in the mature fusion because of the FRLVTE extension. Catalytic
CatD positions are 39/237. ADP catalytic positions are 79/82/176/317 relative to
its 363-residue domain; `selected.json` supplies each fusion's absolute positions.
Masses assume four disulfides, no retained tags, no glycans, and no other adducts.
E180Q and D187N are isobaric at a matched spacer length: intact mass alone cannot
distinguish their substitution sites. Verify encoded sequence and use peptide
mapping when assigning protein identity.

The [production proposal](../production_design.md) explains separate CatD
maturation and near-neutral ligation, protecting ADP from the acidic manufacturing
step. Expression, maturation, tag removal, ligation, and purification remain
experimental steps, not completed outcomes. The protein FASTAs do not specify
codon optimization or a vector backbone.
'''
    (directory/'README.md').write_text(text)
    paper=Path('protease_design/manuscript')
    lines=[r'\begin{table}[t]',r'\centering',r'\small',
           r'\caption{Ten proposed experimental candidates. pLDDT entries are CatD/ADP means from raw predictions. Masses assume four disulfides and no other modifications. Variant positions use native mature CatD numbering; fusion positions are offset by six. No activity or pH-stability measurements are available.}',
           r'\label{tab:panel}',r'\begin{tabular}{llrrrr}',r'\toprule',
           r'CatD & Spacer & aa & ESM pLDDT & Boltz pLDDT & Mass (kDa) \\',r'\midrule']
    for row in rows:
        lines.append(f"{row['catd_variant']} & {row['spacer']} & {row['length']} & "
                     f"{float(row['esm_catd_plddt']):.1f}/{float(row['esm_adp_plddt']):.1f} & "
                     f"{float(row['boltz_catd_plddt']):.1f}/{float(row['boltz_adp_plddt']):.1f} & "
                     f"{float(row['monoisotopic_mass_Da_4SS'])/1000:.3f} "+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
    (paper/'selected_table.tex').write_text('\n'.join(lines)+'\n')
    lines=[r'\section{Selected geometric endpoints}',r'\begin{table}[h]',r'\centering',r'\small',
           r'\caption{Passing points out of 1,728 and selected angle changes (degrees): first-linker phi, first-linker psi, central-spacer phi. Counts describe an unweighted geometric grid, not state probabilities.}',
           r'\begin{tabular}{lrrrr}',r'\toprule',r'Candidate & ESM count & Boltz count & ESM angles & Boltz angles \\',r'\midrule']
    for row in rows:
        ev=evidence[row['id']]['kinematic_feasibility']
        label=row['id'].removeprefix('CDAD_').replace('_',r'\_')
        angles=['/'.join(str(x) for x in ev[method]['selected']['delta_torsion_degrees']) for method in ['esm','boltz_msa']]
        lines.append(f"{label} & {row['esm_feasible_grid_points_of1728']} & {row['boltz_feasible_grid_points_of1728']} & {angles[0]} & {angles[1]} "+r'\\')
    lines += [r'\bottomrule',r'\end{tabular}',r'\end{table}']
    (paper/'selected_grid.tex').write_text('\n'.join(lines)+'\n')
    lines=[r'\section{Mature candidate sequences}',
           'These are final ligated proteins. Removable expression intermediates are provided separately in the accompanying FASTA files.']
    for record in records:
        lines += [r'\par\noindent\begin{minipage}{\linewidth}',r'\scriptsize',r'\begin{verbatim}', '>'+record['id']]
        lines += [record['sequence'][i:i+80] for i in range(0,len(record['sequence']),80)]
        lines += [r'\end{verbatim}',r'\end{minipage}\par\medskip']
    (paper/'selected_sequences.tex').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    main()
