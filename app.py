import streamlit as st
import pandas as pd
import json
from engine import run_gap_analysis

st.set_page_config(page_title="Gap Analysis Tool", layout="wide")

st.title("🔐 Cloud Security Gap Analysis")

# File upload
left_file = st.file_uploader("Upload First File")
right_file = st.file_uploader("Upload Second File")


def read_any(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file, dtype=str).fillna("")
    else:
        return pd.read_excel(file, engine="openpyxl", dtype=str).fillna("")


# Run analysis
if st.button("🚀 Run Gap Analysis"):
    if left_file and right_file:
        df_left = read_any(left_file)
        df_right = read_any(right_file)

        with st.spinner("Processing..."):
            result_df = run_gap_analysis(df_left, df_right)

        st.session_state["gap_result"] = result_df
        st.success("✅ Analysis Complete")
    else:
        st.warning("Please upload both files")


# Show results
if "gap_result" not in st.session_state:
    st.info("Run analysis first")
else:
    result_df = st.session_state["gap_result"]

    st.dataframe(result_df)

    gap_df = result_df[result_df["CID"] == "GAP"]
    st.info(f"🔍 Found {len(gap_df)} GAP controls")

    col1, col2 = st.columns(2)

    # Download Excel
    with col1:
        st.download_button(
            "📥 Download Gap Excel",
            result_df.to_csv(index=False),
            "gap_analysis.csv"
        )

    # Generate JSON
    with col2:
        if st.button("🧠 Generate Control JSON"):
            from control_generator import generate_gap_controls_json

            if gap_df.empty:
                st.warning("No GAP controls found")
            else:
                with st.spinner("Generating..."):
                    controls = generate_gap_controls_json(gap_df)

                st.session_state["controls_json"] = controls


# Show JSON
if "controls_json" in st.session_state:
    st.subheader("Generated Control JSON")
    st.json(st.session_state["controls_json"])

    st.download_button(
        "📥 Download Control JSON",
        json.dumps(st.session_state["controls_json"], indent=2),
        "gap_controls.json"
    )