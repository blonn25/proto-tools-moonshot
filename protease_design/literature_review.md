# Literature review of protease chirality switching

Review date: 2026-10-02. The initial feasibility review was completed before
candidate generation. Implementation-specific sources will be added as needed.
No experimental results have been generated in this project.

Implementation-method update: OpenMM 8 supports reproducible molecular mechanics
calculations ([Eastman et al., 2024](https://doi.org/10.1021/acs.jpcb.3c06662)).
Amber ff14SB protein parameters ([Maier et al., 2015](https://doi.org/10.1021/acs.jctc.5b00255))
and OBC implicit solvent ([Onufriev et al., 2004](https://doi.org/10.1002/prot.20033))
are suitable for a narrowly scoped restrained geometry-repair diagnostic.
This addition follows observation of compressed disulfide distances in both
isolated and fusion ESMFold predictions. Such minimization neither establishes
a pH-dependent conformational ensemble nor validates catalysis; energy changes
across different sequences will not be used as activity scores.

The review asks whether a protein composed exclusively of canonical L-amino
acids can switch between cleaving L-peptides and entirely D-peptides with low
opposite-chirality activity. It will separate direct experimental evidence from
proposed engineering extrapolations and computational predictions.

## Review scope

1. Natural L-protein D-aminopeptidases and D-endopeptidases, including actual
   peptide substrates, catalytic efficiencies, structures, and specificity.
2. L-peptide proteases with well-characterized activation and inactivation.
3. Reversible and irreversible protein switches and mutually exclusive gating.
4. Computational enzyme and protein design with experimental success metrics.
5. Experimental assays that distinguish true peptide-bond hydrolysis from
   reporter cleavage, precipitation, nonspecific signal changes, or racemization.

## Evidence standards

Primary papers and experimental structures take precedence over summaries.
Specificity claims must identify substrate chemistry and assay conditions.
Cleavage of a chromogenic amino-acid amide alone does not establish hydrolysis
of an internal bond between two D-amino acids. Mixed-chirality peptidoglycan
activity does not establish activity on entirely D-peptide substrates.
Structure prediction, docking, and molecular dynamics cannot alone establish
catalytic activity or a switching selectivity ratio.

## Main conclusion

The strongest starting point is a modular system combining a natural D-peptide
endopeptidase with a separately controlled L-peptide protease. The original
ADP–pepsinogen hypothesis required pH 2.5 and is no longer the leading proposal:
the user requires characterization that preserves all required protein folds,
and ADP stability at that pH is unsupported. A reversible cathepsin-D/ADP system
within a preliminary pH 5–7.5 window is now being evaluated. Published component
stability overlaps there, but sufficient reciprocal activity remains unproven.

This is a switch in the substrate preference of a two-catalyst protein system,
not a claim that one active site reverses its stereochemistry. The user permits
multiple catalytic components. A native catalytic scaffold is preferable to a
newly invented D-peptide active site for the first experimental panel.

## Search approach

Searches covered PubMed, primary publisher pages, author-hosted manuscripts,
RCSB PDB, and official method repositories. Query families included
`D-stereospecific aminopeptidase all D peptides`, `alkaline D-peptidase Bacillus
cereus DF4-B`, `pepsinogen fusion activation pH`, `protease stereospecificity D
phenylalanine`, `switchable split protease`, `pH-responsive protein design`,
and `computational enzyme design active site preorganization`. Searches included
2024–2026 publications. This is a focused narrative review, not an exhaustive
systematic review.

Full primary text was accessible for the ADP structural study, several switching
and design studies, and historical pepsin substrate experiments. Some older
papers were available through indexed abstracts or author-uploaded text.
Missing information is not inferred as a measured result. Dates follow primary
records, not crawl dates: Baker's pepsin paper is from 1951, despite some secondary
listings labeling it 1952.

## D-peptide catalysis by L-amino-acid proteins

**Asano et al., 1996.** ADP hydrolyzed entirely D-phenylalanine oligomers,
including D-Phe tetrapeptide, with no reported activity on their L counterparts.
The paper reports relative activities of 7.9%, 15%, 30%, and 46% at pH 7.1,
7.5, 7.9, and 8.5, respectively, relative to pH 10.3. Activity at pH 2.5 was
not established. Activity was retained after one hour at 30 °C over pH 5–10.
**Implication:** examine a fold-preserving window starting at pH 5; retention
after incubation does not establish the instantaneous activity or leakage there.
[Primary paper](https://doi.org/10.1074/jbc.271.47.30256).

**Nakano et al., 2015.** The 2.1 Å apo structure, PDB 4Y7P, identifies Ser74,
Lys77, Tyr171, and His312 in ADP's catalytic network. The reported substrate
poses are computational, not substrate-bound crystal structures. Its molecular
dynamics used active-site restraints, so geometric persistence is not independent
proof of preorganization. **Implication:** preserve experimental scaffold
geometry but do not treat docking as an observed catalytic complex.
[Primary paper](https://doi.org/10.1038/srep13836),
[structure](https://www.rcsb.org/structure/4Y7P).

**Asano et al., 1989.** A distinct D-aminopeptidase from *Ochrobactrum anthropi*
cleaves D-alanine oligomers and prefers appropriate peptides over some amide
reporters. **Implication:** an alternative for alanine-rich substrates, but its
larger oligomeric architecture and substrate preference are less convenient
than ADP for an aromatic-peptide panel.
[Primary record](https://pubmed.ncbi.nlm.nih.gov/2760064/).

**Bompard-Gilles et al., 2000.** The D-aminopeptidase structure resolves three
domains, including an accessory-domain loop entering the substrate pocket.
**Implication:** substrate recognition depends on more than the catalytic
domain; deleting accessory regions is not an evidence-based size reduction.
[Primary record](https://pubmed.ncbi.nlm.nih.gov/10986464/),
[structure](https://www.rcsb.org/structure/1EI5).

**Fanuel et al., 1999.** DmpA prefers D-alanine in some chromogenic derivatives,
but conventional peptide substrates reveal an L-aminopeptidase preference.
**Implication:** its name and reporter activity do not establish all-D peptide
degradation or an externally controlled chirality switch.
[Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC1220341/).

**D-amino-acid amidase structural study, 2007.** The studied amidase hydrolyzes
D-amino-acid amides but lacks peptidase activity. **Implication:** neither an
amidase annotation nor an amino-acid amide assay establishes the required
reaction. [Primary record](https://pubmed.ncbi.nlm.nih.gov/17331533/).

**Delmarcelle et al., 2005.** The reported specificity inversion changes an
aminopeptidase into a carboxypeptidase, not an L-to-D substrate chirality switch.
**Implication:** distinguish cleavage position from substrate stereochemistry.
[Primary paper](https://doi.org/10.1110/ps.051475305).

**Haim et al., 2026.** Chemical cyclization improves a D-stereospecific
hydrolase's robustness. The study assays a peptide containing a central
D-lysine and adds chemical cross-links. **Implication:** useful stability
precedent, but not direct evidence for the all-D substrate requirement or the
simplest entirely genetically encoded architecture.
[Primary paper](https://doi.org/10.1002/anie.202521611).

## L-peptide catalysis and acid activation

**Keilová, Bláha, and Keil, 1968.** Cathepsin D cleaved peptide bonds in
tri- and tetraphenylalanine methyl esters. Changing stereochemistry at a
susceptible bond blocked cleavage in a tested hexapeptide; D isomers could
competitively inhibit L-substrate cleavage. **Implication:** aromatic oligomers
have useful precedent, but methyl esters are not interchangeable with free
carboxylates. Test mixed-substrate inhibition after measuring each enantiomer
separately, and distinguish ester hydrolysis from actual peptide fragmentation.
[Primary paper](https://doi.org/10.1111/j.1432-1033.1968.tb00232.x).

**Baker, 1951.** Pepsin hydrolyzed suitable aromatic L-peptides, whereas tested
substitutions by D residues blocked cleavage. **Implication:** investigate
matched aromatic enantiomers, while verifying the exact chosen tetrapeptide
rather than assuming its kinetics.
[Primary record](https://pubmed.ncbi.nlm.nih.gov/14907769/),
[paper DOI](https://doi.org/10.1016/S0021-9258(18)50936-4).

**Pepsin fluorescent-substrate kinetics, 1975.** Appropriate A-Phe-Phe-B
oligopeptides were cleaved at the central aromatic bond; surrounding interactions
affected catalysis. **Implication:** terminal chemistry and flanking residues
must match between substrate enantiomers.
[Primary record](https://pubmed.ncbi.nlm.nih.gov/1103147/).

**Tanaka and Yada, 1996.** An N-terminal thioredoxin fusion enabled soluble
porcine pepsinogen production in *E. coli*. Acidification yielded active pepsin
with properties comparable to the commercial enzyme. **Implication:** retain
the complete prosegment and put the partner upstream. ADP is a different,
larger partner, so its fusion remains an extrapolation.
[Primary paper](https://doi.org/10.1042/bj3150443).

**Tanaka and Yada, 1997.** Thioredoxin–pepsinogen showed predominantly
intramolecular activation at acidic pH values including pH 3.
**Implication:** a fusion can retain activation without added protease, but
this does not establish the activation rate of a new construct.
[Primary paper](https://doi.org/10.1006/abbi.1997.9925).

**Malik et al., 2006.** Ecotin–human-pepsinogen produced folded zymogen in the
bacterial periplasm; acidification generated pepsin and digestion of the upstream
partner. **Implication:** sacrificial partner degradation is plausible, but
its rate and completeness cannot be assumed for ADP.
[Primary paper](https://doi.org/10.1016/j.pep.2006.02.018).

**Konno et al., 2000.** Alkaline-denatured pepsin is partly structured and does
not simply regain native activity after returning to acid. **Implication:**
start with intact pepsinogen and describe the proposed transition as one-way.
Returning to the initial buffer is not a validated reset mechanism.
[Primary paper](https://doi.org/10.1021/bi991923d).

**Prosegment-mediated folding study, 2014.** NMR and folding analysis support
the prosegment's role in navigating unfavorable pepsin folding pathways.
**Implication:** evaluate the intact zymogen; a confident mature-pepsin model
alone is insufficient. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC3887198/).

The experimental porcine-zymogen reference is
[PDB 3PSG](https://www.rcsb.org/structure/3PSG). Sequence extraction must retain
unresolved residues from the polymer sequence rather than deleting them from
the expressed construct. Native disulfides require explicit attention.

## Alternative switches

**Lee, Gulnik, and Erickson, 1998.** Cathepsin D adopts a folded inactive
conformation at pH 7.5 (1LYW), with its N-terminal segment occupying the active
site. The transition is reversible. The low-pH crystal was obtained at pH 5.1,
but high ammonium sulfate stabilizes that conformation: the crystal alone
does not establish strong activity at pH 5 in dilute assay buffer. Substrate
binding also affects the transition. **Implication:** retain the mature
N-terminal segment and test both substrates at both pH values; avoid treating
pH as a binary switch without kinetics.
[Primary paper](https://doi.org/10.1038/2306),
[author manuscript](https://www.researchgate.net/publication/13502101_Conformational_switching_in_an_aspartic_proteinase).

**Beyer and Dunn, 1996.** Autoprocessed recombinant cathepsin D retains a
prosegment extension. An engineered cleavage site at the native mature
boundary failed to process as intended; moving it upstream yielded an active
shorter pseudoform. **Implication:** activity of a pseudoform does not establish
the native N-terminal pH switch. Production and mature-terminal verification
are explicit design requirements, not routine assumptions.
[Primary paper](https://doi.org/10.1074/jbc.271.26.15590).

**Conus et al., 2012.** Purified cathepsin D had detectable activity at pH 5
and below in the reported assay, with little activity above that range.
**Implication:** pH 5 is a reasonable screening boundary; substrate-dependent
behavior and activity of a fusion must be measured independently.
[Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC3375537/).

**Goldfarb et al., 2005.** The short recombinant cathepsin-D form and four
point variants were tested for pH-dependent kinetics, recovery, and tryptophan
fluorescence. E180Q, D187N, and Y10F increased catalytic efficiency on the
reported substrate; E5Q decreased it. The proteins retained activity following
exposure over pH 3–7.5. Refolding yields were a practical limitation. The
processed construct has a six-residue N-terminal extension, FRLVTE, before
the native mature sequence. **Implication:** use this experimentally supported
recombinant scaffold and consider the characterized substitutions as a bounded
design space. Their activity on our substrates and leakage at pH 7.5 remain
unknown. Separate domain preparation can avoid exposing ADP to acidic maturation.
[Primary paper](https://doi.org/10.1021/bi0511686),
[author manuscript](https://pmc.ncbi.nlm.nih.gov/articles/PMC2569848/).

**Popp et al., 2009; Kobashigawa et al., 2009.** Sortase-mediated ligation
joins an LPXTG-tagged protein to an N-terminal oligoglycine acceptor using an
ordinary peptide bond. Protein-to-protein ligation has been demonstrated.
**Implication:** independently prepare the protease domains and join them under
mild conditions, removing sortase and unreacted domains before assays. The
joined sequence can contain only canonical residues. Ligation yield and
retention of both activities are construct-specific uncertainties.
[Protocol](https://doi.org/10.1002/0471140864.ps1503s56),
[protein-ligation study](https://doi.org/10.1007/s10858-008-9296-5).

**Dagliyan et al., 2018.** SPELL combined structural split-site selection with
inducible reassembly and demonstrated controlled TEV activity. Background
reassembly and weak induced activity were important limitations.
**Implication:** independently inventing a D-peptidase split switch and its
reciprocal L-module control adds uncertainty compared with a native zymogen.
[Primary paper](https://doi.org/10.1038/s41467-018-06531-4).

**Boyken et al., 2019.** Designed histidine networks produced experimentally
characterized pH-dependent conformational changes. **Implication:** rational
pH switching is possible, but a histidine-rich linker alone does not recreate
the mechanism; both conformational states and function require validation.
[Primary paper](https://doi.org/10.1126/science.aav7897).

**Arai et al., 2001.** Helical linkers helped separate domains in a bifunctional
fusion, and length influenced structure and function. **Implication:** compare
spacer geometry and length as controlled variables; behavior in an unrelated
fusion does not guarantee performance here.
[Primary paper](https://doi.org/10.1093/protein/14.8.529).

Mirror-image D-proteases and photocaged noncanonical residues violate the
user's constraints. Metal or inhibitor exchange would require a demonstrated
mutually exclusive control mechanism. Canonical photoreceptor domains are
allowed, but currently offer less direct support for controlling the D catalyst
than acid activation offers for controlling the L catalyst.

## Computational design evidence and useful metrics

**Watson et al., 2023.** RFdiffusion demonstrated backbone generation and
functional-motif scaffolding across multiple design tasks. **Implication:**
motif-scaffolding success does not demonstrate D-peptide catalysis.
[Primary paper](https://doi.org/10.1038/s41586-023-06415-8).

**Dauparas et al., 2022.** ProteinMPNN generated experimentally successful
protein sequences. **Implication:** sequence–backbone compatibility is useful,
but does not predict catalytic rate or switch leakage. Avoid unnecessary
redesign of experimentally supported active sites.
[Primary paper](https://doi.org/10.1126/science.add2187).

**Dauparas et al., 2025.** LigandMPNN incorporates nonprotein atomic context.
**Implication:** substrate-pocket redesign, if needed, should explicitly model
stereochemistry and preserve catalytic residues. Binding compatibility is not
hydrolytic activity. [Primary paper](https://doi.org/10.1038/s41592-025-02626-1).

**Lauko et al., 2025.** Serine-hydrolase design combined active-site ensembles
along the reaction coordinate with experimental kinetics and crystallography.
The model reaction was ester hydrolysis. **Implication:** esterase success does
not solve general protease design; peptide-bond cleavage and reciprocal
regulation add separate requirements.
[Primary paper](https://doi.org/10.1126/science.adu2454).

**RFdiffusion2, 2025/2026.** Atom-level scaffolding expands available active-site
geometries and has experimental support for several reactions.
**Implication:** an alternative if natural scaffolds fail, rather than a reason
to discard direct D-peptide-cleavage evidence in the initial panel.
[Primary paper](https://doi.org/10.1038/s41592-025-02975-x).

**Abramson et al., 2024.** AlphaFold 3 predicts diverse complexes, but chemical
validity and chirality still require checking. **Implication:** a D-peptide
cannot be represented as an ordinary protein FASTA chain. Use explicit
atom-level stereochemistry and verify output stereocenters.
[Primary paper](https://doi.org/10.1038/s41586-024-07487-w).

The intended screen combines sequence validation, domain-specific refolding
confidence, comparison with experimental structures, catalytic geometry,
disulfide geometry, and pocket accessibility. Orthogonal predictions can reveal
fragile structural conclusions. Report metrics separately: global confidence
does not establish biochemical function, and low confidence in a deliberately
flexible linker need not disqualify a construct. Docking energies are not
activation barriers and cannot supply a selectivity ratio.

## Proposed experimental success criteria

The following are project-specific proposals, not measured results or calibrated
probabilities of success.

- Start with purified protein and an all-L/all-D phenylalanine tetrapeptide pair
  with identical terminal chemistry. Confirm solubility and cleavage of these
  exact substrates by isolated parent enzymes before interpreting fusion results.
- Investigate a provisional pH 5.0–7.5 window at approximately 25 °C, contingent
  on direct fold-retention and recovery checks. Do not expand to stronger acid
  simply to suppress D-module activity. See `characterization_plan.md`.
- Quantify all four state/chirality combinations with initial rates, time courses,
  and product identities. Use LC-MS or chromatography with authentic standards.
  Enantiomers have the same mass, requiring separate reactions or validated
  chiral separation when mixed.
- Define within-state selectivity as desired/opposite-chirality initial rate at
  matched concentrations. A below-detection denominator yields a lower bound,
  not infinite selectivity. An initial engineering goal is at least 100-fold
  preference in each state with measurable turnover and meaningful conversion;
  this threshold is chosen here, not prescribed by the user.
- Include substrate-only pH shifts, parent enzymes, an unfused mixture, catalytic
  knockout controls, and an activation-defective or inhibited L-module control.
  Test residual D activity after acidification and recovery after neutralization.
- Exclude precipitation, chemical hydrolysis, racemization, and pH-dependent
  fluorescence artifacts. Quantify intact substrate and stoichiometric fragments.

The initial claim would be controlled fragmentation of selected peptides.
Complete digestion into amino acids, arbitrary D-protein degradation,
and intracellular operation are not supported by current evidence. Reversibility
of a new fusion remains a testable hypothesis.

## Decision before candidate generation

The original ADP–pepsinogen architecture is archived as a rejected strong-acid
option. Evaluate cathepsin D followed by a spacer and ADP, preserving the mature
cathepsin D N terminus and both catalytic domains. A C-terminal partner must
leave the N-terminal switching trajectory and both substrate pockets accessible.
Use the characterized short recombinant form rather than assuming native
maturation. Independently prepare it and an oligoglycine-tagged ADP, then
evaluate sortase-mediated joining as the first production route. The D module
will not be present during acidic cathepsin-D maturation. Additional production
steps are a tradeoff for preserving experimentally supported domain preparation.

The mild-pH concept still requires adequate L cleavage at pH 5, low D leakage
there, low L leakage at pH 7.5, and activity recovery without unfolding or
self-proteolysis. Computation can triage folding and geometry; functional
verification requires experiments. Ten selected constructs must be described
as justified experimental candidates, not ten confirmed switches. If the
fold-preserving pH interval cannot support a credible reciprocal switch, revisit
the trigger rather than relaxing the user's stability requirement.
