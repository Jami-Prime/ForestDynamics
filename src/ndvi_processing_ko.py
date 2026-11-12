
import json
import time
from pathlib import Path

import ee
import numpy as np
import pandas as pd

# ── 1. Configuration and input validation ────────────
if "zones" not in globals() or "weather_df" not in globals():
    raise RuntimeError(
        "산림 경계 zones와 기상자료 weather_df를 만드는 셀을 먼저 실행하세요."
    )

YEARS = list(range(2017, 2026))
MONTHS = [6, 7, 8]

# Process zones in batches to limit request size
BATCH_SIZE = 50

# Use a consistent 10 m analysis grid for all months
ANALYSIS_CRS = "EPSG:32652"
GRID_TRANSFORM = [10, 0, 0, 0, -10, 0]

# Require at least one valid observation per pixel per month
MIN_VALID_OBS = 1

# Minimum coverage threshold for analysis eligibility
# Records failing this threshold are retained in the full dataset
MIN_COVERAGE = 0.80

# Reuse completed batch results within the same runtime
CACHE_DIR = Path("/content/hongcheon_ndvi_scl_v1")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

z = zones[["구역_ID", "geometry"]].copy()
z["구역_ID"] = z["구역_ID"].astype(str)
z = z.sort_values("구역_ID").reset_index(drop=True)

if z.empty or z.crs is None:
    raise ValueError("산림 경계 또는 좌표계가 없습니다.")

if z["구역_ID"].isna().any() or z["구역_ID"].duplicated().any():
    raise ValueError("구역_ID를 확인하세요.")

if (
    z.geometry.isna().any()
    or z.geometry.is_empty.any()
    or not z.geometry.is_valid.all()
):
    raise ValueError("빈 도형 또는 유효하지 않은 도형이 있습니다.")

z_wgs84 = z.to_crs("EPSG:4326")

# Define a rectangular search extent without merging all forest polygons
xmin, ymin, xmax, ymax = z_wgs84.total_bounds
search_region = ee.Geometry.Rectangle(
    [xmin, ymin, xmax, ymax],
    proj="EPSG:4326",
    geodesic=False,
)

source = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(search_region)
    .filterDate("2017-06-01", "2025-09-01")
    .filter(ee.Filter.calendarRange(6, 8, "month"))
)

def make_ndvi(image):
    image = ee.Image(image)
    scl = image.select("SCL")

    clear = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6))

    red = image.select("B4").multiply(0.0001)
    nir = image.select("B8").multiply(0.0001)
    denominator = nir.add(red)

    return (
        nir.subtract(red)
        .divide(denominator)
        .rename("NDVI")
        .updateMask(clear)
        .updateMask(denominator.gt(0))
        .copyProperties(image, ["system:time_start"])
    )

# Prepare forest zone boundaries for each batch
batches = []

for begin in range(0, len(z_wgs84), BATCH_SIZE):
    part = z_wgs84.iloc[begin:begin + BATCH_SIZE]

    features = []
    for zone_id, geometry in zip(part["구역_ID"], part.geometry):
        features.append(
            ee.Feature(
                ee.Geometry(
                    geometry.__geo_interface__,
                    proj="EPSG:4326",
                    geodesic=False,
                ),
                {"zone_id": zone_id},
            )
        )

    batches.append((
        part["구역_ID"].tolist(),
        ee.FeatureCollection(features),
    ))

# Prevent reuse of cached results when boundaries or settings change
import hashlib

signature = hashlib.sha256()
signature.update(
    json.dumps({
        "crs": ANALYSIS_CRS,
        "transform": GRID_TRANSFORM,
        "min_valid_obs": MIN_VALID_OBS,
        "method": "SCL_456_monthly_mean_v1",
    }, sort_keys=True).encode()
)

for zone_id, geometry in zip(z["구역_ID"], z.geometry):
    signature.update(zone_id.encode())
    signature.update(geometry.wkb)

signature_file = CACHE_DIR / "signature.txt"
current_signature = signature.hexdigest()

if signature_file.exists():
    if signature_file.read_text() != current_signature:
        raise RuntimeError(
            "기존 NDVI 캐시와 경계·설정이 다릅니다. "
            "CACHE_DIR을 새로운 폴더명으로 바꾸세요."
        )
else:
    signature_file.write_text(current_signature)

# ── 2. Monthly NDVI and observation statistics ───────
all_frames = []

for year in YEARS:
    for month in MONTHS:
        start = ee.Date.fromYMD(year, month, 1)
        end = start.advance(1, "month")
        monthly = source.filterDate(start, end)

        n_images = monthly.size().getInfo()

        if n_images > 0:
            ndvi_collection = monthly.map(make_ndvi)

            count = (
                ndvi_collection.count()
                .rename("count")
                .unmask(0, sameFootprint=False)
                .setDefaultProjection(
                    ANALYSIS_CRS, GRID_TRANSFORM
                )
            )

            monthly_mean = (
                ndvi_collection.mean()
                .rename("NDVI")
                .setDefaultProjection(
                    ANALYSIS_CRS, GRID_TRANSFORM
                )
                .updateMask(count.gte(MIN_VALID_OBS))
            )

            pixel_area = ee.Image.pixelArea()

            # Prepare bands for zonal aggregation:
            # NDVI × pixel area, valid area, total area,
            # and observation count × pixel area
            statistics_image = (
                monthly_mean.multiply(pixel_area)
                .rename("ndvi_area")
                .addBands(
                    pixel_area
                    .updateMask(monthly_mean.mask())
                    .rename("valid_area")
                )
                .addBands(pixel_area.rename("total_area"))
                .addBands(
                    count.multiply(pixel_area).rename("obs_area")
                )
            )

        for batch_number, (ids, boundaries) in enumerate(batches):
            cache_path = CACHE_DIR / (
                f"{year}_{month:02d}_{batch_number:04d}.csv"
            )

            if cache_path.exists():
                frame = pd.read_csv(
                    cache_path, dtype={"구역_ID": str}
                )
                if frame["구역_ID"].tolist() != ids:
                    raise RuntimeError("캐시의 구역 순서가 다릅니다.")

                all_frames.append(frame)
                continue

            records = []

            if n_images == 0:
                records = [
                    {
                        "구역_ID": zone_id,
                        "연도": year,
                        "월": month,
                        "월평균NDVI": np.nan,
                        "NDVI_유효면적비율": 0.0,
                        "NDVI_평균유효관측수": 0.0,
                        "NDVI_입력영상수_조회범위": 0,
                    }
                    for zone_id in ids
                ]
            else:
                # Retry temporary request failures up to three times
                for attempt in range(3):
                    try:
                        result = statistics_image.reduceRegions(
                            collection=boundaries,
                            reducer=ee.Reducer.sum(),
                            crs=ANALYSIS_CRS,
                            crsTransform=GRID_TRANSFORM,
                            tileScale=4,
                        )

                        # Exclude complex geometries from the response
                        result = result.map(
                            lambda feature: ee.Feature(
                                None, ee.Feature(feature).toDictionary()
                            )
                        ).getInfo()
                        break
                    except Exception:
                        if attempt == 2:
                            raise
                        time.sleep(3 * (attempt + 1))

                lookup = {
                    feature["properties"]["zone_id"]:
                        feature["properties"]
                    for feature in result["features"]
                }

                for zone_id in ids:
                    p = lookup.get(zone_id, {})
                    total_area = float(p.get("total_area") or 0)
                    valid_area = float(p.get("valid_area") or 0)
                    numerator = p.get("ndvi_area")
                    obs_area = float(p.get("obs_area") or 0)

                    mean_ndvi = (
                        float(numerator) / valid_area
                        if valid_area > 0 and numerator is not None
                        else np.nan
                    )

                    coverage = (
                        np.clip(valid_area / total_area, 0, 1)
                        if total_area > 0 else np.nan
                    )

                    records.append({
                        "구역_ID": zone_id,
                        "연도": year,
                        "월": month,
                        "월평균NDVI": mean_ndvi,
                        "NDVI_유효면적비율": coverage,
                        # Area-weighted observation count
                        # normalized by the total zone area
                        "NDVI_평균유효관측수": (
                            obs_area / total_area
                            if total_area > 0 else np.nan
                        ),
                        # Number of images in the regional search extent,
                        # not the number of images for each individual zone
                        "NDVI_입력영상수_조회범위": n_images,
                    })

            frame = pd.DataFrame(records)
            frame.to_csv(
                cache_path, index=False, encoding="utf-8-sig"
            )
            all_frames.append(frame)

            print(
                f"{year}-{month:02d} / "
                f"배치 {batch_number + 1}/{len(batches)} 완료",
                flush=True,
            )

        print(f"▶ {year}-{month:02d} 전체 완료", flush=True)

# ── 3. NDVI dataset construction ─────────────────────
ndvi_df = pd.concat(all_frames, ignore_index=True)

keys = ["구역_ID", "연도", "월"]

ndvi_df = ndvi_df.sort_values(keys).reset_index(drop=True)

if ndvi_df.duplicated(keys).any():
    raise RuntimeError("NDVI 표의 구역·연도·월이 중복됩니다.")

ndvi_df["NDVI_품질통과"] = (
    ndvi_df["월평균NDVI"].notna()
    & ndvi_df["NDVI_유효면적비율"].ge(MIN_COVERAGE)
)

# ── 4. Merge NDVI with existing climate data ─────────
weather_for_merge = weather_df.copy()
weather_for_merge["구역_ID"] = (
    weather_for_merge["구역_ID"].astype(str)
)

for column in ["연도", "월"]:
    weather_for_merge[column] = pd.to_numeric(
        weather_for_merge[column], errors="raise"
    ).astype(int)

if weather_for_merge.duplicated(keys).any():
    raise RuntimeError("기상자료의 구역·연도·월이 중복됩니다.")

# Remove existing NDVI columns to prevent duplicates on reruns
ndvi_columns = [c for c in ndvi_df.columns if c not in keys]
weather_for_merge = weather_for_merge.drop(
    columns=ndvi_columns, errors="ignore"
)

combined_df = weather_for_merge.merge(
    ndvi_df,
    on=keys,
    how="left",
    validate="one_to_one",
    indicator=True,
)

if combined_df["_merge"].ne("both").any():
    raise RuntimeError("일부 기상자료에 대응하는 NDVI 행이 없습니다.")

combined_df = combined_df.drop(columns="_merge")

analysis_df = combined_df.loc[
    combined_df["NDVI_품질통과"]
    & combined_df["월평균기온_C"].notna()
    & combined_df["월누적강수량_mm"].notna()
].copy()

print("\nNDVI 수집 행 수:", len(ndvi_df))
print("병합한 전체 행 수:", len(combined_df))
print("품질 기준 통과 분석 행 수:", len(analysis_df))

display(combined_df.head())
