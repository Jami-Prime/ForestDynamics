# ForestDynamics

Spatiotemporal correlation analysis between climate(T,P) and NDVI(satellite) data in Hongcheon, South Korea.

## 1. Introduction

- Monthly mean temperature, Monthly accumulation of precipitation and monthly average Normalized Difference Vegetation Index (NDVI) spatial and temporal correlation analysis in Hongcheon-gun, Gangwon State, South Korea.
- Spatial zone was created based on the vector data of Forest Type Map of Korea Forest Service.
- The data of climate was collected from ERA5-Land and the data of NDVI was calculated using the satellite data of Sentinel-2 through Google Earth Engine(GEE).
- Raster data were not downloaded and analyzed locally, but instead the computation of the raster data was conducted within GEE and the statistics (zonal statistics) of the raster data were exported and arranged, integrated into the tabular data.
- Spatial data setup, the combination of climate data and vegetation data, descriptive statistics, joint relative frequency table, and correlation analysis.
- This is only exploratory analysis, no causal analysis and future prediction(vegetation)

## 2. Summary

| Item | Description |
|---|---|
| Study Area | Hongcheon-gun, Gangwon State, South Korea |
| Study Period | 2017-2025(Jun-Aug) |
| Unit of Observation | Zone(space) * Year * Month |
| Total spatial zone | 2,005 |
| Total Possible Observations | 54,135 |
| Observations Included in Statistical Analysis | 50,771 |
| Observations w/ 80% NDVI Coverage Criteria | 46,048 |
| Main tools | QGIS, Google Earth Engine, Python, Pandas, Excel |
| Main Variable | Temperature, Precipitation, NDVI |

※ Data Interpretation - 46,048 observations in 원자료, 50,771 observations in 정제자료. The names are not simple filter-in/filter-out. You need to check the dataset for statistical analysis and the dataset where NDVI quality filtering has been applied.

## 3. Data Sources

3 basic dataset is used.

| Dataset | Source | Purpose |
|-----------------|-------------------------------------------------------------|------------------------------------------|
| Forest Type Map | Korea Forest Service (51720.shp) | spatial analysis unit construction |
| Temperature & Precipitation | ECMWF ERA5-Land Daily Aggregated | extract climate variable |
| Satellite Image | Sentinel-2 Surface Reflectance Harmonized | calculate NDVI |

### Climate Data

The climate data that was monthly extracted from ERA5-Land Daily Aggregated data are as follows.
- **Temperature:** The mean 2 m air temperature (daily mean) which was averaged by month and converted into Celsius from Kelvin.
- **Precipitation:** Daily precipitation and the total sum (monthly sum), converted into millimeters from meters.

The climate data for 2m temperature is for the temperature of the air two meters above the ground. It does not mean two meter resolution.

ERA5-Land climate data are the climate reanalysis data and not actual weather stations within the forest zone.

### Forest Spatial Data

The original Forest Type Map was acquired from the spatial data distribution service in Korea Forest Service.

You need to double check the details (version of the dataset and when it was acquired. And permission for redistribution of the original dataset and the processed spatial dataset before public distribution.

## 4. Construction of Spatial Analysis Units

The original forest boundary dataset(51720.shp) was applied to the EPSG:5179 coordinate system and created the spatial analysis unit with 1km grid.

### Processing Steps

1. Create 1km x 1km grid with the integer multiple of 1,000 meter of the grid boundary (based on projected coordinate system).
2. Clip the original forest polygon data to the grid.
3. Combine the fragmented polygons of the same grid.
4. Give the unique ID for each analysis zone (구역_ID)
5. Save the geometry as GeoPackage file (.gpkg)
6. Confirm the spatial units in QGIS

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

(validated with generated GeoPackage, `split_report.json`)

### Classification
Per the spatial processing report:

`classification_filter: "none; all original classes maintained"`
which means the output dataset is NOT restricted to any specific forest species / vegetation classification

For a solely focused analysis (i.e. only certain forest cover classifications), further classification filtering is needed.

### QGIS Project Setup
The qgis project points to GeoPackage relative path:
```
./hongcheon_split_1km.gpkg|layername=forest_split_1km
```
it's important to keep .qgz project and .gpkg file in the same directory.

## 5. Climate Raster Processing
ERA5-Land temperature & precipitation variables aggregated at spatial zone x year x month level

### Climate Variables
* Monthly Average Temperature (°C)
Daily 2m air temp averaged per month.
(temp. Kelvin -> Celsius)
* Monthly Cumulative Precipitation (mm)
Daily precipitation sum per month.
(precipitation unit m -> mm)

### Spatial Aggregation
Since spatial resolution of ERA5-Land does not necessarily match the spatial resolution of 1km forest analysis units, we use spatial aggregation based on overlapping areas of raster cells and spatial zones.
Instead of getting value for one raster cell for all forest zone we use spatial aggregation according to ratio of overlapping raster cell.

### Correction of Precipitation
During data processing, some cases of minor negative values for daily precipitation were corrected to zero.
(Need to double check the actual correction status of intermediate climate dataset with the actual processing results)

### Climate Dataset Structure
Intermediate excel file gee데이터.xlsx contains:
is it clear before or after last negative precip correction?
it means that we cannot ensure exact copy of last correction climate dataset just by reloading this excel file

therefore, just by reloading the excel file we cannot make sure to have an exact replication of the last correction climate dataset.

## 6. Sentinel-2 NDVI Processing and Data Integration

### 6.1 NDVI Computation in Google Earth Engine

NDVI computation here is based on Sentinel-2 Surface Reflectance Harmonized data

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
| min valid observations | 1 |
| min valid coverage | 80% |
| batch for processing | 50 spatial zones |

**NDVI:** `NDVI = (B8 - B4) / (B8 + B4)`

**NDVI computation steps:**

1. download of sentinel-2 surface reflectance images from Google Earth Engine
2. extract spectral bands B4 B8 and calculate NDVI
3. use mask Scene Classification Layer (SCL) to keep only defined classess
4. calculate monthly mean NDVI per pixel
5. calculate count of valid obs
6. reduceRegions() and calculate statistics (area weighted) NDVI per spatial analysis zone
7. calculate valid area coverage, calculate statistics of observation quality
8. cache results (csv files with statistics for spatial zones)
9. merge monthly stats NDVI with climate (variables) on spatial zone_id,year,month

All raster calculations are done server side in Google Earth Engine. No download of full satellite images datasets for local raster calculations.

We keep empty values (non valid observation pixels) and do not replace them with zero.

### 6.2 Generated DataFrames

ndvi_df - monthly stats of NDVI, stats of quality of observation

combined_df - integrated temperature+precip+ndvi dataset

analysis_df - observations which satisfy conditions of required ndvi coverage and availabilty of climate data


- The analysis dataset (`analysis_df`) includes observations that meet the following conditions:

  - Monthly NDVI data are available.
  - `ndvi valid area >= 80%`
  - Monthly mean temperature data are available.
  - Monthly cumulative precipitation data are available.

>  A data quality criteria that can be configured in the processing code is the NDVI valid area threshold of 80%. This threshold has not always been applied to all the datasets that have been created in the past.

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

- research background + description of dataset
- descriptive stats
- scatter plots
- Pearson's correlation coef
- joint relative frequency dist. tables
- interpret results, discussion of limitations of approach

### 7.1 Analysis Dataset

- Statistical analysis was run over 50771 obs from worksheet "정제자료".
- This is different dataset than the dataset with 46048 observations which satisfy threshold of valid area of NDVI 80%

### 7.2 Pearson Correlation Coefficients

| Variable Pair | Pearson Correlation Coefficient (r) |
|---|---:|
| Monthly Mean Temperature – NDVI | -0.1656 |
| Monthly Cumulative Precipitation – NDVI | -0.2066 |
| Monthly Mean Temperature – Precipitation | +0.2313 |

### 7.3 Monthly Changes in Correlation Coefficients

- Correlation between temperature and NDVI differs for different months of summer.
- As seen in the results. It is not correct to think that the value of correlation from all observations of summer months is more or less the same every month.

| Month | Correlation of Temperature vs. NDVI (r) |
|---|---:|
| June | -0.2370 |
| July | +0.1510 |
| August | -0.0115 |

As can be seen from the results, it would be not correct to assume that the correlation value based on all summer observations is generally the same for each month.

Keep in mind that those are not values of causal relations and nothing can be said about mortality of forests or expected veg decline from these correlations.

### 7.4 Joint Relative Frequency Distribution

3 variable joint rel. freq. dist. for temperature, precipitation, ndvi is calculated by splitting these values to three intervals (each variable).
So in total there is 27 different possible combinations of intervals for each of variables.

This is done to analyze distribution of veg, climate states in observed dataset.

The purpose of this analysis is to investigate the distribution of vegetation and climate state in the observed dataset.

Naturally, this analysis depends on intervals choice. This is some explorative stat summary of data.

---

## 8. Proposed Repository Structure

Suggested directory structure for GitHub project organization.

This is only suggested structure. It does not mean that not necessarily all files are there yet or full pipeline is ready to run right now without additional preparations..

### Notes for the Repository

- QGIS project and corresponding GeoPackage should be in the same directory
- Please remember to remove or at least change the personal abs path in split_report.json file before publication
- Personal file name should be changed. also check file internal meta information
- Please consider rights for redistribution before publishing original or derived forest spatial data
- Big raw satellite data is not necessary in the whole repo. we can do raster calculation with GEE (remote)

---

## 9. Environment Setup and Reproducibility

### 9.1 Python Dependencies

The following external python packages are used in the given scripts to process NDVI data and create excel files:

You need geopandas too if there is script(s) which directly read spatial geometry data from GeoPackage (e.g. if you have something in the repo?)

The python modules used from standard python lib (e.g. json, time, pathlib, hashlib, etc.) are not separately listed.

The google.colab modules are provided by the Colab environment.


### 9.2 Reproduction Steps

1. Install necessary python packages on Google Colab
2. Google Earth Engine authorize and initialize with appropriate GEE project
3. Load hongcheon_split_1km.gpkg to GeoDataFrame(zones)
4. Make ERA5-Land climate Data(frame)(weather_df)
5. Run scripts for NDVI data gathering and data integration.
6. Run final data export script to save dataset as excel.

For example, spatial data loading is like below.

**Climate DataFrame Fields**

The following fields are required.

If you have verified final climate workbook, you can load a worksheet with pandas.read_excel().

However, the worksheet name, variable names, and precipitation correction status should be checked before running the scripts.

### 9.3 Current Reproducibility Limitations

The provided NDVI processing script expects already initialized zones and weather_df.

The NDVI script does not contain full process of initial forest analysis unit construction and ERA5-land climate data gathering and data correction..

In this sense, current repo contains generated results and partly process excecution procedure, not full reproducible procedure.

**At this stage, full end-to-end procedure is not reproducible with single command.**

## 10. Limitations and Future Work

### Current Limitations

- **Geographical Scope:** Geographical Analysis is confined to Hongcheon-gun of Korea
- **Temporal Scope:** Temporal Analysis is restricted only to Jun-Jul-Aug period of 2017~2025.
- **Satellite Observation Quality:** Quality of satellite observation (cloud/shadow/image-quality etc.) can sometimes affect the validity of ndvi observation or validity-area-coverage is too small to meet threshold.
- **Spatial Resolution:** Large difference in spatial resolution between sentinel-2 & ERA5-Land.
- **Shared Climate Grid Cells:** Common Climate Grid cell among forest analysis zone can affect where the climate value of ERA5-Land is common among multiple forest analysis zones.
- **Spatial and Temporal Dependence:** Spatial or Temporal dependence is not necessarily the statistically independent for repeating observation on the same spatial zone, or zone adjacent to the spatial zone.

### Forest Classification
Spatial processing kept all the classification types as original. More filtering could be needed to extract only certain types of forest cover.

### Variables Not Explicitly Modeled
All types of classification stayed as original upon applying the spatial processing. You may need additional filtering to pick only certain type of forest cover.

### Potential Future Work
- Sensitivity analysis of various ndvi quality threshold
- Time-lagged analysis on climate/vegetation relations
- Inclusion of additional environmental variables
- Analysis on spatiotemporal dependency
- Prediction model on vegetation condition
- Time ordered model validation (avoiding temporal info leak)

Above are potential future works and not the result of completed analysis.

## 11. Raw Forest Inventory Data

### Data Source

| Item | Description |
|---|---|
| Provider | Korea Forest Service |
| Dataset | Forest Type Map (1:5,000) |
| Region | Hongcheon-gun, Gangwon State, S.Korea |
| Original File Name | 51720.shp |
| Coordinate Reference System | EPSG:5179 |
| Number of original polygons | 76,479 |

### Data Availability
 The original data were downloaded from Korea Forest Service's spatial data sharing service.

Note: We've download the original data from spatial data sharing service of Korea Forest Service.

Be sure to verify the re-distribution on derived spatial data set as well before publishing.

### Reproducibility
 Results of preprocessing are recorded in data/metadata/split_report.json
 - Report contains details of spatial processing option, feature count of input/output, geometry validation, area consistency, etc.

## 12. Project Status

(Exploratory data analysis - need more validation and development)

Project currently focuses on explanation of spatial pre-processing, sat-ndvi processing, climate data processing, and initial statistical exploratory analysis.

We plan to increase the re-producibility and validity criteria of data quality. Also, to further advance the analysis to more advanced spatiotemporal modeling.

The repo was used to document the development process and undergraduate project with the purpose of keeping track of implemented methods, deficiencies and future upgrades.
