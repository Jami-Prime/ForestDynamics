
# ForestDynamics

Spatiotemporal correlation analysis between climate (T, P) and NDVI (satellite) data in Hongcheon, South Korea.

## 1. Introduction

- Monthly mean temperature, monthly cumulative precipitation, and monthly average Normalized Difference Vegetation Index (NDVI) spatial and temporal correlation analysis in Hongcheon-gun, Gangwon State, South Korea.
- Spatial zones were created based on the vector data of the Forest Type Map of the Korea Forest Service.
- Climate data were collected from ERA5-Land, and NDVI data were calculated using Sentinel-2 satellite data through Google Earth Engine (GEE).
- Raster data were not downloaded and analyzed locally, but instead, raster computations were conducted within GEE, and the statistics (zonal statistics) of the raster data were exported, arranged, and integrated into tabular data.
- Spatial data setup, the combination of climate data and vegetation data, descriptive statistics, joint relative frequency tables, and correlation analysis.
- This is an exploratory analysis only, with no causal analysis or future prediction (vegetation).

## 2. Summary

| Item | Description |
|---|---|
| Study Area | Hongcheon-gun, Gangwon State, South Korea |
| Study Period | 2017-2025 (Jun-Aug) |
| Unit of Observation | Zone (space) * Year * Month |
| Total spatial zones | 2,005 |
| Total Possible Observations | 54,135 |
| Observations in "원자료" | 46,048 |
| Observations in "정제자료" | 50,771 |
| Main tools | QGIS, Google Earth Engine, Python, Pandas, Excel |
| Main Variables | Temperature, Precipitation, NDVI |

※ Data Interpretation -The Excel workbook contains two worksheets:

- `원자료`: 46,048 observations
- `정제자료`: 50,771 observations

Note that the `정제자료` worksheet contains more observations than the `원자료` worksheet. Therefore, these two datasets should not be interpreted as the results of a simple filtering process.

Please check the dataset structure and processing criteria before selecting a worksheet for statistical analysis.

## 3. Data Sources

Three basic datasets are used.

| Dataset | Source | Purpose |
|---|---|---|
| Forest Type Map | Korea Forest Service (51720.shp) | spatial analysis unit construction |
| Temperature & Precipitation | ECMWF ERA5-Land Daily Aggregated | extract climate variables |
| Satellite Image | Sentinel-2 Surface Reflectance Harmonized | calculate NDVI |

### Climate Data

The climate data extracted monthly from ERA5-Land Daily Aggregated data are as follows.

- **Temperature:** The mean 2 m air temperature (daily mean), which was averaged by month and converted into Celsius from Kelvin.
- **Precipitation:** Daily precipitation and the total sum (monthly sum), converted into millimeters from meters.

The climate data for 2 m temperature refer to the temperature of the air two meters above the ground. It does not mean a two-meter resolution.

ERA5-Land climate data are climate reanalysis data and not actual observations from weather stations within the forest zones.

### Forest Spatial Data

The original Forest Type Map was acquired from the spatial data distribution service of the Korea Forest Service.

You need to double-check the details (the version of the dataset and when it was acquired), as well as the permission for redistribution of the original dataset and the processed spatial dataset before public distribution.

## 4. Construction of Spatial Analysis Units

The original forest boundary dataset (51720.shp) was transformed into the EPSG:5179 coordinate system, and spatial analysis units were created using a 1 km grid.

### Processing Steps

1. Create a 1 km x 1 km grid with grid boundaries at integer multiples of 1,000 meters (based on the projected coordinate system).
2. Clip the original forest polygon data to the grid.
3. Combine the fragmented polygons of the same grid.
4. Give a unique ID to each analysis zone (구역_ID).
5. Save the geometry as a GeoPackage file (.gpkg).
6. Confirm the spatial units in QGIS.

*Grid lines are fixed at integer multiples of 1,000 m in the projected coordinate system.*

### Spatial Processing Results

| Validation Metric | Result |
|---|---:|
| Original Features | 76,479 |
| Generated Spatial Zones | 2,005 |
| Total Input Area | 1,525,798,527.223 m² |
| Total Output Area | 1,525,798,527.213 m² |
| Duplicate Zone IDs | 0 |
| Invalid Output Geometries | 0 |

(Validated with the generated GeoPackage, `split_report.json`.)

### Classification

Per the spatial processing report:

`classification_filter: "none; all original classes maintained"`

This means the output dataset is NOT restricted to any specific forest species / vegetation classification.

For a solely focused analysis (i.e. only certain forest cover classifications), further classification filtering is needed.

### QGIS Project Setup

The QGIS project points to the GeoPackage relative path:
```text
./hongcheon_split_1km.gpkg|layername=forest_split_1km
```

It's important to keep the .qgz project and .gpkg file in the same directory.

## 5. Climate Raster Processing

ERA5-Land temperature & precipitation variables are aggregated at the spatial zone x year x month level.

### Climate Variables

* Monthly Average Temperature (°C)

Daily 2 m air temperature averaged per month.

(temp. Kelvin -> Celsius)

* Monthly Cumulative Precipitation (mm)

Daily precipitation sum per month.

(precipitation unit m -> mm)

### Spatial Aggregation

Since the spatial resolution of ERA5-Land does not necessarily match the spatial resolution of 1 km forest analysis units, we use spatial aggregation based on overlapping areas of raster cells and spatial zones.

Instead of getting a value from one raster cell for the entire forest zone, we use spatial aggregation according to the ratio of overlapping raster cells.

### Correction of Precipitation

During data processing, some cases of minor negative values for daily precipitation were corrected to zero.

(Need to double-check the actual correction status of the intermediate climate dataset against the actual processing results.)

### Climate Dataset Structure

The intermediate Excel file `gee데이터.xlsx` contains:

Is it clear whether this is before or after the last negative precipitation correction?

This means that we cannot ensure an exact copy of the last corrected climate dataset just by reloading this Excel file.

Therefore, just by reloading the Excel file, we cannot make sure that we have an exact replication of the last correction climate dataset.

## 6. Sentinel-2 NDVI Processing and Data Integration

### 6.1 NDVI Computation in Google Earth Engine

NDVI computation here is based on Sentinel-2 Surface Reflectance Harmonized data.

**NDVI computation configuration:**

| Parameter | Configuration |
|---|---|
| Image Collection | COPERNICUS/S2_SR_HARMONIZED |
| Timeframe | 2017-2025 |
| Months | June, July, August |
| Red | B4 |
| Near-Infrared | B8 |
| Accepted SCL classes | 4 (Vegetation), 5 (Not Vegetation), 6 (Water) |
| Analysis CRS | EPSG:32652 |
| Analysis grid resolution | 10 m |
| Min. valid observations | 1 |
| Min. valid coverage | 80% |
| Batch for processing | 50 spatial zones |

**NDVI:** `NDVI = (B8 - B4) / (B8 + B4)`

**NDVI computation steps:**

1. Download Sentinel-2 surface reflectance images from Google Earth Engine.
2. Extract spectral bands B4 and B8 and calculate NDVI.
3. Use the Scene Classification Layer (SCL) mask to keep only defined classes.
4. Calculate monthly mean NDVI per pixel.
5. Calculate the count of valid observations.
6. Apply `reduceRegions()` and calculate area-weighted NDVI statistics per spatial analysis zone.
7. Calculate valid area coverage and statistics of observation quality.
8. Cache results (CSV files with statistics for spatial zones).
9. Merge monthly NDVI statistics with climate variables using spatial zone_id, year, and month.

All raster calculations are done on the server side in Google Earth Engine. Full satellite image datasets are not downloaded for local raster calculations.

We keep empty values (pixels without valid observations) and do not replace them with zero.

### 6.2 Generated DataFrames

ndvi_df - monthly statistics of NDVI and statistics of observation quality

combined_df - integrated temperature + precipitation + NDVI dataset

analysis_df - observations that satisfy the required NDVI coverage conditions and the availability of climate data

- The analysis dataset (`analysis_df`) includes observations that meet the following conditions:

  - Monthly NDVI data are available.
  - `ndvi valid area >= 80%`
  - Monthly mean temperature data are available.
  - Monthly cumulative precipitation data are available.

> A data quality criterion that can be configured in the processing code is the NDVI valid area threshold of 80%. This threshold has not always been applied to all the datasets that have been created in the past.

### 6.3 Backup and Excel Export

The Google Colab code creates the following in-memory backup copies:

- `combined_df_backup`
- `analysis_df_backup`

Generated Excel file:

- 홍천_기온_강수_NDVI_병합완료.xlsx

**The Excel file contains two worksheets:**

| Sheet | Source |
|---|---|
| 전체자료 | `combined_df` |
| 분석자료 | `analysis_df` |

The Excel file is exported using `pandas.ExcelWriter` with the `openpyxl` engine.

The following formatting options are applied:

- Frozen header row
- AutoFilter
- Adjusted column widths

## 7. Statistical Analysis Results

The statistical analysis results are documented in the following file:

- 202510124최재민 통계적분석 프로젝트1차 과제 (1)(2).xlsx

The analysis includes:

- Research background + description of dataset
- Descriptive statistics
- Scatter plots
- Pearson's correlation coefficients
- Joint relative frequency distribution tables
- Interpretation of results and discussion of the limitations of the approach

### 7.1 Analysis Dataset

- Statistical analysis was run on 50,771 observations from the worksheet "정제자료".
- This is a different dataset from the one with 46,048 observations that satisfy the 80% valid NDVI area threshold.

### 7.2 Pearson Correlation Coefficients

| Variable Pair | Pearson Correlation Coefficient (r) |
|---|---:|
| Monthly Mean Temperature – NDVI | -0.1656 |
| Monthly Cumulative Precipitation – NDVI | -0.2066 |
| Monthly Mean Temperature – Precipitation | +0.2313 |

### 7.3 Monthly Changes in Correlation Coefficients

- The correlation between temperature and NDVI differs across different months of summer.
- As seen in the results, it is not correct to think that the correlation value from all observations of summer months is more or less the same every month.

| Month | Correlation of Temperature vs. NDVI (r) |
|---|---:|
| June | -0.2370 |
| July | +0.1510 |
| August | -0.0115 |

As can be seen from the results, it would not be correct to assume that the correlation value based on all summer observations is generally the same for each month.

Keep in mind that these are not values of causal relationships, and nothing can be said about forest mortality or expected vegetation decline from these correlations.

### 7.4 Joint Relative Frequency Distribution

The joint relative frequency distribution of the three variables (temperature, precipitation, and NDVI) is calculated by splitting these values into three intervals (for each variable).

So in total, there are 27 different possible combinations of intervals for each of the variables.

This is done to analyze the distribution of vegetation and climate states in the observed dataset.

The purpose of this analysis is to investigate the distribution of vegetation and climate state in the observed dataset.

Naturally, this analysis depends on the choice of intervals. This is an exploratory statistical summary of the data.

---

## 8. Proposed Repository Structure

Suggested directory structure for GitHub project organization.

This is only a suggested structure. It does not necessarily mean that all files are already there or that the full pipeline is ready to run right now without additional preparation.

### Notes for the Repository

- The QGIS project and corresponding GeoPackage should be in the same directory.
- Please remember to remove or at least change the personal absolute path in the `split_report.json` file before publication.
- Personal file names should be changed. Also, check the internal file metadata.
- Please consider redistribution rights before publishing original or derived forest spatial data.
- Large raw satellite data are not necessary in the entire repository. We can perform raster calculations with GEE (remotely).

---

## 9. Environment Setup and Reproducibility

### 9.1 Python Dependencies

The following external Python packages are used in the given scripts to process NDVI data and create Excel files:

You need GeoPandas too if there are scripts that directly read spatial geometry data from a GeoPackage (e.g., if you have something in the repository).

The Python modules used from the standard Python library (e.g., json, time, pathlib, hashlib, etc.) are not separately listed.

The google.colab modules are provided by the Colab environment.

### 9.2 Reproduction Steps

1. Install necessary Python packages on Google Colab.
2. Authorize and initialize Google Earth Engine with an appropriate GEE project.
3. Load hongcheon_split_1km.gpkg into GeoDataFrame (zones).
4. Prepare the ERA5-Land climate DataFrame (weather_df).
5. Run scripts for NDVI data gathering and data integration.
6. Run the final data export script to save the dataset as Excel.

For example, spatial data loading is shown below.

**Climate DataFrame Fields**

The following fields are required.

If you have a verified final climate workbook, you can load a worksheet with pandas.read_excel().

However, the worksheet name, variable names, and precipitation correction status should be checked before running the scripts.

### 9.3 Current Reproducibility Limitations

The provided NDVI processing script expects zones and weather_df to be initialized already.

The NDVI script does not contain the full process of initial forest analysis unit construction and ERA5-Land climate data gathering and data correction.

In this sense, the current repository contains generated results and partial processing procedures, not a fully reproducible procedure.

**At this stage, the full end-to-end procedure is not reproducible with a single command.**

## 10. Limitations and Future Work

### Current Limitations

- **Geographical Scope:** Geographical analysis is confined to Hongcheon-gun, Korea.
- **Temporal Scope:** Temporal analysis is restricted to the Jun-Jul-Aug period of 2017~2025.
- **Satellite Observation Quality:** The quality of satellite observations (cloud/shadow/image quality, etc.) can sometimes affect the validity of NDVI observations, or the valid area coverage may be too small to meet the threshold.
- **Spatial Resolution:** There is a large difference in spatial resolution between Sentinel-2 & ERA5-Land.
- **Shared Climate Grid Cells:** Common climate grid cells among forest analysis zones can result in the same ERA5-Land climate values being assigned to multiple forest analysis zones.
- **Spatial and Temporal Dependence:** Spatial or temporal dependence means that repeated observations within the same spatial zone or an adjacent spatial zone are not necessarily statistically independent.

### Forest Classification

Spatial processing kept all the classification types as originally provided. More filtering could be needed to extract only certain types of forest cover.

### Variables Not Explicitly Modeled

All types of classification were retained as originally provided during spatial processing. You may need additional filtering to select only certain types of forest cover.

### Potential Future Work

- Sensitivity analysis of various NDVI quality thresholds
- Time-lagged analysis of climate/vegetation relationships
- Inclusion of additional environmental variables
- Analysis of spatiotemporal dependencies
- Prediction models for vegetation conditions
- Time-ordered model validation (avoiding temporal information leakage)

The above are potential future works and not the results of completed analyses.

## 11. Raw Forest Inventory Data

### Data Source

| Item | Description |
|---|---|
| Provider | Korea Forest Service |
| Dataset | Forest Type Map (1:5,000) |
| Region | Hongcheon-gun, Gangwon State, S. Korea |
| Original File Name | 51720.shp |
| Coordinate Reference System | EPSG:5179 |
| Number of original polygons | 76,479 |

### Data Availability

The original data were downloaded from the Korea Forest Service's spatial data sharing service.

Note: We downloaded the original data from the spatial data sharing service of the Korea Forest Service.

Be sure to verify the redistribution permissions for the derived spatial dataset as well before publishing.

### Reproducibility

Results of preprocessing are recorded in `data/metadata/split_report.json`.

- The report contains details of spatial processing options, input/output feature counts, geometry validation, area consistency, etc.

## 12. Project Status

(Exploratory data analysis - needs more validation and development)

The project currently focuses on explaining spatial preprocessing, satellite NDVI processing, climate data processing, and initial statistical exploratory analysis.

We plan to improve reproducibility and data quality validation criteria. We also plan to further advance the analysis toward more advanced spatiotemporal modeling.

The repository was used to document the development process and undergraduate project, with the purpose of keeping track of implemented methods, deficiencies, and future upgrades.
