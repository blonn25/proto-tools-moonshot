"""Render original vector figures from references, analysis, and explicit equations."""

import argparse
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import FancyBboxPatch
import numpy as np

from analyze_structures import ca_positions, fit, read_reference

BLUE, ORANGE, GRAY = "#0072B2", "#D55E00", "#6B7280"


def save(fig, directory, name):
    fig.savefig(directory / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(directory / f"{name}.svg", bbox_inches="tight")
    fig.savefig(directory / f"{name}.png", bbox_inches="tight", dpi=300)
    plt.close(fig)


def architecture(directory):
    fig, axes = plt.subplots(2, 1, figsize=(7.1, 4.0), gridspec_kw={"height_ratios": [1, 1.2]})
    ax = axes[0]
    ax.set(xlim=(0, 10), ylim=(0, 3)); ax.axis("off")
    ax.text(0, 2.8, "a  Final canonical-L polypeptide", weight="bold")
    for x, width, color, label in [(0.2, 3.3, BLUE, "srCatD\nL-peptide catalyst"),
                                   (3.65, 2.0, GRAY, "ligation junction\n+ spacer"),
                                   (5.8, 3.7, ORANGE, "ADP\nD-peptide catalyst")]:
        ax.add_patch(FancyBboxPatch((x, 0.85), width, 1.1, boxstyle="round,pad=0.05", facecolor=color, edgecolor="none"))
        ax.text(x + width / 2, 1.4, label, ha="center", va="center", color="white", fontsize=9)
    ax.text(0.2, 0.25, "4 CatD sequences × (6 initial + 2 adaptive spacers) = 32 proposals", fontsize=9)
    ax = axes[1]
    ax.set(xlim=(0, 10), ylim=(0, 3)); ax.axis("off")
    ax.text(0, 2.8, "b  Proposed reversible input and required readouts", weight="bold")
    ax.text(2, 1.85, "pH 5.0\nL cleavage favored", ha="center", color=BLUE, weight="bold")
    ax.text(8, 1.85, "pH 7.5\nD cleavage favored", ha="center", color=ORANGE, weight="bold")
    ax.annotate("", xy=(6.0, 2.0), xytext=(4.0, 2.0), arrowprops={"arrowstyle": "<->", "linestyle": "--", "color": GRAY})
    ax.text(5, 1.35, "Buffer exchange; activity preference remains unmeasured", ha="center", fontsize=9)
    ax.text(5, 0.65, "At each pH: L rate + D rate + fold integrity\nAfter a cycle: recovery of both catalytic activities", ha="center", fontsize=9)
    fig.tight_layout(h_pad=0.3)
    save(fig, directory, "architecture")


def native_states(references, directory):
    low = read_reference(references, "1LYA", "catd")
    high = read_reference(references, "1LYW", "catd")
    positions = sorted(set(ca_positions(low, "catd")) & set(ca_positions(high, "catd")))
    r, t, _ = fit([high[p, "CA"] for p in positions], [low[p, "CA"] for p in positions])
    low_ca = {p: v for (p, atom), v in low.items() if atom == "CA"}
    high_ca = {p: v @ r + t for (p, atom), v in high.items() if atom == "CA"}
    gate = sorted(p for p in low_ca if p <= 22 and p in high_ca)
    center = np.mean(list(low_ca.values()), axis=0)
    direction = np.mean([high_ca[p] - low_ca[p] for p in gate], axis=0)
    direction /= np.linalg.norm(direction)
    _, _, axes = np.linalg.svd(np.array(list(low_ca.values())) - center)
    vertical = axes[0] - axes[0].dot(direction) * direction
    vertical /= np.linalg.norm(vertical)
    projection = np.array([direction, vertical]).T
    fig, ax = plt.subplots(1, 3, figsize=(7.1, 2.9), gridspec_kw={"width_ratios": [1, 1, 1.1]})
    for axis, coordinates, color, label in [(ax[0], low_ca, BLUE, "a  1LYA: active-site accessible"),
                                            (ax[1], high_ca, ORANGE, "b  1LYW: gate in active site")]:
        numbers = sorted(coordinates)
        splits = np.where(np.diff(numbers) > 1)[0] + 1
        for segment in np.split(numbers, splits):
            xy = (np.array([coordinates[p] for p in segment]) - center) @ projection
            axis.plot(xy[:, 0], xy[:, 1], color="#C4C8CC", lw=0.8, zorder=1)
        xy = (np.array([coordinates[p] for p in gate]) - center) @ projection
        axis.plot(xy[:, 0], xy[:, 1], color=color, lw=2.5, zorder=2)
        for residue in (39, 237):
            point = (coordinates[residue] - center) @ projection
            axis.scatter(*point, s=24, color="#333333", zorder=3)
        axis.set_title(label, fontsize=9, loc="left")
        axis.set_aspect("equal"); axis.axis("off")
        axis.set(xlim=(-35, 35), ylim=(-35, 35))
    ax[0].text(0.03, -0.05, "Cα trace; color: native residues 3–16\nDots: catalytic Asp Cα positions", transform=ax[0].transAxes, fontsize=7)
    displacement = [np.linalg.norm(high_ca[p] - low_ca[p]) for p in gate]
    ax[2].plot(np.array(gate) - 6, displacement, "o-", color=GRAY, markersize=3, lw=1.3)
    ax[2].set(xlabel="Native gate residue", ylabel="Cα displacement (Å)", ylim=(0, 34), xticks=[3, 6, 9, 12, 15])
    ax[2].set_title("c  Experimental-state difference", fontsize=9, loc="left")
    ax[2].spines[["top", "right"]].set_visible(False)
    fig.tight_layout(w_pad=1.0)
    save(fig, directory, "native_states")


def feasibility(directory):
    fig, ax = plt.subplots(figsize=(4.5, 3.7))
    values = np.linspace(-5, 1, 501)
    x, y = np.meshgrid(values, values)
    category = np.zeros_like(x)
    category[x + y <= -4] = 1
    category[(x <= -2) & (y <= -2)] = 2
    ax.pcolormesh(values, values, category, shading="auto", rasterized=True,
                  cmap=ListedColormap(["#E9EBED", "#F3D6C5", "#BCDDEC"]), vmin=0, vmax=2)
    ax.plot(values, -4 - values, color=ORANGE, lw=1.2)
    ax.plot([-5, -2, -2], [-2, -2, -5], color=BLUE, lw=1.5)
    ax.text(-4.8, -4.7, "One-to-one fusion\ncan meet both targets", fontsize=9, color=BLUE)
    ax.text(-4.75, -1.3, "Adjusted ratio\nneeded", fontsize=9, color=ORANGE, va="center")
    ax.text(-0.2, -0.8, "Neither", fontsize=9, color=GRAY)
    ax.set(xlim=(-5, 1), ylim=(-5, 1),
           xlabel=r"$\log_{10}[a_D(\mathrm{low})/a_L(\mathrm{low})]$",
           ylabel=r"$\log_{10}[a_L(\mathrm{high})/a_D(\mathrm{high})]$")
    ax.set_title("Analytical feasibility, illustrative target S = 100", fontsize=10)
    ax.text(0, -0.24, "No measured or predicted candidate rates are plotted.", transform=ax.transAxes, fontsize=8)
    save(fig, directory, "selectivity_feasibility")


def native_ribbon(rendered, analysis, directory):
    """Compose actual CPU ray traces with the quantitative state comparison."""
    if not all((rendered / f"native_{s}.png").exists() for s in ("low", "high")):
        return
    images = [plt.imread(rendered / f"native_{s}.png") for s in ("low", "high")]
    # Identical crop preserves the shared camera and scale of both ray traces.
    occupied = np.any(np.stack([im[:, :, :3] < 0.97 for im in images]), axis=(0, 3))
    yy, xx = np.where(occupied)
    ymin, ymax = max(0, yy.min() - 25), min(images[0].shape[0], yy.max() + 26)
    xmin, xmax = max(0, xx.min() - 25), min(images[0].shape[1], xx.max() + 26)
    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.8), gridspec_kw={"width_ratios": [1, 1, 1.1]})
    for axis, im, title in zip(axes[:2], images, ["a  Accessible: 1LYA", "b  Occluded: 1LYW"]):
        axis.imshow(im[ymin:ymax, xmin:xmax]); axis.axis("off"); axis.set_anchor("N")
        axis.set_title(title, fontsize=9, loc="left")
    data = json.loads(analysis.read_text())["native_catd_state_comparison"]
    gate = data["native_gate_residue_CA_displacements_A"]
    positions = sorted(map(int, gate))
    axes[2].plot(positions, [gate[str(p)] for p in positions], "o-", color=GRAY, markersize=3, lw=1.3)
    axes[2].set(xlabel="Native gate residue", ylabel="Cα displacement (Å)", ylim=(0, 34), xticks=[3, 6, 9, 12, 15])
    axes[2].set_title("c  Gate rearrangement", fontsize=9, loc="left")
    axes[2].spines[["top", "right"]].set_visible(False)
    fig.tight_layout(w_pad=0.7)
    save(fig, directory, "native_states_ribbon")


def screen(analysis, directory):
    if not analysis.exists():
        return
    rows = [r for r in json.loads(analysis.read_text())["records"] if r["kind"] == "fusion"]
    if not rows:
        return
    fig, ax = plt.subplots(1, 2, figsize=(7.1, max(3.5, len(rows) * 0.16 + 1.2)), sharey=True)
    y = np.arange(len(rows))
    for domain, color, offset in [("catd", BLUE, -0.12), ("adp", ORANGE, 0.12)]:
        ax[0].scatter([r["domains"][domain]["resolved_mean_plddt"] for r in rows], y + offset,
                      color=color, s=15, label=domain.upper())
        ax[1].scatter([r["domains"][domain]["framework_rmsd_A"] for r in rows], y + offset,
                      color=color, s=15)
    ax[0].axvline(80, color=GRAY, ls="--", lw=0.8)
    ax[1].axvline(2.5, color=GRAY, ls="--", lw=0.8)
    ax[0].set(xlabel="Resolved-domain mean pLDDT", yticks=y, yticklabels=[r["id"].replace("CDAD_", "") for r in rows])
    ax[1].set(xlabel="Framework Cα RMSD (Å)")
    ax[0].invert_yaxis(); ax[0].legend(frameon=False, fontsize=8, loc="best")
    for axis in ax:
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(axis="y", labelsize=7)
    fig.tight_layout(w_pad=1)
    save(fig, directory, "structural_screen")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--references", type=Path, default=Path("data/corehpc/protease_design/references"))
    parser.add_argument("--analysis", type=Path, default=Path("data/corehpc/protease_design/results/analysis/structural_analysis.json"))
    parser.add_argument("--output", type=Path, default=Path("data/corehpc/protease_design/results/figures"))
    parser.add_argument("--rendered", type=Path, default=Path("data/corehpc/protease_design/results/rendered"))
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Render scientific figures through the CPU SLURM template.")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.labelsize": 9,
                         "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none"})
    args.output.mkdir(parents=True, exist_ok=True)
    architecture(args.output)
    native_states(args.references, args.output)
    native_ribbon(args.rendered, args.analysis, args.output)
    feasibility(args.output)
    screen(args.analysis, args.output)


if __name__ == "__main__":
    main()
