from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd
import io

from engine import run_gap_analysis
from control_generator import generate_gap_controls_json

app = FastAPI()


async def read_file(upload: UploadFile) -> pd.DataFrame:
    filename = (upload.filename or "").lower()
    content = await upload.read()

    if filename.endswith(".csv"):
        text = content.decode("utf-8", errors="ignore")
        return pd.read_csv(io.StringIO(text), dtype=str).fillna("")

    return pd.read_excel(io.BytesIO(content), dtype=str).fillna("")


@app.post("/analyze")
async def analyze(left: UploadFile = File(...), right: UploadFile = File(...)):

    df_left = await read_file(left)
    df_right = await read_file(right)

    # 1️⃣ Run gap analysis
    result_df = run_gap_analysis(df_left, df_right)

    # 2️⃣ Extract GAP rows
    gap_df = result_df[result_df["CID"] == "GAP"]

    # 3️⃣ Generate JSON controls
    gap_controls = generate_gap_controls_json(gap_df)

    # 4️⃣ Create Excel file
    buffer = io.BytesIO()
    result_df.to_excel(buffer, index=False)
    buffer.seek(0)

    return {
        "gap_analysis_download": "Use /download endpoint",
        "gap_controls": gap_controls
    }


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