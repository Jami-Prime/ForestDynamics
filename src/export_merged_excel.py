import pandas as pd
from google.colab import files

if "combined_df" not in globals() or "analysis_df" not in globals():
    raise RuntimeError("NDVI 수집·병합 셀을 먼저 완료하세요.")

output_path = "/content/홍천_기온_강수_NDVI_병합완료.xlsx"

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    for sheet_name, df in {
        "전체자료": combined_df,
        "분석자료": analysis_df,
    }.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

        ws = writer.sheets[sheet_name]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        for column in ws.columns:
            ws.column_dimensions[column[0].column_letter].width = 24

files.download(output_path)
