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
Since the spatial resolution of ERA5-Land doesn't necessarily align with the 1km forest analysis units, spatial aggregation was done based on overlap areas of raster cells and spatial zones.
Instead of attributing a single raster cell value to the whole forest zone, spatial aggregation was done based on the ratio of overlapping raster cell.

### Correction of Precipitation
During data processing, some cases of minor negative values for daily precipitation were corrected to zero.
(Need to double check the actual correction status of intermediate climate dataset with the actual processing results)

### Climate Dataset Structure
Intermediate Excel file (gee데이터.xlsx) contains the following variables:

is it clear whether this excel is before or after the last negative precipitation correction?

therefore, just by reloading the excel file we cannot make sure to have an exact replication of the last correction climate dataset.

## 6. Sentinel-2 NDVI Processing and Data Integration

### 6.1 NDVI Computation in Google Earth Engine

The following NDVI computation was performed based on Sentinel-2 Surface Reflectance Harmonized data.

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

1. download Sentinel-2 surface reflectance images from Google Earth Engine
2. extract spectral bands B4, B8 and perform NDVI computation
3. apply mask of Scene Classification Layer (SCL) to keep only defined classes
4. perform monthly mean NDVI per pixel computation
5. perform count of valid observations computation
6. perform reduceRegions() and compute area-weighted NDVI statistics per spatial analysis zone.
7. perform computation of coverage for valid area, computation of observation quality statistics.
8. cache results (spatial zones statistics in csv files)
9. combine monthly NDVI statistics with climate variables on spatial zone_id, year, month.

All raster computations are performed on Google Earth Engine server side. There is no download of full datasets of satellite images to perform raster computations on the local machine.

We keep non-valid-observation pixels with empty values, instead of setting values equal to zero.

### 6.2 Generated DataFrames

ndvi_df: monthly NDVI statistics and observation quality statistics

combined_df: integrated temperature+precipitation+ndvi dataset

analysis_df: observations fulfilling the conditions of the required NDVI coverage and the climate data availability.

- 분석데이터셋(analysis_df) 에 대해 아래조건을 만족하는 데이터들을 포함하고 있음.

* 월별 ndvi 존재
- `ndvi valid area >= 80%`
* 월평균온도 존재
* 월 누적강수량 존재

> ndvi valid area ≥ 80%은 데이터처리가되는 코드상에서 설정가능한 데이터 품질 기준이며, 이 기준은 종전의 다양한 데이터셋에 대해 일률적으로 적용되지 않았음

### 6.3 백업 및 Excel 파일 추출

google colab 코드에서 제공되는 코드상으로는 아래 in-memory copy들이 만들어짐

- combined_df_backup
- analysis_df_backup

생성되는 excel 파일명

- 홍천_기온_강수_NDVI_병합완료.xlsx

**구성되어 있는 Excel 시트 2장:**

| sheet | source |
|---|---|
| 전체자료 | combined_df |
| 분석자료 | analysis_df |

excel 파일 추출은 pandas.excelWriter를 사용하였음. openpyxl Engine 사용.

- frozen header 행 적용
- auto filter 적용
- column width 변경 등 적용

<!-- 원문에 내용이 없는 미완성 항목: excel 파일 추출시 -->

## 7. 통계분석결과

통계분석 결과는 아래 파일에서 정리됨

- 202510124최재민 통계적분석 프로젝트1차 과제 (1)(2).xlsx

* 연구배경 및 데이터소개
* 단순통계량
* 산점도
* Pearson 상관계수
* Joint 상대빈도분포표
* 결과 해석 및 분석 방법론적 한계 설명

### 7.1 분석데이터

50771 (정제자료 sheet) 데이터 대상으로 통계적분석을 수행한 것을 정리하였음.

- ndvi가 존재하지 않은 데이터를 제외한 데이터셋(46048, ndvi valid area >= 80%) 데이터셋과 별개임.

### 7.2 Pearson 상관계수

| 상관변수 | Pearson 상관계수 r |
|---|--:|
| 월평균온도 ndvi | -0.1656 |
| 월누적강수 ndvi | -0.2066 |
| 월평균온도-강수 | +0.2313 |

### 7.3 월별 상관계수 변화

- summer 기간동안 온도의 ndvi 상관성이 변화가 발생함.

| Month | Correlation of Temperature vs. NDVI (r) |
|---|---:|
| June | -0.2370 |
| July | +0.1510 |
| August | -0.0115 |

As can be seen from the results, it would be not correct to assume that the correlation value based on all summer observations is generally the same for each month.

Note that the values found are not causal relations, nor can one say anything about forest mortality or expected vegetation decline based on these correlations.

### 7.4 Joint Relative Frequency Distribution

A three-variable joint relative frequency distribution for temperature, precipitation, and NDVI is created by segmenting these values into three intervals each.

Hence, there are 27 possible combinations of intervals of the variables.

The purpose of this analysis is to investigate the distribution of vegetation and climate state in the observed dataset.

The results naturally depend on the choice of intervals and should be seen as an exploratory statistical summary of the data.

---

## 8. Proposed Repository Structure

The following structure for the directory is suggested for the project's organization on GitHub.

The structure is a suggestion and does not necessarily mean that all files are available already, or the full pipeline is ready to run at the moment without further preparations.

### Notes for the Repository

- QGIS project and its referenced GeoPackage should be in the same directory.
- Do not forget to remove or at least rename personal absolute paths in the split_report.json before publication.
- Personal filenames must be renamed as well. Also check the internal metadata of the files.
- Take care about redistribution rights before publishing any original or derived forest spatial data.
- The full repository does not need big raw satellite imagery datasets, since raster calculations can be done on GEE (remote).

---

## 9. Environment Setup and Reproducibility

### 9.1 Python Dependencies

The following external python packages are used in the given scripts to process NDVI data and create excel files:

For any script using a direct reading of spatial geometry from a GeoPackage (e.g., if any are provided in the repository), geopandas is needed too.

Note that the python modules used from the standard python library (e.g. json, time, pathlib, hashlib, etc.) are not listed separately.

google.colab 모듈은 구글 Colab의 환경에서 제공됩니다.

### 9.2 재현 순서

- 구글 Colab에 필요한 파이썬 패키지 설치
- 구글 Earth Engine과의 인증 및 적절한 GEE 프로젝트 초기화
- hongcheon_split_1km.gpkg 를 GeoDataFrame(zones) 로 읽어옴
- ERA5-Land의 기후 데이터 (DataFrame, weather_df) 준비
- NDVI 수집 및 데이터 통합 실행 스크립트 실행
- 최종 dataset을 excel로 저장하기 위한 실행 스크립트 (excel로 export)

예시로 spatial 데이터셋을 읽어오는 부분은 아래와 같습니다.

기후 DataFrame필드

- 반드시 있어야 하는 필드는 다음과 같습니다.

만약 검증된 마지막 기후 워크북이 있다면, 해당 워크시트를 pandas.read_excel() 로 로딩하실 수 있습니다.

다만 워크시트명, 변수명, 강수보정 여부를 확인 후 실행을 진행해야합니다.

### 9.3 현재 재현성 제한점

제공된 NDVI 처리 스크립트는 이미 zones, weather_df 가 초기화된 상태를 가정하고 있습니다.

초기 forest analysis unit 생성 방법, ERA5-Land 기후 데이터 수집 및 보정하는 전체 절차는 NDVI 스크립트 상에서 제공되지 않고 있습니다.

즉, 현재 상태에서 설명할 수 있는 부분은 output들 및 부분 실행 절차에 대한 설명 뿐입니다.

즉, **아직은 단 하나의 명령어로 모든 과정(end-to-end)의 재현성을 보장하지 못하는 상태입니다.** 

## 10. 제한점 및 향후 계획

### 현재 제한점

- Geographical scope: 홍천군 (한국)
- Temporal scope: 2017~2025년 중 6, 7, 8월 관측만 적용
- Satellite observation quality: 구름 및 그늘 등 이미지 퀄리티에 따라 NDVI 관측 불가능 및 적절한 valid area 범위를 보장하지 못할 수 있음
- Spatial resolution: Sentinel-2 와 ERA5-land가 상당히 다른 spatial resolution을 가지고 있어서, 
- 여러 forest analysis zone이 동일한 ERA5-land grid cell의 기후 정보를 공유할 수 있음
- Spatial / temporal dependency: 동일한 spatial zone의 반복 관측이나 인접 지역의 관측값이 항상 통계적으로 독립적이라고 볼 수 없음

### Forest Classification
Spatial processing kept all the classification types as original. More filtering could be needed to extract only certain types of forest cover.

### Variables Not Explicitly Modeled
Elevation, species type in forest, soil condition, accumulated precipitations, time-lag effect from climate.

### Potential Future Work
- Sensitivity analysis for different NDVI quality threshold
- Time-lagged analysis for climate and vegetation relations
- Incorporate more environmental variables
- Spatial-temporal dependency analysis
- Prediction model of vegetation conditions
- Time ordered model validation to avoid temporal info leak

The above are potential future works, not the result of completed analysis.

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

Note: The original shapefile is not placed here as we have not confirmed permission for re-distribution.

You must also confirm the re-distribution for the derived spatial data set before publication.

### Reproducibility
 Results of preprocessing are recorded in data/metadata/split_report.json
 - Report includes spatial processing option, input/output feature count, geometry validation, area consistency etc.

## 12. Project Status

(Exploratory data analysis - need more validation and development)

Project is currently describing spatial preprocessing, sat-ndvi processing, climate data processing, and initial statistical exploratory analysis.

Developments planned include increase of reproducibility and data-quality validity criteria. Further, develop the analysis towards more advanced spatiotemporal modeling.

The repo was used to document a development process and undergraduate project with the goal of recording implemented methods, shortcomings and future upgrades.
