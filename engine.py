import pandas as pd
import re

# Try to import sentence-transformers, fallback to simple matching if not available
try:
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer("all-MiniLM-L6-v2")
    USE_EMBEDDINGS = True
except ImportError:
    print("Warning: sentence-transformers not available, using simple text matching")
    model = None
    util = None
    USE_EMBEDDINGS = False

def clean_text(text):
    text = (text or "").lower()
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_numbers(text):
    """Extract all numbers from text with their context."""
    numbers = re.findall(r'\d+', str(text))
    return [int(n) for n in numbers]

def normalize_text_without_numbers(text):
    """Remove numbers from text for semantic comparison."""
    text = (text or "").lower()
    # Replace numbers with placeholder to maintain word boundaries
    text = re.sub(r'\d+', 'NUM', text)
    text = re.sub(r'[^a-z ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def find_keyword_differences(left_text, right_text):
    """Identify semantic keyword differences between controls."""
    left_lower = left_text.lower()
    right_lower = right_text.lower()
    
    differences = []
    
    # Common semantic variations
    variations = [
        (["older", "old"], ["unused", "inactive", "not used"]),
        (["enabled", "enable", "turned on"], ["disabled", "disable", "turned off"]),
        (["allow", "permit", "authorized"], ["deny", "block", "prevent"]),
        (["public", "exposed"], ["private", "internal"]),
        (["encrypted", "encryption"], ["unencrypted", "no encryption"]),
        (["secure", "secured"], ["insecure", "unsecured"]),
        (["must", "should", "ensure"], ["must not", "should not", "prevent"]),
    ]
    
    for group1, group2 in variations:
        found_left = any(word in left_lower for word in group1)
        found_right = any(word in right_lower for word in group2)
        
        if found_left and found_right:
            left_word = next((w for w in group1 if w in left_lower), group1[0])
            right_word = next((w for w in group2 if w in right_lower), group2[0])
            differences.append(f"'{left_word}' vs '{right_word}'")
        
        # Check opposite direction
        found_left2 = any(word in left_lower for word in group2)
        found_right2 = any(word in right_lower for word in group1)
        
        if found_left2 and found_right2:
            left_word = next((w for w in group2 if w in left_lower), group2[0])
            right_word = next((w for w in group1 if w in right_lower), group1[0])
            differences.append(f"'{left_word}' vs '{right_word}'")
    
    return differences

def compare_controls(left_text, right_text):
    """Compare two controls and identify numeric and semantic differences."""
    left_nums = extract_numbers(left_text)
    right_nums = extract_numbers(right_text)
    
    # Normalize without numbers for semantic comparison
    left_norm = normalize_text_without_numbers(left_text)
    right_norm = normalize_text_without_numbers(right_text)
    
    # Check if texts are similar when numbers are removed
    similarity_ratio = len(set(left_norm.split()) & set(right_norm.split())) / max(1, len(set(left_norm.split()) | set(right_norm.split())))
    
    comment = ""
    
    # Check for keyword differences
    keyword_diffs = find_keyword_differences(left_text, right_text)
    
    # Build comment based on differences found
    # Lower threshold since we're already past the matching threshold
    if similarity_ratio > 0.15 or keyword_diffs or (left_nums and right_nums):
        parts = []
        
        if left_nums != right_nums:
            if left_nums and right_nums:
                parts.append(f"numeric difference: {left_nums} vs {right_nums}")
            elif left_nums:
                parts.append(f"your control specifies {left_nums}, reference is generic")
            elif right_nums:
                parts.append(f"reference specifies {right_nums}, your control is generic")
        
        if keyword_diffs:
            parts.append(f"wording difference: {', '.join(keyword_diffs)}")
        
        if parts:
            comment = "Mapped with " + "; ".join(parts)
    
    return comment, similarity_ratio

def find_best_column(df, keywords):
    # Case-insensitive column matching
    for col in df.columns:
        col_lower = str(col).lower().strip()
        for kw in keywords:
            if kw.lower() in col_lower:
                return col
    return None

def run_gap_analysis(df_left, df_right):
    print(f"\n{'='*60}")
    print(f"Starting GAP Analysis")
    print(f"USE_EMBEDDINGS: {USE_EMBEDDINGS}")
    print(f"Left file rows: {len(df_left)}, Right file rows: {len(df_right)}")
    print(f"{'='*60}\n")

    policy_col_left = find_best_column(df_left, ["policy", "control", "rule", "name", "title"])
    policy_col_right = find_best_column(df_right, ["policy", "control", "rule", "name", "title"])
    cid_col_right = find_best_column(df_right, ["cid", "id"])

    if not policy_col_left or not policy_col_right or not cid_col_right:
        error_msg = f"Column detection failed. Found columns:\n"
        error_msg += f"Left file: {list(df_left.columns)}\n"
        error_msg += f"Right file: {list(df_right.columns)}\n"
        error_msg += f"Detected: policy_left={policy_col_left}, policy_right={policy_col_right}, cid_right={cid_col_right}"
        raise Exception(error_msg)

    right_names = []
    right_cids = []

    for _, r in df_right.iterrows():
        name = clean_text(r[policy_col_right])
        right_names.append(name)
        right_cids.append(r[cid_col_right])

    # Pre-compute embeddings only if available
    if USE_EMBEDDINGS:
        right_embeddings = model.encode(right_names, convert_to_tensor=True)
    else:
        right_embeddings = None

    output = []

    for _, left in df_left.iterrows():
        original = left[policy_col_left]
        clean_name = clean_text(original)

        cid_value = "GAP"
        comment = ""
        match_score = 0.0
        
        # Debug for access keys control
        is_access_keys = "access" in original.lower() and "key" in original.lower()
        if is_access_keys:
            print(f"\n=== Processing: '{original}' ===")
            print(f"Cleaned: '{clean_name}'")

        # Exact match
        if clean_name in right_names:
            idx = right_names.index(clean_name)
            cid_value = right_cids[idx]
            comment = "Exact match"
            match_score = 1.0
            if is_access_keys:
                print(f"✓ Exact match found!")

        else:
            if is_access_keys:
                print(f"No exact match, trying substring...")
            
            # Substring match
            for i, r_name in enumerate(right_names):
                if clean_name in r_name or r_name in clean_name:
                    cid_value = right_cids[i]
                    # Check for numeric differences
                    num_comment, _ = compare_controls(original, df_right.iloc[i][policy_col_right])
                    comment = num_comment if num_comment else "Substring match"
                    match_score = 0.9
                    if is_access_keys:
                        print(f"✓ Substring match found: '{df_right.iloc[i][policy_col_right]}'")
                    break
            
            if is_access_keys and cid_value == "GAP":
                print(f"No substring match, trying semantic...")

            # Semantic similarity match
            if cid_value == "GAP":
                if USE_EMBEDDINGS:
                    # Use embeddings for better matching
                    left_emb = model.encode(clean_name, convert_to_tensor=True)
                    scores = util.cos_sim(left_emb, right_embeddings)[0]

                    best_idx = scores.argmax().item()
                    best_score = scores[best_idx].item()
                else:
                    # Fallback: simple word overlap similarity with keyword boosting
                    left_words = set(normalize_text_without_numbers(original).split())
                    best_idx = 0
                    best_score = 0.0
                    
                    # Debug: print for access keys controls
                    if is_access_keys:
                        print(f"  Left words (normalized): {left_words}")
                        print(f"  Checking {len(right_names)} reference controls...")
                    
                    for i, r_name in enumerate(right_names):
                        right_words = set(normalize_text_without_numbers(df_right.iloc[i][policy_col_right]).split())
                        overlap = len(left_words & right_words)
                        total = len(left_words | right_words)
                        base_score = overlap / max(1, total)
                        
                        # Boost score if semantic keywords are found
                        keyword_diffs = find_keyword_differences(original, df_right.iloc[i][policy_col_right])
                        boost = 0.25 if keyword_diffs else 0.0  # 25% boost for semantic similarity
                        
                        # Additional boost if controls share core concepts AND have numeric differences
                        left_nums = extract_numbers(original)
                        right_nums = extract_numbers(df_right.iloc[i][policy_col_right])
                        
                        # Check if they share key resource words (like "access keys", "password", "encryption", etc.)
                        core_concepts = ['access key', 'password', 'encryption', 'rotation', 'mfa', 'backup', 
                                        'logging', 'monitoring', 'firewall', 'certificate', 'token']
                        shares_concept = any(concept in original.lower() and concept in df_right.iloc[i][policy_col_right].lower() 
                                            for concept in core_concepts)
                        
                        if shares_concept and left_nums and right_nums and left_nums != right_nums:
                            boost += 0.20  # Extra 20% boost for same concept with different numbers
                        
                        score = min(1.0, base_score + boost)
                        
                        # Debug logging for access keys control - show top 5 matches
                        if is_access_keys and i < 10:
                            right_title = df_right.iloc[i][policy_col_right]
                            if "access" in right_title.lower() or "key" in right_title.lower():
                                boost_msg = f" +{boost:.0%} boost" if boost > 0 else ""
                                print(f"  [{i}] '{right_title[:60]}...' - Score: {score:.2%}{boost_msg}")
                        
                        if score > best_score:
                            best_score = score
                            best_idx = i
                    
                    if is_access_keys:
                        print(f"  Best match: '{df_right.iloc[best_idx][policy_col_right]}' (score: {best_score:.2%})")
                        print(f"  Threshold: 50% (current score: {best_score:.2%})")
                
                if best_score > 0.60:  # Threshold at 60% to prevent false matches
                    cid_value = right_cids[best_idx]
                    match_score = best_score
                    
                    # Check for numeric and semantic differences
                    diff_comment, sim_ratio = compare_controls(original, df_right.iloc[best_idx][policy_col_right])
                    if diff_comment:
                        comment = diff_comment
                    elif best_score < 0.70:
                        # Lower confidence matches - add warning
                        comment = f"Possible match (similarity: {best_score:.2%}) - verify accuracy"
                    else:
                        comment = f"Semantic match (similarity: {best_score:.2%})"

        # Check for multi-resource controls (mentions multiple services)
        if cid_value != "GAP":
            # List of cloud service keywords
            service_keywords = ['s3', 'ec2', 'rds', 'lambda', 'iam', 'kms', 'cloudtrail', 'vpc', 
                               'storage', 'compute', 'database', 'sql', 'kubernetes', 'aks', 'gke',
                               'vm', 'virtual machine', 'api', 'cosmos', 'redis', 'service bus']
            
            # Count how many different services are mentioned
            services_found = [svc for svc in service_keywords if svc in original.lower()]
            
            # If multiple services mentioned, it might be too broad - mark as GAP for review
            if len(services_found) > 2:
                cid_value = "GAP"
                comment = f"Multi-resource control (mentions: {', '.join(services_found[:3])}) - requires manual review"
                match_score = 0.0
        
        # If still GAP, no match found
        if cid_value == "GAP" and not comment:
            comment = "No matching control found"

        output.append({
            "Title": original,
            "CID": cid_value,
            "Match": cid_value,
            "Comment": comment,
            "Match_Score": f"{match_score:.2%}" if match_score > 0 else "N/A"
        })

    return pd.DataFrame(output)