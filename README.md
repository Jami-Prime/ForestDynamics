# ForestDynamics

**Spatiotemporal Correlation Analysis of Climate Variables and Satellite-Derived NDVI in Hongcheon, South Korea**

## 1. Introduction

This project explores the spatial and temporal relationships between monthly mean temperature, monthly cumulative precipitation, and the Normalized Difference Vegetation Index (NDVI) in Hongcheon-gun, Gangwon State, South Korea.

- Spatial analysis zones were constructed from the Korea Forest Service's Forest Type Map.
- Climate variables were obtained from ERA5-Land, and NDVI was calculated from Sentinel-2 imagery using Google Earth Engine (GEE).
- Raster calculations were performed on GEE rather than by downloading complete raster datasets for local processing. Zonal statistics were exported and integrated into tabular datasets.
- The analysis includes spatial preprocessing, climate–vegetation data integration, descriptive statistics, joint relative frequency distributions, and Pearson correlation analysis.

**Scope:** This is exploratory analysis. The reported correlations do not establish causal effects or support predictions of future vegetation conditions.

## 2. Project Summary

| Item | Description |
|---|---|
| Study Area | Hongcheon-gun, Gangwon State, South Korea |
| Study Period | 2017–2025 (June–August) |
| Unit of Observation | Spatial zone × year × month |
| Spatial Zones | 2,005 |
| Total Possible Observations | 54,135 |
| Observations Included in Statistical Analysis | 50,771 |
| Observations Meeting the 80% NDVI Coverage Criterion | 46,048 |
| Main Tools | QGIS, Google Earth Engine, Python, pandas, Excel |
| Main Variables | Temperature, precipitation, NDVI |

> **Dataset distinction:** The 50,771 observations used in the reported statistical analysis and the 46,048 observations meeting the 80% NDVI coverage criterion refer to different datasets. Workbook labels such as `원자료` and `정제자료` must not be interpreted as a simple before/after filtering relationship without checking the underlying sheets.

## 3. Data Sources

| Dataset | Source | Purpose |
|---|---|---|
| Forest Type Map | Korea Forest Service (`51720.shp`) | Construction of spatial analysis units |
| Temperature and Precipitation | ECMWF ERA5-Land Daily Aggregated | Extraction of climate variables |
| Satellite Imagery | Sentinel-2 Surface Reflectance Harmonized | NDVI computation |

### 3.1 Climate Data

- **Monthly mean temperature (°C):** Daily mean 2 m air temperature, averaged by month and converted from Kelvin to Celsius.
- **Monthly cumulative precipitation (mm):** Daily precipitation accumulated within each month and converted from meters to millimeters.

The term *2 m air temperature* refers to measurement height above the surface, not a 2 m spatial resolution. ERA5-Land provides reanalysis estimates, not direct weather-station measurements within each forest zone.

### 3.2 Forest Spatial Data

The original Forest Type Map was obtained from the Korea Forest Service's spatial data distribution service.

> **Verification required:** Confirm the source dataset version, acquisition date, and redistribution rights for both original and derived spatial datasets before public release.

## 4. Construction of Spatial Analysis Units

The original forest boundary data (`51720.shp`) were processed in the EPSG:5179 projected coordinate reference system using a 1 km grid.

### 4.1 Processing Steps

1. Create a 1 km × 1 km grid with boundaries aligned to integer multiples of 1,000 m in the projected coordinate system.
2. Clip the original forest polygons to the grid.
3. Combine polygon fragments belonging to the same grid cell.
4. Assign each analysis zone a unique identifier (`구역_ID`).
5. Save the spatial units as a GeoPackage (`.gpkg`).
6. Inspect the resulting zones in QGIS.

The grid alignment is intended to preserve consistent cell positions across runs.

### 4.2 Spatial Validation Results

| Validation Metric | Result |
|---|---:|
| Original Features | 76,479 |
| Generated Spatial Zones | 2,005 |
| Total Input Area | 1,525,798,527.223 m² |
| Total Output Area | 1,525,798,527.213 m² |
| Duplicate Zone IDs | 0 |
| Invalid Output Geometries | 0 |

Validation results were recorded using the generated GeoPackage and `split_report.json`.

### 4.3 Forest Classification

The spatial processing report records:

```json
{"classification_filter": "none; all original classes retained"}
```

Therefore, the derived analysis units are **not restricted to a particular forest species or vegetation classification**. A forest-cover-specific study would require additional classification filtering.

### 4.4 QGIS Project Setup

The QGIS project references its GeoPackage with the relative layer path:

```text
./hongcheon_split_1km.gpkg|layername=forest_split_1km
```

Keep the `.qgz` project and referenced `.gpkg` file in the same directory if this relative reference is used.

## 5. Climate Raster Processing

ERA5-Land temperature and precipitation variables were aggregated at the **spatial zone × year × month** level.

### 5.1 Variables

| Variable | Processing | Unit |
|---|---|---|
| Monthly Mean Temperature | Average daily 2 m air temperature over the month; convert Kelvin to Celsius | °C |
| Monthly Cumulative Precipitation | Sum daily precipitation over the month; convert meters to millimeters | mm |

### 5.2 Spatial Aggregation

ERA5-Land cells do not necessarily align with the 1 km forest analysis units. The documented aggregation procedure uses overlap-area proportions between raster cells and analysis zones rather than assigning a single raster cell value to an entire zone.

### 5.3 Precipitation Correction

Small negative daily precipitation values were reportedly corrected to zero during processing.

> **Verification required:** Confirm whether the intermediate climate workbook (`gee데이터.xlsx`) was saved before or after the final precipitation correction. Reloading that workbook alone may not reproduce the corrected final climate dataset exactly.

## 6. Sentinel-2 NDVI Processing and Data Integration

### 6.1 NDVI Configuration

| Parameter | Configuration |
|---|---|
| Image Collection | `COPERNICUS/S2_SR_HARMONIZED` |
| Study Years | 2017–2025 |
| Months | June, July, August |
| Red Band | B4 |
| Near-Infrared Band | B8 |
| Accepted SCL Classes | 4 (vegetation), 5 (non-vegetated surfaces), 6 (water) |
| Analysis CRS | EPSG:32652 |
| Analysis Resolution | 10 m |
| Minimum Valid Observations | 1 |
| NDVI Coverage Threshold | 80% |
| Processing Batch Size | 50 spatial zones |

NDVI was calculated as:

$$
\mathrm{NDVI} = \frac{B8 - B4}{B8 + B4}
$$

### 6.2 Processing Steps

1. Access Sentinel-2 surface reflectance imagery through Google Earth Engine.
2. Select B4 and B8 and calculate NDVI.
3. Apply the Scene Classification Layer (SCL) mask using the accepted classes.
4. Compute monthly mean NDVI for each pixel.
5. Count valid observations.
6. Use `reduceRegions()` to calculate zonal NDVI statistics, including area-weighted statistics as described in the processing workflow.
7. Calculate valid-area coverage and observation-quality statistics.
8. Cache zonal results in CSV files.
9. Join monthly NDVI statistics with climate observations using zone ID, year, and month.

Raster processing takes place on the GEE server; the workflow does not require downloading the full satellite image dataset to a local computer. Invalid observations remain missing rather than being replaced with zero.

### 6.3 Generated DataFrames

| DataFrame | Contents |
|---|---|
| `ndvi_df` | Monthly NDVI statistics and quality metrics |
| `combined_df` | Combined temperature, precipitation, and NDVI observations |
| `analysis_df` | Observations meeting the configured NDVI and climate-data availability requirements |

The documented conditions for `analysis_df` are:

- Monthly NDVI is present.
- Valid NDVI area is at least 80%.
- Monthly mean temperature is available.
- Monthly cumulative precipitation is available.

> The NDVI coverage threshold is configurable, and it was not uniformly applied to every historical/intermediate dataset. Do not assume that every dataset described in this repository uses an identical filter.

### 6.4 Backups and Excel Export

The Colab workflow creates in-memory copies:

- `combined_df_backup`
- `analysis_df_backup`

The documented export file is `홍천_기온_강수_NDVI_병합완료.xlsx`.

| Excel Sheet | Source |
|---|---|
| `전체자료` | `combined_df` |
| `분석자료` | `analysis_df` |

Excel export uses `pandas.ExcelWriter` with the `openpyxl` engine. Formatting includes a frozen header row, autofilter, and adjusted column widths.

## 7. Statistical Analysis

The statistical workbook documents the research background, dataset, descriptive statistics, scatterplots, Pearson correlations, joint relative frequency distributions, interpretation, and methodological limitations.

### 7.1 Dataset Used

The reported statistical analysis uses **50,771 observations** from the workbook's `정제자료` sheet. This must be distinguished from the **46,048 observations** that meet the 80% NDVI coverage criterion.

### 7.2 Pearson Correlation Coefficients

| Variable Pair | Pearson's r |
|---|---:|
| Monthly Mean Temperature – NDVI | -0.1656 |
| Monthly Cumulative Precipitation – NDVI | -0.2066 |
| Monthly Mean Temperature – Precipitation | +0.2313 |

### 7.3 Monthly Temperature–NDVI Correlations

| Month | Pearson's r |
|---|---:|
| June | -0.2370 |
| July | +0.1510 |
| August | -0.0115 |

Temperature–NDVI correlations differ across the summer months. A pooled summer correlation should not be assumed to describe each individual month.

**Interpretation limitation:** Correlation does not establish causation, forest mortality, or a forecast of vegetation decline.

### 7.4 Joint Relative Frequency Distribution

Temperature, precipitation, and NDVI were each divided into three intervals, creating **3 × 3 × 3 = 27** possible combinations. The resulting joint relative frequency distribution describes how observed climate and vegetation conditions are distributed across these combinations.

Results depend on the chosen interval boundaries and should be interpreted as exploratory descriptive statistics.

## 8. Repository Organization

The repository is intended to separate spatial inputs, processing scripts, intermediate data, outputs, and documentation. The final directory layout and availability of individual files should be checked against the actual repository.

### Publication Notes

- Keep the QGIS project and referenced GeoPackage in the same directory when using relative paths.
- Remove personal absolute paths from `split_report.json` and other published metadata.
- Rename personally identifying filenames and inspect embedded document metadata before publication.
- Confirm redistribution permissions for original and derived forest spatial data.
- Full raw Sentinel-2 imagery is not necessary in the repository because raster calculations are performed remotely on GEE.

## 9. Environment and Reproducibility

### 9.1 Software and Dependencies

- Python, including `pandas` and the Excel export engine `openpyxl`
- Google Earth Engine and a properly authenticated GEE project
- Google Colab for the documented notebook workflow (`google.colab` is provided in Colab)
- `geopandas` when reading GeoPackage geometry directly into a GeoDataFrame
- QGIS for spatial data inspection

Python standard-library modules such as `json`, `time`, `pathlib`, and `hashlib` do not require separate installation. An exact, validated dependency lockfile is not documented here.

### 9.2 Partial Reproduction Workflow

1. Install the required Python packages in Google Colab.
2. Authenticate and initialize the Google Earth Engine project.
3. Read `hongcheon_split_1km.gpkg` into the `zones` GeoDataFrame.
4. Prepare the ERA5-Land climate DataFrame (`weather_df`).
5. Execute the NDVI collection and data integration scripts.
6. Export the resulting tables to Excel.

Before loading a saved climate workbook using `pandas.read_excel()`, verify its worksheet name, column names, and precipitation-correction status.

### 9.3 Current Reproducibility Limitations

The available NDVI processing script assumes that `zones` and `weather_df` have already been initialized. The full original spatial-zone generation procedure and all ERA5-Land acquisition/correction steps are not included in the NDVI script itself.

**A one-command, end-to-end reproduction of the entire analysis is not yet established.** The current documentation describes outputs and a partial execution workflow.

## 10. Limitations and Future Work

### 10.1 Current Limitations

- **Geographical scope:** Hongcheon-gun, South Korea.
- **Temporal scope:** June–August observations for 2017–2025.
- **Satellite observation quality:** Clouds, shadows, and other acquisition conditions can reduce valid NDVI coverage.
- **Spatial resolution mismatch:** Sentinel-2 and ERA5-Land have substantially different spatial resolutions; multiple forest zones may share climate information from the same ERA5-Land cell.
- **Spatial and temporal dependence:** Repeated measurements of a zone and observations from neighboring zones are not necessarily statistically independent.
- **Forest classification:** The preprocessing retained all original classifications rather than restricting analysis to specific forest-cover classes.
- **Variables not explicitly modeled:** Elevation, forest species, soil properties, antecedent precipitation, and climate–vegetation time lags.

### 10.2 Potential Future Work

- Sensitivity analysis across NDVI coverage thresholds.
- Time-lagged analysis of climate–vegetation relationships.
- Inclusion of additional environmental variables.
- Explicit modeling of spatial and temporal dependence.
- Predictive modeling of vegetation conditions.
- Time-ordered validation to reduce temporal information leakage.

These are **planned directions, not completed results**.

## 11. Raw Forest Inventory Data

| Item | Description |
|---|---|
| Provider | Korea Forest Service |
| Dataset | Forest Type Map (1:5,000) |
| Region | Hongcheon-gun, Gangwon State, South Korea |
| Original Filename | `51720.shp` |
| Coordinate Reference System | EPSG:5179 |
| Original Polygons | 76,479 |

The original shapefile was obtained from the Korea Forest Service's spatial data distribution service. It has not been included here because redistribution permission has not been confirmed. Permissions for distributing derived spatial datasets also require confirmation.

Spatial preprocessing results are recorded in `data/metadata/split_report.json`, including processing options, source/output feature counts, geometry validation, and area consistency.

## 12. Project Status

**Current status: Exploratory data analysis; further validation and development are needed.**

This repository documents spatial preprocessing, Sentinel-2 NDVI processing, climate-data integration, initial statistical analysis, and identified methodological limitations. Future development will focus on reproducibility, data-quality validation, and more advanced spatiotemporal modeling.

The repository serves as a record of an undergraduate project's implemented methods, remaining limitations, and planned improvements.
