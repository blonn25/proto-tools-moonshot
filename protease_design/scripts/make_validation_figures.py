"""Plot actual method controls and contact diagnostics; no biochemical data."""

import argparse
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
import numpy as np

from make_figures import BLUE, ORANGE, GRAY, save


def load(path):
    return {r['id']: r for r in json.loads(path.read_text())['records']}


def calibration(esm, single, msa, refined, output):
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.4), gridspec_kw={'width_ratios': [1.25, 1]})
    for data, marker in [(esm, 'o'), (single, '^'), (msa, 's')]:
        for name, row in data.items():
            if row['kind'] != 'isolated_domain':
                continue
            for domain, score in row['domains'].items():
                axes[0].scatter(score['resolved_mean_plddt'], score['framework_rmsd_A'],
                                color=BLUE if domain == 'catd' else ORANGE, marker=marker,
                                s=40 if name in ['ADP_parent', 'srCatD_WT'] else 17, alpha=0.8)
    axes[0].set(xlabel='Resolved-domain mean pLDDT', ylabel='Framework Cα RMSD (Å)',
                xlim=(25, 100), ylim=(0.45, 30), yscale='log')
    axes[0].axvline(80, color=GRAY, ls='--', lw=0.7)
    axes[0].axhline(2.5, color=GRAY, ls='--', lw=0.7)
    axes[0].annotate('ADP: no alignment', (32.145, 22.093), xytext=(45, 13), fontsize=8,
                     arrowprops={'arrowstyle': '-', 'color': GRAY})
    handles = [Line2D([], [], marker=m, color=GRAY, ls='', label=l, markersize=5)
               for m, l in [('o', 'ESMFold'), ('^', 'Boltz: no MSA'), ('s', 'Boltz: domain MSA')]]
    axes[0].legend(handles=handles, loc='center left', frameon=False, fontsize=7)
    axes[0].text(0.04, 0.02, 'Blue: CatD   Orange: ADP', transform=axes[0].transAxes, fontsize=7)
    axes[0].set_title('a  Native-parent method controls', loc='left', fontsize=9)
    ids = [k for k in refined if refined[k]['kind'] == 'fusion' and k != 'CDAD_WT_GS3']
    values = [[v for k in ids for v in data[k]['domains']['catd']['disulfide_distances_A']]
              for data in [esm, refined]]
    rng = np.random.default_rng(20261002)
    for i, (data, color) in enumerate(zip(values, [GRAY, BLUE])):
        axes[1].scatter(i + rng.uniform(-0.15, 0.15, len(data)), data, s=12, color=color, alpha=0.7)
    axes[1].axhline(2.03, color=GRAY, ls='--', lw=0.7)
    axes[1].set(xticks=[0, 1], xticklabels=['Raw\nESMFold', 'Restrained\ngeometry repair'],
                xlim=(-0.5, 1.5), ylim=(1.1, 2.8), ylabel='CatD disulfide S–S distance (Å)')
    axes[1].set_title('b  Four disulfides per fusion', loc='left', fontsize=9)
    for ax in axes:
        ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout(w_pad=1.6)
    save(fig, output, 'validation_controls')


def contact_screen(esm, msa, output):
    variants = ['WT', 'E180Q', 'D187N', 'Y10F']
    spacers = ['GS1', 'GS3', 'GS5', 'H2', 'H4', 'H6', 'GS7', 'GS9', 'GS11']
    panels = [(esm, False, 'a  ESMFold: raw interdomain contacts'),
              (esm, True, 'b  ESMFold: transferred occluded CatD'),
              (msa, False, 'c  Boltz + MSA: raw interdomain contacts'),
              (msa, True, 'd  Boltz + MSA: transferred occluded CatD')]
    cmap = ListedColormap(['#F6F7F7', '#FBDAC8', '#F3AC83', '#D55E00', '#853A00'])
    cmap.set_bad('#BFC5CA')
    norm = BoundaryNorm([-0.5, 0.5, 4.5, 19.5, 49.5, 1000], cmap.N)
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 4.6))
    for ax, (data, transferred, title) in zip(axes.flat, panels):
        values = np.full((4, len(spacers)), np.nan)
        for y, variant in enumerate(variants):
            for x, spacer in enumerate(spacers):
                row = data.get(f'CDAD_{variant}_{spacer}')
                if row:
                    score = row['transferred_catd_states']['1LYW'] if transferred else row['interdomain_contacts']
                    values[y, x] = score['atoms_a_within_2A']
        ax.imshow(values, cmap=cmap, norm=norm, aspect='auto')
        for (y, x), value in np.ndenumerate(values):
            ax.text(x, y, '–' if np.isnan(value) else str(int(value)), ha='center', va='center',
                    fontsize=7, color='white' if value >= 20 else '#242424')
        ax.axvline(5.5, color='white', lw=2)
        ax.set(xticks=range(len(spacers)), xticklabels=spacers, yticks=range(4), yticklabels=variants)
        ax.tick_params(length=0, labelsize=7)
        ax.set_title(title, loc='left', fontsize=8)
        ax.spines[:].set_visible(False)
    fig.text(0.5, 0.015, 'Numbers: CatD heavy atoms within 2 Å of ADP. Gray: not evaluated.\n'
             'Relative domain placement is uncertain; these counts are static geometry diagnostics.',
             ha='center', fontsize=8)
    fig.tight_layout(rect=(0, 0.10, 1, 1), h_pad=1.8, w_pad=1.6)
    save(fig, output, 'contact_screen')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path('data/corehpc/protease_design/results')
    parser.add_argument('--esm', type=Path, default=base / 'analysis_esm_final/structural_analysis.json')
    parser.add_argument('--single', type=Path, default=base / 'analysis_boltz_single_pool/structural_analysis.json')
    parser.add_argument('--msa', type=Path, default=base / 'analysis_boltz_msa_final/structural_analysis.json')
    parser.add_argument('--refined', type=Path, default=base / 'analysis_refined_final/structural_analysis.json')
    parser.add_argument('--output', type=Path, default=base / 'figures')
    args = parser.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):
        raise SystemExit('Use the CPU SLURM template.')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none'})
    args.output.mkdir(parents=True, exist_ok=True)
    esm, single, msa, refined = [load(p) for p in (args.esm, args.single, args.msa, args.refined)]
    calibration(esm, single, msa, refined, args.output)
    contact_screen(esm, msa, args.output)


if __name__ == '__main__':
    main()
