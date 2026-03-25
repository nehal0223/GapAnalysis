import pandas as pd
import re
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def clean_text(text):
    text = (text or "").lower()
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def find_best_column(df, keywords):
    for col in df.columns:
        for kw in keywords:
            if kw in col:
                return col
    return None

def run_gap_analysis(df_left, df_right):

    policy_col_left = find_best_column(df_left, ["policy", "control", "rule", "name", "title"])
    policy_col_right = find_best_column(df_right, ["policy", "control", "rule", "name", "title"])
    cid_col_right = find_best_column(df_right, ["cid", "id"])

    if not policy_col_left or not policy_col_right or not cid_col_right:
        raise Exception("Column detection failed")

    right_names = []
    right_cids = []

    for _, r in df_right.iterrows():
        name = clean_text(r[policy_col_right])
        right_names.append(name)
        right_cids.append(r[cid_col_right])

    right_embeddings = model.encode(right_names, convert_to_tensor=True)

    output = []

    for _, left in df_left.iterrows():
        original = left[policy_col_left]
        clean_name = clean_text(original)

        cid_value = "GAP"

        if clean_name in right_names:
            cid_value = right_cids[right_names.index(clean_name)]

        else:
            for i, r_name in enumerate(right_names):
                if clean_name in r_name or r_name in clean_name:
                    cid_value = right_cids[i]
                    break

            if cid_value == "GAP":
                left_emb = model.encode(clean_name, convert_to_tensor=True)
                scores = util.cos_sim(left_emb, right_embeddings)[0]

                best_idx = scores.argmax().item()
                if scores[best_idx] > 0.75:
                    cid_value = right_cids[best_idx]

        output.append({
            "Title": original,
            "CID": cid_value,
            "Match": cid_value
        })

    return pd.DataFrame(output)