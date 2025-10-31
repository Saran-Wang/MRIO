# 🌍 Analysis Code for *“International (Fair) Trade in Air-Quality-Related Mortality”*

This repository contains the full Python workflow used in the paper **“International (Fair) Trade in Air-Quality-Related Mortality.”**  
The project integrates the **InMAP atmospheric model** with **multi-regional input–output (MRIO)** frameworks (GTAP and EORA datasets) to quantify **country-level production- and consumption-based PM₂.₅ concentrations, health impacts, and economic externalities** associated with international trade.

---

## ⚙️ Environment Setup

The computational environment for InMAP simulations can be set up following the official repository:  
👉 [https://github.com/spatialmodel/inmap](https://github.com/spatialmodel/inmap)

All analysis codes here are written in **Python**, with required packages listed at the beginning of each notebook.  
The project assumes that InMAP simulations have already been run and the resulting **country-specific concentration outputs** are available as inputs for subsequent analysis.

---

## 🧱 Repository Overview

The repository is structured into six main folders, corresponding to the major stages of the analysis pipeline:

| Folder | Purpose |
|:-------|:---------|
| `1_Country_Emission` | Prepare inputs for InMAP simulations and generate country-specific emission maps. |
| `2_Concentration_Factors` | Derive consumption-based concentrations from production-based simulation outputs. |
| `3_Mortality` | Estimate PM₂.₅-related premature deaths based on simulated concentrations. |
| `4_Result_Interpretation` | Analyze trade-related inequalities and economic externalities in health impacts. |
| `5_Plot_generation` | Generate all figures presented in the main text and Supplementary Information. |
| `6_Model_assessment` | Perform model validation and Monte Carlo–based uncertainty analysis. |

---

## 📁 Folder Descriptions

### 🗂️ Folder 1 — `1_Country_Emission`
**Purpose:** Prepare input files for InMAP simulations and quantify **production-based concentrations** caused by each country’s trade-related anthropogenic activities.

**Key Notebooks:**
- **1_MRIOTable-woANT_USR.ipynb**  
  Processes GTAP or EORA raw MRIO data. Produces Leontief inverse and sectoral output matrices following the methods described in the paper.  
  *Input:* GTAP/EORA datasets  
  *Output:* Leontief inverse, total output matrix  

- **2_geoJson.ipynb**  
  Generates country-specific GeoJSON masks for InMAP simulations.  
  *Input:* Global shapefile  
  *Output:* JSON geometries for each country consistent with GTAP/EORA country codes  

- **3_processCEDS.ipynb**  
  Converts daily **CEDS emissions** into annual mean gridded NetCDF files for use in InMAP.  
  *Output:* Annual average anthropogenic emissions (NetCDF)  

**Output of Folder 1 (after InMAP simulations):**  
High-resolution **production-based PM₂.₅ concentration fields** simulated by InMAP.

---

### 🗂️ Folder 2 — `2_Concentration_Factors`
**Purpose:** Use InMAP outputs and MRIO tables to derive **consumption-based PM₂.₅ concentrations** via trade linkages.

**Key Notebooks:**
- **1_Total_output_SectorCountry-woANTUSR.ipynb**  
  Maps industrial sectors to economic sectors and calculates total sectoral output by country.  

- **2_Total_output_SectorSector-woANTUSR.ipynb**  
  Constructs the sector–sector output matrix as shown in *Supplementary Fig. S16*.  

- **3_Concentration_factors.ipynb**  
  Computes PM₂.₅ concentration factors (μg/m³ per unit economic output) for each country–sector pair.  
  *Input:* Production-based concentrations and total output  
  *Output:* Concentration factors  

- **4_Consumption_concentrations.py**  
  Combines MRIO trade linkages with concentration factors to calculate **consumption-based concentrations** for all countries.  

**Output of Folder 2:**  
High-resolution **consumption-based concentration fields** for each country.

---

### 🗂️ Folder 3 — `3_Mortality`
**Purpose:** Quantify **PM₂.₅-related premature deaths** attributable to both production and consumption activities.

**Key Notebooks:**
- **1_NCDLRI.ipynb**  
  Calculates mortality from *Non-Communicable Diseases* (NCD) and *Lower Respiratory Infections* (LRI) per country using Global Burden of Disease (GBD) data.  

- **2_CountryClassify.ipynb**  
  Implements *Algorithm S1* to map each InMAP grid cell to GTAP/EORA countries based on geographic location.  

- **3_Baseline.ipynb**  
  Implements *Algorithm S2* to estimate counterfactual baseline mortality (i.e., mortality in the absence of air pollution).  

- **4_MortPerConcentration.ipynb**  
  Calculates the mortality rate attributable to PM₂.₅ per unit concentration in each country–cell pair.  

- **5_concentrations_sectors.ipynb**  
  Aggregates simulated concentrations by industrial sector for downstream mortality calculations.  

- **6_Excess_Mort_Consumption.ipynb**  
  Implements *Algorithm S3* to calculate **excess mortality due to consumption** behavior by country.  

- **7_Excess_Mort_Production.ipynb**  
  Implements *Algorithm S3* to calculate **excess mortality due to production** of goods and services.  

- **8_mortality_sectors.ipynb**  
  Extends mortality estimation to the sectoral level for each country.  

**Output of Folder 3:**  
Country-level and sector-level mortality attributable to PM₂.₅ from both production and consumption perspectives.

---

### 🗂️ Folder 4 — `4_Result_Interpretation`
**Purpose:** Evaluate **economic externalities** and **distributional inequalities** in trade-related air-pollution mortality.

**Key Notebooks:**
- **1_VSL.ipynb**  
  Calculates *Value of Statistical Life (VSL)* using the method of Viscusi & Masterman (Income Elasticities and Global Values of a Statistical Life).  

- **2_PlaywithVSL.ipynb**  
  Assesses global trade-related externalities under three scenarios of VSL equality (“Business as Usual", Global Community”, and Fair Trade in Deaths”).  
  Produces results shown in *Figure 5 (main text)*.  

- **3_Fraction.ipynb**  
  Computes domestic vs. international mortality fractions caused by each country’s consumption and production (used in *Figure 3*).  

- **4_output_fraction.ipynb**  
  Calculates **Total Output Fraction (`Frac_TO_{~m n}`)** for sectoral analysis.  
  <br>

- **5_demand_fraction.ipynb**  
  Computes **Direct and Total Final Demand Fractions (`Frac_DFD_{~m ~n}` and `Frac_TFD_{~m ~n}`)** for sectoral decomposition.  
  <br>

**Output of Folder 4:**  
Country- and sector-level indicators of trade-related mortality externalities and inequality.

---

### 🗂️ Folder 5 — `5_Plot_generation`
**Purpose:** Generate all figures included in the main text and Supplementary Information.  
All plot inputs are available at:  
👉 [https://tinyurl.com/ysyeafv2](https://tinyurl.com/ysyeafv2)

**Key Notebooks:**
- **1_mriomaps_gtap.ipynb** — Generates *Figure 1* and supplementary *S9.csv* (GTAP-based).  
- **1_mriomaps_eora.ipynb** — Generates *Figure S3* and *S10.csv* (EORA counterpart).  
- **2_Merge_bubble_bar.ipynb** — Produces *Figure 2* (and *Figure S6* for EORA).  
- **3_RatioPlot.ipynb** — Produces *Figure 3* (and *Figures S7–S8*).  
- **4_correlation_plot.ipynb** — Produces *Figure 4*, *Figures S11–S12*, and exports *S14.xlsx* summarizing cross-model correlations.  
- **5_VSLPlot.ipynb** — Produces *Figure 5* (and *Figure S13*).  

**Output of Folder 5:**  
All published figures and supporting data visualizations.

---

### 🗂️ Folder 6 — `6_Model_assessment`
**Purpose:** Evaluate model performance and quantify uncertainty in mortality estimates.

**Key Scripts:**
- **1_Measurement_Comparison.ipynb**  
  Compares InMAP-simulated concentrations against ground-based measurements across regions.  
  *Output:* *Figures S1–S2 (Validation)*  

- **2_theta_draws.py**  
  Performs **Monte Carlo sampling (500 draws)** of the GEMM θ parameter to capture uncertainty in concentration–response relationships.  
  - Draws θ from Normal(θ̂, SE²)  
  - Computes baseline mortality per country per draw  
  - Allocates results to grid cells  

- **3_theta_deaths.py**  
  Aggregates deaths per country for each θ draw, yielding uncertainty ranges.  
  *Output:* Datasets *S15.csv* (production-based) and *S16.csv* (consumption-based).  

**Output of Folder 6:**  
Model validation metrics, uncertainty distributions, and supporting figures.

---

## 📊 Input & Output Data

### **Input Files**
All data sources and preprocessing steps are detailed in the *Methods* section of the paper, including:
- GTAP and EORA MRIO datasets  
- CEDS emission inventory  
- GBD mortality database  
- InMAP concentration outputs  

### **Output Files**
All derived datasets (country-level mortality, concentration factors, uncertainty draws, and visualization inputs) are described in the *Data Availability* section of the paper and hosted in the supplementary data repository.

---

## 🧭 Analytical Workflow Summary

1. **Prepare Inputs** → Generate emission and geometry files for InMAP simulations (`Folder 1`).  
2. **Simulate Concentrations** → Run InMAP to obtain production-based PM₂.₅ concentrations.  
3. **Link to Trade Data** → Combine InMAP outputs with MRIO tables to compute consumption-based concentrations (`Folder 2`).  
4. **Estimate Health Impacts** → Apply GEMM model to derive premature deaths (`Folder 3`).  
5. **Analyze Externalities** → Quantify economic inequalities and trade-related effects (`Folder 4`).  
6. **Visualize Results** → Generate figures for the main text and SI (`Folder 5`).  
7. **Validate & Quantify Uncertainty** → Compare with measurements and perform Monte Carlo draws (`Folder 6`).

---

## 🧾 Citation
If you use this repository or its derived data, please cite the original paper:  
> Wang, S. *et al.* “International (Fair) Trade in Air-Quality-Related Mortality.” *[Journal Name, Year, DOI TBD]*.

---

## 👩‍🔬 Contact
For questions or collaboration inquiries, please contact:  
**Shiyuan Wang**  
PhD Candidate, Environmental Engineering  
University of Illinois Urbana–Champaign  
📧 shiyuan8@illinois.edu
