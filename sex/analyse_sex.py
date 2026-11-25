"""Is research volume (papers, trials) linked to whether a disease mostly affects women or men?

Run from the repo root: python3 -I sex/analyse_sex.py
Inputs: expanded/burden_vs_research_expanded_2021-2025.csv (120 diseases: DALYs, papers, trials),
expanded/papers_cleaned_2021-2025.csv, expanded/trials_title_filtered_2021-2025.csv,
sex/sex_labels.csv (approximate female share of cases, coded by hand).
Outputs (sex/): sex_models_2021-2025.csv, sex_robustness_2021-2025.csv, sex_by_disease_2021-2025.csv,
sex_residuals.png.

Research volume tracks burden, so every model adjusts for log10 DALYs. Main outcome: log10 papers or
trials per year. Main exposure: female share of cases (0-1), reported per +10 percentage points.
"""
import os
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.join(HERE, "..", "expanded")
SEED = 88774815  # drawn from a random number generator
rng = np.random.default_rng(SEED)
N_PERM = 10000
N_NOISE = 2000

d = pd.read_csv(os.path.join(EXP, "burden_vs_research_expanded_2021-2025.csv"))
lab = pd.read_csv(os.path.join(HERE, "sex_labels.csv"))
d = d.merge(lab, on="label", how="left", validate="1:1")
assert d["female_share"].notna().all()
pc = pd.read_csv(os.path.join(EXP, "papers_cleaned_2021-2025.csv")).rename(columns={"disease": "label"})
tc = pd.read_csv(os.path.join(EXP, "trials_title_filtered_2021-2025.csv")).rename(columns={"disease": "label"})
d = d.merge(pc[["label", "papers_cleaned_per_year"]], on="label", how="left")
d = d.merge(tc[["label", "trials_weighted_per_year"]], on="label", how="left")


def sex_class(f):
    if f >= 0.95: return "female-specific"
    if f <= 0.05: return "male-specific"
    if f >= 0.60: return "female-dominant"
    if f <= 0.40: return "male-dominant"
    return "balanced"


d["sex_class"] = d["female_share"].map(sex_class)
d["log_dalys"] = np.log10(d["dalys"])
d["log_papers"] = np.log10(d["papers_per_year"])
d["log_trials"] = np.log10(d["trials_per_year"])
d["log_papers_clean"] = np.log10(d["papers_cleaned_per_year"])
d["log_trials_clean"] = np.log10(d["trials_weighted_per_year"])
d["f10"] = d["female_share"] * 10  # coefficient = change per +10 percentage points
d["group"] = d["group"].replace({"Maternal/neonatal": "MatNeo"})
d["papers_5y"] = (d["papers_per_year"] * 5).round().astype(int)
d["trials_5y"] = (d["trials_per_year"] * 5).round().astype(int)
d["female_dom"] = (d["sex_class"] == "female-dominant").astype(int)
d["male_dom"] = (d["sex_class"] == "male-dominant").astype(int)

nonspec = d[~d["sex_class"].isin(["female-specific", "male-specific"])].copy()
OUT = {"papers": "log_papers", "trials": "log_trials"}
rows = []


def fold(b):  # log10 coefficient -> multiplier
    return 10 ** b


def add(metric, sample, model, term, fit, n, logscale=True, note=""):
    b, se, p = fit.params[term], fit.bse[term], fit.pvalues[term]
    lo, hi = fit.conf_int().loc[term]
    f = fold if logscale else np.exp
    rows.append({"metric": metric, "sample": sample, "model": model, "term": term, "n": n,
                 "coef": round(b, 4), "se": round(se, 4), "p": round(p, 4),
                 "multiplier": round(f(b), 3), "mult_ci_low": round(f(lo), 3), "mult_ci_high": round(f(hi), 3),
                 "note": note})


def ols(formula, data):
    return smf.ols(formula, data).fit(cov_type="HC3")


def perm_p(formula, data, term, strata=None):
    """Permutation p for one term: shuffle female share (within strata if given), refit by least squares."""
    import patsy
    yv, X = patsy.dmatrices(formula, data, return_type="dataframe")
    j = list(X.columns).index(term)
    Xm, yv = X.to_numpy().copy(), yv.to_numpy().ravel()
    obs = np.linalg.lstsq(Xm, yv, rcond=None)[0][j]
    x = Xm[:, j].copy()
    groups = None if strata is None else [np.where(data[strata].to_numpy() == g)[0] for g in data[strata].unique()]
    hits = 0
    for _ in range(N_PERM):
        if groups is None:
            xs = rng.permutation(x)
        else:
            xs = x.copy()
            for idx in groups:
                xs[idx] = rng.permutation(x[idx])
        Xm[:, j] = xs
        if abs(np.linalg.lstsq(Xm, yv, rcond=None)[0][j]) >= abs(obs):
            hits += 1
    return (hits + 1) / (N_PERM + 1)


perms = {}
for metric, y in OUT.items():
    # 1. Main: continuous female share, non-sex-specific diseases
    for name, form in [("DALYs", f"{y} ~ log_dalys + f10"), ("DALYs + group", f"{y} ~ log_dalys + f10 + C(group)")]:
        fit = ols(form, nonspec)
        add(metric, "non-sex-specific", name, "f10", fit, len(nonspec), note="per +10 pp female")
    perms[(metric, "DALYs")] = perm_p(f"{y} ~ log_dalys + f10", nonspec, "f10")
    perms[(metric, "DALYs + group")] = perm_p(f"{y} ~ log_dalys + f10 + C(group)", nonspec, "f10", strata="group")

    # 2. Unadjusted (no DALYs), for reference
    fit = ols(f"{y} ~ f10", nonspec)
    add(metric, "non-sex-specific", "unadjusted", "f10", fit, len(nonspec), note="no burden adjustment")

    # 3. Categories, all 120, balanced = reference
    cat = "C(sex_class, Treatment(reference='balanced'))"
    for name, form in [("DALYs", f"{y} ~ log_dalys + {cat}"), ("DALYs + group", f"{y} ~ log_dalys + {cat} + C(group)")]:
        fit = ols(form, d)
        for t in fit.params.index:
            if t.startswith("C(sex_class"):
                add(metric, "all 120", name, t, fit, len(d), note="vs balanced")
    # female-dominant vs male-dominant directly
    fit = ols(f"{y} ~ log_dalys + female_dom + male_dom", nonspec)
    t = fit.t_test("female_dom - male_dom")
    b = float(np.ravel(t.effect)[0]); se = float(np.ravel(t.sd)[0]); p = float(np.ravel(t.pvalue)[0])
    rows.append({"metric": metric, "sample": "non-sex-specific", "model": "DALYs", "term": "female-dominant minus male-dominant",
                 "n": len(nonspec), "coef": round(b, 4), "se": round(se, 4), "p": round(p, 4),
                 "multiplier": round(10 ** b, 3), "mult_ci_low": round(10 ** (b - 1.96 * se), 3),
                 "mult_ci_high": round(10 ** (b + 1.96 * se), 3), "note": "contrast"})

    # 4. Negative binomial on 5-year counts (log link, so exp(coef))
    cnt = f"{metric}_5y"
    for name, form in [("NB, DALYs", f"{cnt} ~ np.log(dalys) + f10"), ("NB, DALYs + group", f"{cnt} ~ np.log(dalys) + f10 + C(group)")]:
        fit = smf.negativebinomial(form, nonspec).fit(disp=0, maxiter=500)
        add(metric, "non-sex-specific", name, "f10", fit, len(nonspec), logscale=False, note="per +10 pp female")

models = pd.DataFrame(rows)
models["perm_p"] = [perms.get((r.metric, r.model), np.nan) if (r.term == "f10" and r.model in ("DALYs", "DALYs + group"))
                    else np.nan for r in models.itertuples()]
models.to_csv(os.path.join(HERE, "sex_models_2021-2025.csv"), index=False)

# Robustness: main model (DALYs + f10, non-sex-specific) under variations
rob = []


def rob_fit(metric, label, data, y, extra=""):
    fit = ols(f"{y} ~ log_dalys + f10{extra}", data)
    lo, hi = fit.conf_int().loc["f10"]
    rob.append({"metric": metric, "variant": label, "n": len(data), "multiplier": round(10 ** fit.params["f10"], 3),
                "ci_low": round(10 ** lo, 3), "ci_high": round(10 ** hi, 3), "p": round(fit.pvalues["f10"], 4)})


for metric, y in OUT.items():
    yc = {"papers": "log_papers_clean", "trials": "log_trials_clean"}[metric]
    rob_fit(metric, "main", nonspec, y)
    rob_fit(metric, "cleaned counts", nonspec, yc)
    rob_fit(metric, "without original 13", nonspec[~nonspec["original_13"]], y)
    rob_fit(metric, "only high/medium-confidence labels", nonspec[nonspec["confidence"] != "low"], y)
    rob_fit(metric, "only high-confidence labels", nonspec[nonspec["confidence"] == "high"], y)
    rob_fit(metric, "breast cancer included (share 0.99)", d[~d["sex_class"].isin(["male-specific"]) &
                                                          ((d["female_share"] < 0.95) | (d["label"] == "Breast cancer"))], y)
    for g in sorted(nonspec["group"].unique()):
        rob_fit(metric, f"without {g}", nonspec[nonspec["group"] != g], y)
    rob_fit(metric, "NCDs only", nonspec[nonspec["group"] == "NCD"], y)
    rob_fit(metric, "cancers only", nonspec[nonspec["group"] == "Cancer"], y)
    rob_fit(metric, "infectious + NTD only", nonspec[nonspec["group"].isin(["Infectious", "NTD"])], y)
    # robust regression (Huber) to downweight outliers
    hub = smf.rlm(f"{y} ~ log_dalys + f10", nonspec, M=sm.robust.norms.HuberT()).fit()
    lo, hi = hub.conf_int().loc["f10"]
    rob.append({"metric": metric, "variant": "Huber robust regression", "n": len(nonspec),
                "multiplier": round(10 ** hub.params["f10"], 3), "ci_low": round(10 ** lo, 3),
                "ci_high": round(10 ** hi, 3), "p": round(hub.pvalues["f10"], 4)})
    # label error: perturb each female share by noise scaled to label confidence
    sd = nonspec["confidence"].map({"high": 0.03, "medium": 0.07, "low": 0.12}).to_numpy()
    bs, ps = [], []
    work = nonspec.copy()
    for _ in range(N_NOISE):
        work["f10"] = 10 * np.clip(nonspec["female_share"].to_numpy() + rng.normal(0, sd), 0.05, 0.95)
        fit = ols(f"{y} ~ log_dalys + f10", work)
        bs.append(fit.params["f10"]); ps.append(fit.pvalues["f10"])
    bs = np.array(bs)
    rob.append({"metric": metric, "variant": "label noise (2,000 draws): median, 5-95% of estimates", "n": len(nonspec),
                "multiplier": round(10 ** np.median(bs), 3), "ci_low": round(10 ** np.percentile(bs, 5), 3),
                "ci_high": round(10 ** np.percentile(bs, 95), 3), "p": round(float(np.mean(np.array(ps) < 0.05)), 3)})
pd.DataFrame(rob).to_csv(os.path.join(HERE, "sex_robustness_2021-2025.csv"), index=False)

# Per disease: residual from the DALY trend (all 120), so the reader can see which diseases drive it
for metric, y in OUT.items():
    fit = smf.ols(f"{y} ~ log_dalys", d).fit()
    d[f"{metric}_resid_fold"] = (10 ** fit.resid).round(3)  # actual / trend
cols = ["label", "group", "sex_class", "female_share", "confidence", "basis", "dalys", "papers_per_year",
        "trials_per_year", "papers_resid_fold", "trials_resid_fold"]
d[cols].sort_values("female_share").to_csv(os.path.join(HERE, "sex_by_disease_2021-2025.csv"), index=False)

# Group means of residuals by class (geometric means of actual/trend)
summ = d.groupby("sex_class").agg(n=("label", "size"),
                                  papers_vs_trend=("papers_resid_fold", lambda s: round(float(np.exp(np.log(s).mean())), 2)),
                                  trials_vs_trend=("trials_resid_fold", lambda s: round(float(np.exp(np.log(s).mean())), 2)))
print(summ.to_string())
print()
print(models[["metric", "sample", "model", "term", "n", "multiplier", "mult_ci_low", "mult_ci_high", "p", "perm_p"]].to_string())
print()
print(pd.DataFrame(rob).to_string())
summ.to_csv(os.path.join(HERE, "sex_class_summary_2021-2025.csv"))
