# Quantitative interpretation of a two-domain switch

This is an analytical framework, not fitted experimental data or a prediction
of candidate activity. It makes the remaining biochemical requirements explicit.

Let `a_L(p)` and `a_D(p)` be initial cleavage rates normalized to nominal moles
of the corresponding intact, processed domain on a matched substrate pair at
pH `p`. These effective rates include each state's catalytically available
fraction; normalizing only to the open conformer would remove the very gating
effect being tested. Concentrations, terminal
chemistry, temperature, and the observation window are fixed. Initially assume
each isolated domain has negligible activity on the other enantiomer. Let
`r = [L domain]/[D domain]`; an intact one-to-one fusion fixes `r = 1`.

For a low-pH L-selective state and high-pH D-selective state:

```
S_low  = r a_L(low) / a_D(low)
S_high = a_D(high) / (r a_L(high))
```

Both selectivities can reach an engineering target `S` only if:

```
S a_D(low)/a_L(low) <= r <= a_D(high)/(S a_L(high))
```

Consequently, the product of the two domains' activity changes must satisfy:

```
[a_L(low)/a_L(high)] [a_D(high)/a_D(low)] >= S^2.
```

This is necessary and sufficient for *some* positive domain ratio when the
rates are positive and the simplified independent-domain model applies. A
one-to-one fusion additionally requires the interval to contain `r = 1`.
Increasing the concentration of the entire fusion scales both rates and cannot
repair an unfavorable within-state selectivity ratio. A substrate or mutation
that increases acidic L activity could also raise high-pH L leakage, so either
change must be evaluated at both pH values.

When either domain has non-negligible cross-chirality activity, measure the
complete matrix `a_ij(p)`, where `i` is domain identity and `j` is substrate
chirality. The total rates are:

```
v_L(p) = [D domain] [r a_LL(p) + a_DL(p)]
v_D(p) = [D domain] [a_DD(p) + r a_LD(p)].
```

Use these rates to calculate the two state-selectivity ratios. Intrinsic
cross-cleavage creates a leakage floor that cannot be removed merely by
suppressing the other domain. Interdomain effects, partial maturation,
unequal active fractions, substrate competition, and self-proteolysis can all
invalidate predictions from isolated-domain measurements.

For a fusion with two active sites, nominal protein concentration does not
establish either site's active fraction. Report rates per nominal fusion
concentration for the switching comparison, and characterize functional
concentration separately at each module's reference condition. Do not silently
switch normalization conventions between states.
Distinguish transient switching lag from steady-state rates by recording full
time courses after buffer exchange. Below-detection rates supply bounds rather
than zero-valued denominators. Do not extrapolate an unmeasured acidic ADP rate
from a high-pH curve and label the resulting ratio as experimentally supported.
