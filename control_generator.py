from ai_control_generator import generate_control_ai

def generate_gap_controls_json(gap_df):

    output = []

    for _, row in gap_df.iterrows():

        # Dynamic column detection
        title = str(row.iloc[0]).strip()

        if not title:
            continue

        control = generate_control_ai(title)

        output.append(control)

    return output