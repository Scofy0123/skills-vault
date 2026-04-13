import argparse
import sys
import os
import glob
import re
import json
import random

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

def check_file_pairing(directory, src_lang, tgt_lang):
    src_files = sorted(glob.glob(os.path.join(directory, f"*_{src_lang}.md")))
    tgt_files = sorted(glob.glob(os.path.join(directory, f"*_{tgt_lang}.md")))
    
    src_bases = [os.path.basename(f).replace(f"_{src_lang}.md", "") for f in src_files]
    tgt_bases = [os.path.basename(f).replace(f"_{tgt_lang}.md", "") for f in tgt_files]
    
    missing_tgt = set(src_bases) - set(tgt_bases)
    missing_src = set(tgt_bases) - set(src_bases)
    
    return {
        "status": len(missing_tgt) == 0 and len(missing_src) == 0,
        "src_files_count": len(src_files),
        "tgt_files_count": len(tgt_files),
        "missing_translations": list(missing_tgt),
        "orphan_translations": list(missing_src)
    }

def check_file_constraints(directory, tgt_lang, max_chars=8000):
    tgt_files = sorted(glob.glob(os.path.join(directory, f"*_{tgt_lang}.md")))
    results = []
    
    for fpath in tgt_files:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        has_page_header = bool(re.search(r"📄.*页码", content) or re.search(r> ".*p\.\d+ - p\.\d+", content))
        char_count = len(content)
        is_over_limit = char_count > max_chars
        
        results.append({
            "file": os.path.basename(fpath),
            "has_page_header": has_page_header,
            "char_count": char_count,
            "is_over_limit": is_over_limit
        })
        
    all_headers = all(r["has_page_header"] for r in results)
    all_under_limit = all(not r["is_over_limit"] for r in results)
    
    return {
        "status": all_headers and all_under_limit,
        "details": results
    }

def semantic_verification(directory, src_lang, tgt_lang, target_file_base):
    if not GENAI_AVAILABLE or not os.environ.get("GEMINI_API_KEY"):
        return {"status": "skipped", "reason": "google-generativeai installed or GEMINI_API_KEY not set"}
        
    src_file = os.path.join(directory, f"{target_file_base}_{src_lang}.md")
    tgt_file = os.path.join(directory, f"{target_file_base}_{tgt_lang}.md")
    
    if not os.path.exists(src_file) or not os.path.exists(tgt_file):
        return {"status": "error", "reason": "Files not found"}
        
    with open(src_file, 'r', encoding='utf-8') as f:
        src_content = f.read()
        
    paragraphs = [p.strip() for p in src_content.split('\n\n') if len(p.strip()) > 100]
    if not paragraphs:
        return {"status": "error", "reason": "No suitable paragraphs found in source"}
        
    sample = random.choice(paragraphs)
    
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-pro")
    
    try:
        # Step 1: Independent Translation
        translation_prompt = f"Translate the following paragraph to {tgt_lang} accurately:\n\n{sample}"
        independent_translation = model.generate_content(translation_prompt).text
        
        with open(tgt_file, 'r', encoding='utf-8') as f:
            tgt_content = f.read()
            
        # Step 2: Semantic Comparison
        eval_prompt = f"""
Compare the 'Independent Translation' with the 'Target File Content' to determine if the semantic meaning of the original paragraph is accurately and fully represented in the Target File.
Original Source Paragraph: {sample}
Independent Translation: {independent_translation}
Target File Content: {tgt_content}

Provide your analysis in JSON format with the following keys:
- 'found_in_target': boolean, whether the paragraph exists in the target file
- 'accuracy_score': int, 1-10
- 'completeness_score': int, 1-10
- 'explanation': string, brief reasoning
"""
        eval_result = model.generate_content(eval_prompt).text
        
        match = re.search(r'\{.*\}', eval_result, re.DOTALL)
        if match:
            json_eval = json.loads(match.group(0))
        else:
            json_eval = {"raw_eval": eval_result}
            
        return {
            "status": "success",
            "sample_source": sample[:100] + "...",
            "evaluation": json_eval
        }
        
    except Exception as e:
        return {"status": "error", "reason": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Verify PDF translation outputs.")
    parser.add_argument("directory", help="Directory containing the translated files")
    parser.add_argument("--src-lang", default="english", help="Source language suffix (default: english)")
    parser.add_argument("--tgt-lang", default="chinese", help="Target language suffix (default: chinese)")
    parser.add_argument("--semantic-check-file", help="Base name of file to run semantic check on (e.g., whitepaper_ch01)")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' not found.")
        sys.exit(1)
        
    results = {}
    
    print("Running File Pairing Check...")
    results["file_pairing"] = check_file_pairing(args.directory, args.src_lang, args.tgt_lang)
    
    print("Running File Constraints Check...")
    results["file_constraints"] = check_file_constraints(args.directory, args.tgt_lang)
    
    if args.semantic_check_file:
        print(f"Running Semantic Verification on {args.semantic_check_file}...")
        results["semantic_verification"] = semantic_verification(args.directory, args.src_lang, args.tgt_lang, args.semantic_check_file)
        
    print("\n--- RESULTS ---")
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
