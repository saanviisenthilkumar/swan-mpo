#!/usr/bin/env python3
"""Publication-resolution Figures 2 and 4 from the verified OR2 ZIP tables."""
import io
import sys
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd

COLORS = {"navy": "#23405B", "teal": "#087E8B", "gold": "#D39139", "grey": "#B7C5D0", "red": "#BE6950"}


def load(z, name):
    return pd.read_csv(io.BytesIO(z.read(name)))


def style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 11.6,
        "axes.labelsize": 10, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "savefig.facecolor": "white", "figure.facecolor": "white",
        "axes.axisbelow": True, "pdf.fonttype": 42,
    })


def save(fig, target):
    fig.savefig(str(target.with_suffix(".png")), dpi=360, facecolor="white", bbox_inches="tight", pad_inches=0.25)
    fig.savefig(str(target.with_suffix(".pdf")), facecolor="white", bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


def figure2(s8, out):
    style()
    assert len(s8) == 20 and set(s8.panel) == {"Colon", "Prostate", "RCC"}
    panels = [("Colon", "Colorectal cancer"), ("Prostate", "Prostate cancer"), ("RCC", "Renal cell carcinoma")]
    fig, axes = plt.subplots(2, 3, figsize=(15.8, 10.7), height_ratios=[1.0, 1.05])
    fig.subplots_adjust(top=0.89, bottom=0.10, left=0.15, right=0.99, hspace=0.42, wspace=0.36)
    fig.suptitle("Internal discovery: integration changes compound priorities", fontsize=16, fontweight="bold", x=0.50, y=0.98)

    for i, (panel, name) in enumerate(panels):
        sub = s8[s8.panel == panel].sort_values("rank_Internal_SWAN_BestNode").copy()
        n = len(sub)
        yp = np.arange(n)
        highlight = {"Muricatacin": COLORS["teal"], "Annomuricin C": COLORS["gold"], "Annopentocin A": COLORS["red"]}
        palette = [highlight.get(x, COLORS["grey"]) for x in sub.Compound]
        ax = axes[0, i]
        bars = ax.barh(yp, sub.Internal_SWAN_BestNode, color=palette, edgecolor="white", height=.68)
        ax.set_yticks(yp)
        ax.set_yticklabels(sub.Compound)
        ax.invert_yaxis()
        ax.set_xlim(0, 1.0)
        ax.set_xlabel("Integrated SWAN-BestNode score")
        ax.set_title(f"{chr(97 + i)}   {name}  (n = {n})", fontweight="bold", loc="left", pad=12)
        ax.grid(axis="x", alpha=.15, lw=.7)
        for bar, val in zip(bars, sub.Internal_SWAN_BestNode):
            ax.text(float(val) + .008, bar.get_y() + bar.get_height()/2, f"{val:.3f}", va="center", fontsize=8.2, color=COLORS["navy"])

        ax = axes[1, i]
        # Reproduce the original manuscript's lower-panel sequence: binding-only
        # rank first; within tied binding ranks, lower integrated priorities first.
        # The original rank axis placed rank 1 at the RIGHT.
        rank_sub = sub.sort_values(["rank_bestnode_binding", "rank_Internal_SWAN_BestNode"],
                                   ascending=[True, False]).copy()
        old = rank_sub.rank_bestnode_binding.to_numpy(float)
        new = rank_sub.rank_Internal_SWAN_BestNode.to_numpy(float)
        rank_y = np.arange(n)
        rank_colors = [highlight.get(x, COLORS["grey"]) for x in rank_sub.Compound]
        for yy, o, nn, c in zip(rank_y, old, new, rank_colors):
            ax.plot([o, nn], [yy, yy], color=c, lw=2.2, alpha=.72, zorder=1)
            ax.scatter([o], [yy], marker="o", s=31, color="white", edgecolor=c, linewidth=1.6, zorder=3)
            ax.scatter([nn], [yy], marker="D", s=40, color=c, edgecolor="white", linewidth=.5, zorder=4)
        ax.set_yticks(rank_y)
        ax.set_yticklabels(rank_sub.Compound)
        ax.invert_yaxis()
        ax.set_xticks(range(1, n+1))
        ax.set_xlim(n+.5,.5)
        ax.set_xlabel("Within-panel rank (1 = highest)")
        ax.set_title(f"{chr(100+i)}   Binding-only → integrated rank", fontweight="bold", loc="left", pad=12)
        ax.grid(axis="x", color="#DCE5ED", alpha=.8)

    from matplotlib.lines import Line2D
    fig.legend(handles=[
        Line2D([0], [0], marker="o", ls="none", markerfacecolor="white", markeredgecolor=COLORS["navy"], label="Binding-only rank"),
        Line2D([0], [0], marker="D", ls="none", color=COLORS["navy"], label="Integrated rank"),
        Line2D([0], [0], color=COLORS["teal"], lw=5, label="Muricatacin"),
        Line2D([0], [0], color=COLORS["gold"], lw=5, label="Annomuricin C"),
        Line2D([0], [0], color=COLORS["red"], lw=5, label="Annopentocin A"),
    ], loc="lower center", bbox_to_anchor=(.50,.012), ncol=5, frameon=False, fontsize=9)
    save(fig, out / "Figure_2_internal_rank_shifts")


def figure4(s13b, s13c, s14a, out):
    style()
    fig, axs = plt.subplots(2, 2, figsize=(15.6, 10.7))
    fig.subplots_adjust(top=.84, left=.11, right=.96, bottom=.10, wspace=.36, hspace=.46)
    fig.suptitle("External ChEMBL validation: performance and domain contribution", fontsize=16, fontweight="bold", y=.98)

    # (a): restore the original Figure 4's three-metric panel and its order.
    # Individual ROC-AUC intervals remain reported in OR2 S13B and Figure 4d.
    ax = axs[0, 0]
    row = s13b[(s13b.section=="primary_performance") & (s13b.score_implementation=="integrated_gm3")]
    assert len(row)==1
    rec=row.iloc[0]
    labels=["ROC-AUC", "PR-AUC", "BEDROC (α = 20)"]
    vals=[float(rec.roc_auc),float(rec.pr_auc),float(rec.bedroc_alpha20)]
    yy=np.arange(3)
    ax.barh(yy,vals,color=COLORS["teal"],height=.66)
    ax.set_yticks(yy);ax.set_yticklabels(labels);ax.invert_yaxis()
    ax.set_xlim(0,1.03);ax.set_xlabel("Performance")
    ax.set_title(f"a   Primary activity/status benchmark (188 records)\n"
                 f"EF@1% = {rec.ef_1pct:.2f}  |  EF@5% = {rec.ef_5pct:.2f}",
                 loc="left",fontweight="bold",pad=12)
    for y,v in zip(yy,vals):ax.text(v+.014,y,f"{v:.3f}",va="center",fontsize=9,fontweight="bold")
    ax.grid(axis="x", alpha=.16)

    # (b): task-dependent performance from explicitly stated A-versus-C and A-versus-B rows.
    ax=axs[0,1]
    tasks = ["A_vs_C_active_favorable_vs_weak_inactive_favorable", "A_vs_B_active_favorable_vs_active_serious_warning"]
    keys2=["binding_only","adme_only","liability_only","binding_adme_gm","integrated_gm3","qed"]
    labels2=["Binding only","ADME only","Structure-derived liability","Binding + ADME","Integrated (3 domains)","QED"]
    arr=np.zeros((len(keys2),2))
    for j,t in enumerate(tasks):
        for i,k in enumerate(keys2):
            row=s13c[(s13c.contrast==t)&(s13c.analysis_type=="metrics")&(s13c.score_implementation==k)]
            assert len(row)==1,(t,k)
            arr[i,j]=float(row.iloc[0].roc_auc)
    cmap=mcolors.LinearSegmentedColormap.from_list("valid",["#F5EDE3","#9ABFC8","#087E8B"])
    ax.imshow(arr,cmap=cmap,vmin=.45,vmax=1.0,aspect="auto")
    ax.set_xticks([0,1]);ax.set_xticklabels(["A vs C\nActivity","A vs B\nWarning status"])
    ax.set_yticks(range(len(keys2)));ax.set_yticklabels(labels2)
    for (i,j),v in np.ndenumerate(arr):
        ax.text(j,i,f"{v:.3f}",ha="center",va="center",fontsize=9.5,fontweight="bold",color="white" if v>.80 else COLORS["navy"])
    ax.set_title("b   Domain information varies by task",loc="left",fontweight="bold",pad=12)

    # (c): equal negative-class group weighting (B and C), weighted ROC-AUC only.
    ax=axs[1,0]
    balanced=s13c[(s13c.analysis_type=="weighted_metrics") & (s13c.contrast=="A_vs_B_plus_C_class_balanced")]
    assert len(balanced)>=6,[(c,n) for c,n in s13c.groupby(["contrast","analysis_type"]).size().items()]
    order=["binding_only","adme_only","liability_only","binding_adme_gm","integrated_gm3","qed"]
    pts=[]
    for k in order:
        row=balanced[balanced.score_implementation==k]
        assert len(row)==1,(k,len(row))
        pts.append(float(row.iloc[0].weighted_roc_auc))
    palette=[COLORS["navy"],COLORS["gold"],"#9BACBA",COLORS["navy"],COLORS["teal"],COLORS["grey"]]
    ax.barh(range(6),pts,height=.65,color=palette)
    ax.set_yticks(range(6));ax.set_yticklabels(labels2);ax.invert_yaxis()
    ax.axvline(.5, color="#7D8B92",ls="--",lw=1)
    ax.set_xlim(0,.95);ax.set_xlabel("Class-balanced weighted ROC-AUC")
    ax.set_title("c   Balanced warning/activity sensitivity",loc="left",fontweight="bold",pad=12)
    for y,v in enumerate(pts):ax.text(v+.015,y,f"{v:.3f}",va="center",fontsize=9)
    ax.grid(axis="x",alpha=.16)

    # (d): shared-descriptor comparator analysis with new independent CIs.
    ax=axs[1,1]
    pretty={"Descriptor-compatible SWAN variant":"SWAN-compatible",
            "CNS-MPO":"CNS-MPO proxy", "LE–QED composite proxy":"LE–QED proxy",
            "QED":"QED", "QEPPI":"QEPPI proxy"}
    # Fixed source-method order from original figure: SWAN, CNS, LE–QED, QED, QEPPI.
    desired=["Descriptor-compatible SWAN variant","CNS-MPO","LE–QED composite proxy","QED","QEPPI"]
    df=s14a.set_index("Framework").loc[desired].reset_index()
    assert df.Framework.tolist()==desired
    vals=df["ROC-AUC"].to_numpy(float)
    lows=df["ci_lower"].to_numpy(float); highs=df["ci_upper"].to_numpy(float)
    cols=[COLORS["teal"] if x=="Descriptor-compatible SWAN variant" else COLORS["grey"] for x in df.Framework]
    yy=np.arange(len(df))
    ax.barh(yy,vals,color=cols,height=.65)
    ax.errorbar(vals,yy,xerr=[vals-lows,highs-vals],fmt="none",ecolor="#263441",capsize=3,lw=1.1)
    ax.set_yticks(yy);ax.set_yticklabels([pretty[x] for x in df.Framework]);ax.invert_yaxis()
    ax.set_xlim(0,.72);ax.axvline(.5,color="#7D8B92",ls="--",lw=1)
    ax.set_xlabel("ROC-AUC (95% stratified bootstrap CI)")
    ax.set_title("d   Descriptor-compatible comparator cohort (3,980)",loc="left",fontweight="bold",pad=12)
    for y,v in enumerate(vals):
        ax.text(.024,y,f"{v:.3f}",ha="left",va="center",fontsize=9,
                fontweight="bold",color="white" if y==0 else COLORS["navy"])
    ax.grid(axis="x",alpha=.16)

    fig.text(.51,.028,"A: active, favorable-status  |  B: active, serious-warning  |  C: weak/inactive, favorable-status",ha="center",fontsize=10,color="#405467")
    save(fig,out / "Figure_4_external_validation")


if __name__ == "__main__":
    if len(sys.argv)!=3:raise SystemExit("Usage: python generate_swan_figures.py OR2.zip output_directory")
    output=Path(sys.argv[2]);output.mkdir(exist_ok=True,parents=True)
    with zipfile.ZipFile(sys.argv[1]) as z:
        s8=load(z,"Table_S8A_internal_final_SWAN_scores.csv")
        s13b=load(z,"Table_S13B_ChEMBL_activity_status_performance.csv")
        s13c=load(z,"Table_S13C_ChEMBL_domain_contribution.csv")
        s14a=load(z,"Table_S14A_MPO_comparator_metrics.csv")
    figure2(s8,output)
    figure4(s13b,s13c,s14a,output)
    print("Generated four publication figures in",output)
