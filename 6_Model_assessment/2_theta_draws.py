# --- REQUIREMENTS ---
# - fraction1: DataFrame with columns:
#     'TotalPM25' (float, µg/m3),
#     'TotalPop'  (float, persons),
#     'area_fraction' (dict or JSON string like "{'USA':0.4,...}")
# - NCDLRI_Total: dict {country: SUM of NCD+LRI deaths (≥25y) in that country}
#
# This code:
#   * draws theta from GEMM uncertainty (Normal(theta_hat, SE^2))
#   * computes baseline mortality per country under each theta
#   * allocates to cells
#   * computes linearized mort_per_con per theta
#   * stores each theta's dict-per-row in new columns mort_per_con_theta_XXX

import json
import numpy as np
import pandas as pd
from tqdm import tqdm
import geopandas as gpd


with open("NCDLRI_Total_gtap.json",'r') as load_f: # ../2_Concentration_Factors/
    NCDLRI_Total = json.load(load_f)
countries = list(NCDLRI_Total.keys())


fraction = pd.read_csv('comparison_gtap_new/MortPerCon_gtap.csv')

A = ['road','rcor','agr','ene','ind','nrtr','rcoc','rcoo','shp','slv','wst']

shp = pd.read_csv('comparison_gtap_new/Production_concentrations/'+str(countries[0])+'.csv',header=0)

for country in tqdm(countries[1:]):
    read_shp = pd.read_csv('comparison_gtap_new/Production_concentrations/'+str(country)+'.csv',header=0)
    shp += read_shp

production_con_list = list(shp[A].sum(axis=1))

bio_concentration = gpd.read_file("output/output_wholeworld/wholeworld_bio.shp")

bio_con_list = list(bio_concentration['TotalPM25'])

total_con = [production_con_list[i] + bio_con_list[i] for i in range(len(bio_con_list))]


fraction['TotalPM25'] = total_con


fraction1 = fraction[['TotalPM25','TotalPop','area_fraction']]



# ---------------- GEMM params (NCD+LRI, age ≥25; Table S3, Compound Symmetry) ----------------
THETA_HAT = 0.1430
SE_THETA  = 0.01807
ALPHA, MU, V = 1.6, 15.5, 36.8
CF = 2.4  # µg/m3

def sample_thetas(n_draws=500, seed=42, theta_hat=THETA_HAT, se_theta=SE_THETA):
    rng = np.random.default_rng(seed)
    return rng.normal(theta_hat, se_theta, size=n_draws)

# Scalar GEMM RR for completeness (we'll vectorize below)
def hazard_ratio(theta, alpha, mu, v, concentration):
    z = (concentration - CF) if (concentration - CF) > 0 else 0.0
    numerator = theta * np.log(z / alpha + 1.0)
    denominator = 1.0 + np.exp(-(z - mu) / v)
    return np.exp(numerator / denominator)

# ---------------- PREP: copy df and ensure area_fraction is dict ----------------
# fraction1 = fraction1.copy(deep=True)  # avoid SettingWithCopyWarning
if not isinstance(fraction1['area_fraction'].iloc[0], dict):
    fraction1['area_fraction'] = fraction1['area_fraction'].apply(
        lambda s: json.loads(s.replace("'", '"')) if isinstance(s, str) else s
    )

# Country universe (use keys from your totals to stay consistent)
Countries = list(NCDLRI_Total.keys())

# Shorthand arrays
C_total = fraction1['TotalPM25'].to_numpy(dtype=float)
Pop     = fraction1['TotalPop'].to_numpy(dtype=float)
N       = len(fraction1)

# ---------------- SPEED TRICKS: precompute pieces that don't depend on theta ----------------
# 1) Precompute logistic/log parts once (so each theta draw is just exp(theta * T))
z     = np.maximum(0.0, C_total - CF)
omega = 1.0 / (1.0 + np.exp(-(z - MU) / V))
T     = np.log1p(z / ALPHA) * omega  # GEMM's T(z), shape (N,)

# 2) Per-country weights:
#    Wsum[c] = Σ_i frac_ic * Pop_i       (denominator for baseline allocation)
#    rows_weights_by_country[c] = list of (i, w_i) with w_i = frac_ic * Pop_i
Wsum = {c: 0.0 for c in Countries}
rows_weights_by_country = {c: [] for c in Countries}

for i, afrac in enumerate(fraction1['area_fraction']):
    pi = Pop[i]
    for c, frac in afrac.items():
        w = frac * pi
        if c in Wsum:
            Wsum[c] += w
            rows_weights_by_country[c].append((i, w))

# Guard zero denominators
for c in Countries:
    if Wsum[c] <= 0:
        Wsum[c] = 1.0  # to avoid division by zero; that country will effectively contribute 0

# ---------------- MAIN: loop over theta draws and create mort_per_con_theta_* columns --------
thetas = sample_thetas(n_draws=500, seed=42)  # adjust 200–1000 as you like

# We will build each column off-DataFrame (list of dicts), then attach once — fastest & no warnings
for d_idx, theta in enumerate(tqdm(thetas)):
    colname = f"mort_per_con_theta_{d_idx:03d}"

    # 1) RR_i under this theta; then your linearized ratio_i = 1 - 1/RR_i
    RR = np.exp(theta * T)               # (N,)
    RR = np.maximum(RR, 1.0)             # numeric guard
    ratio = 1.0 - 1.0 / RR               # (N,)
    # ratio / concentration (guard zeros)
    ratio_over_C = np.zeros(N, dtype=float)
    pos = C_total > 0
    ratio_over_C[pos] = ratio[pos] / C_total[pos]   # (N,)

    # 2) Baseline per country for this theta (Hbar, then baseline = NCDLRI_Total / Hbar)
    baseline_country = {}
    for c in Countries:
        lst = rows_weights_by_country[c]
        if not lst:
            baseline_country[c] = 0.0
            continue
        idxs, wts = zip(*lst)
        idxs = np.fromiter(idxs, dtype=int)
        wts  = np.fromiter(wts,  dtype=float)
        Hsum_c = np.dot(RR[idxs], wts)   # Σ_i RR_i * (frac_ic * Pop_i)
        Hbar_c = Hsum_c / Wsum[c]
        baseline_country[c] = (NCDLRI_Total[c] / Hbar_c) if Hbar_c > 0 else 0.0

    # 3) Precompute country scalar S_c = baseline_c / Wsum_c (used for each cell)
    S = {c: (baseline_country[c] / Wsum[c]) for c in Countries}

    # 4) Build this draw's column: list of dicts (one per row)
    col_vals = []
    for i, afrac in enumerate(fraction1['area_fraction']):
        r_over_C = float(ratio_over_C[i])
        if r_over_C == 0.0:
            col_vals.append({})  # nothing from this cell
            continue
        out_d = {}
        pi = Pop[i]
        for c, frac in afrac.items():
            if c in S:
                val = r_over_C * (frac * pi) * S[c]
                if val != 0.0:
                    out_d[c] = val
        col_vals.append(out_d)

    # 5) Attach column safely (no chained assignment)
    fraction1.loc[:, colname] = pd.Series(col_vals, index=fraction1.index, dtype=object)

# ---- DONE ----
# fraction1 now contains mort_per_con_theta_000 ... mort_per_con_theta_(n-1),
# each cell is a dict {country: value}, following YOUR linear method with θ-draws.

fraction1.to_csv('comparison_gtap/theta_draws.csv')
