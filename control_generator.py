from ai_control_generator import generate_control_ai

def generate_gap_controls_json(gap_df):

    output = []
    gap_counter = 1

    for _, row in gap_df.iterrows():

        # Dynamic column detection
        title = str(row.iloc[0]).strip()

        if not title:
            continue

        control = generate_control_ai(title)
        
        # Override control_id with sequential GAP numbering
        if control.get("control_id") in ("generated", "parse_error", "llm_not_configured", ""):
            control["control_id"] = f"gap_{gap_counter}"
        
        gap_counter += 1
        output.append(control)

    return output