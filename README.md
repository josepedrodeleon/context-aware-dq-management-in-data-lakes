# Context-Aware Data Quality Management in Data Lakes

A proof-of-concept implementation for managing **data quality (DQ)** in a data lake using **context-aware** models. The system uses a graph database (Neo4j) to store metadata about datasets, zones, processes, and DQ models, and links DQ metrics to business context (requirements, rules, user types, and tasks).

## Overview

This repository demonstrates:

- **Zone-based data flow**: Data moves through four zones—**Landing** → **Raw** → **Trusted** → **Refined**—with transformations and DQ checks at each stage.
- **Context models**: Business rules, DQ requirements, user types, and tasks are modeled and linked to DQ dimensions and metrics so quality is evaluated in context.
- **DQ models**: Multiple DQ models (e.g. `dqm1`, `dqm2`, `dqm3`) are defined with dimensions (Accuracy, Completeness, Consistency, Uniqueness, Freshness, Data Volume), factors, metrics, and applied methods—each contextualized by a different context model.
- **Metadata in Neo4j**: Datasets, tables, columns, processes, and DQ measure results are persisted in Neo4j and linked to context and DQ model metadata.

The POC uses **movie data** (TMDB and IMDB title ratings) flowing through the zones, with DQ metrics (e.g. non-null ratios, “no sentinel value” ratios) computed and stored alongside metadata.

## Architecture

```
Landing Zone     →  Raw Zone       →  Trusted Zone    →  Refined Zone
(TMDB, ratings)     (as ingested)     (clean + merge)     (sanitized for ML)
                         ↓                  ↓                    ↓
                    DQ Model 3          DQ Model 2           DQ Model 1
                    (ctxm3)             (ctxm2)              (ctxm1)
```

- **Landing**: Ingests TMDB movie dataset and IMDB title ratings into the Raw zone; runs DQ step using **dqm3** (e.g. completeness on key columns).
- **Trusted**: Cleans TMDB data, merges with ratings; runs DQ step using **dqm2** (completeness, consistency, etc.).
- **Refined**: Sanitizes for ML (fill missing dates/genres/countries with sentinel values); runs DQ step using **dqm1** (stricter completeness including exclusion of sentinel values).

Context models (`ctxm1`, `ctxm2`, `ctxm3`) define business rules, DQ requirements, and tasks; each DQ model is contextualized by one of them and applied to the corresponding zone’s datasets.

## Repository Structure

```
context-aware-dq-management-in-data-lakes-main/
├── README.md
└── poc_implementation/
    ├── poc.ipynb                    # Main notebook: run zone pipelines
    ├── setup_models.cypher          # Neo4j: context models, DQ models, zones
    ├── metadata/
    │   └── metadata_utils.py        # Neo4j helpers: datasets, tables, columns, processes, DQ measures
    ├── zone_processes/
    │   ├── landing_zone.py          # Ingest TMDB + title.ratings → Raw zone
    │   ├── trusted_zone.py          # Clean TMDB, merge with ratings
    │   └── refined_zone.py          # Sanitize for ML (Movies_ML.csv)
    └── data_quality/
        └── metrics.py               # DQ metrics (e.g. ratioNoNulos, ratioNoNulosNiSD)
```

## Prerequisites

- **Python 3** with `pandas`, `numpy`, and `neo4j` driver.
- **Neo4j** (e.g. 4.x/5.x) running locally; default connection in code is `bolt://localhost:7687` with user `neo4j` and password `password`.

## Setup

1. **Install Python dependencies**

   ```bash
   pip install pandas numpy neo4j
   ```

2. **Start Neo4j** and create the graph schema and context/DQ models:

   - Load `poc_implementation/setup_models.cypher` in Neo4j Browser or via `cypher-shell` (or run the statements manually). This creates:
     - Zones: `landing-zone`, `raw-zone`, `trusted-zone`, `refined-zone`
     - Context models (e.g. Application Domain, Business Rules, DQ Requirements, User Types, Tasks, Data Filtering, Data Lineage)
     - DQ models (dimensions, factors, metrics, methods, applied methods) and their links to context models

3. **Prepare input data** (paths used in the notebook):

   - `data/Movies/Landing_Zone/TMDB_movie_dataset_v11.csv`
   - `data/Movies/Landing_Zone/title.ratings.tsv`

   Adjust paths in `poc.ipynb` if your files are elsewhere.

4. **Configure Neo4j** in `metadata/metadata_utils.py` if needed:

   - `uri`, `user`, `password` (defaults: `bolt://localhost:7687`, `neo4j`, `password`).

## Running the POC

1. From the repo root, start Jupyter and open `poc_implementation/poc.ipynb`.
2. Run the cells in order:
   - **Landing zone**: Ingest TMDB and title.ratings into the Raw zone (and run DQ with dqm3).
   - **Trusted zone**: Clean TMDB and merge with ratings (DQ with dqm2).
   - **Refined zone**: Sanitize movies and write `Movies_ML.csv` (DQ with dqm1).

Output files are written under `data/Movies/` (Raw_Zone, Trusted_Zone, Refined_Zone). Metadata and DQ measure results are written to Neo4j.

## Data Quality Module

- **`data_quality/metrics.py`** provides:
  - `ratioNoNulos(dataset, column_name, valores_SD=None)`: percentage of non-null values in a column.
  - `ratioNoNulosNiSD(dataset, column_name, valores_SD)`: percentage of values that are non-null and not in a list of sentinel values (e.g. `"Sin Datos"`, `"1800-01-01"`).

These metrics are used by the zone processes and their results are stored via `metadata_utils.load_metric_metadata()` and linked to applied DQ methods and datasets.

## License

See repository license file if present.
