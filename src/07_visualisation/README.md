
These scripts should be run **after** completing all steps above.

---

## Visualization Workflow

### `coexpression_heatmaps.py`

- Heatmap of Topological Overlap Matrix (TOM)
- Hierarchical clustering of co-expressed genes
- Used to assess global network structure

---

### `coexpression_network_plots.py`

- Force-directed co-expression networks
- Module-colored nodes
- Central highlighting of CYCLOPS
- High-resolution PNG and SVG figures suitable for publication

---

## Notes for Reproducibility

- All correlation thresholds are explicitly defined in scripts
- No proprietary software is required
- Network plots are fully reproducible from the exported matrices
- Exploratory parameter tuning was performed in notebooks (not included)

---

## Relationship to Manuscript

This analysis supports:
- Identification of CYCLOPS-associated gene modules
- Functional interpretation of transcriptional regulation
- Network figures presented in the Results section

Each figure can be traced to a specific script in this directory
or the visualization directory.
