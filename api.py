from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
import io

from engine import run_gap_analysis
from control_generator import generate_gap_controls_json
from llm_service import llm_config_summary

# Version: 2.0 - Enhanced matching with numeric difference detection
app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/llm")
async def health_llm():
    return llm_config_summary()


@app.post("/debug/preview")
async def debug_preview(left: UploadFile = File(...), right: UploadFile = File(...)):
    """Debug endpoint to preview file columns and sample data."""
    from engine import find_best_column
    
    df_left = await read_file(left)
    df_right = await read_file(right)
    
    policy_col_left = find_best_column(df_left, ["policy", "control", "rule", "name", "title"])
    policy_col_right = find_best_column(df_right, ["policy", "control", "rule", "name", "title"])
    cid_col_right = find_best_column(df_right, ["cid", "id"])
    
    return {
        "left_file": {
            "columns": list(df_left.columns),
            "detected_policy_column": policy_col_left,
            "row_count": len(df_left),
            "sample_titles": df_left[policy_col_left].head(5).tolist() if policy_col_left else []
        },
        "right_file": {
            "columns": list(df_right.columns),
            "detected_policy_column": policy_col_right,
            "detected_cid_column": cid_col_right,
            "row_count": len(df_right),
            "sample_data": df_right[[policy_col_right, cid_col_right]].head(10).to_dict('records') if (policy_col_right and cid_col_right) else []
        }
    }


async def read_file(upload: UploadFile) -> pd.DataFrame:
    filename = (upload.filename or "").lower()
    content = await upload.read()

    if filename.endswith(".csv"):
        text = content.decode("utf-8", errors="ignore")
        return pd.read_csv(io.StringIO(text), dtype=str).fillna("")

    return pd.read_excel(io.BytesIO(content), dtype=str).fillna("")


@app.post("/download")
async def download(left: UploadFile = File(...), right: UploadFile = File(...)):

    df_left = await read_file(left)
    df_right = await read_file(right)

    result_df = run_gap_analysis(df_left, df_right)

    buffer = io.BytesIO()
    result_df.to_excel(buffer, index=False)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=gap_analysis.xlsx"}
    )


@app.post("/analyze")
async def analyze(left: UploadFile = File(...), right: UploadFile = File(...)):

    df_left = await read_file(left)
    df_right = await read_file(right)

    result_df = run_gap_analysis(df_left, df_right)

    gap_df = result_df[result_df["CID"] == "GAP"]

    gap_controls = generate_gap_controls_json(gap_df)

    return {
        "gap_analysis_download": "Use /download endpoint",
        "gap_controls": gap_controls
    }