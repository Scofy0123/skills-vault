---
name: pdf-translator
description: A comprehensive workflow for translating long-form PDF documents into structurally organized Markdown files. Supports auto-language detection, dual-language output, automatic chunking for long chapters, image extraction, and semantic verification using LLMs.
---

# PDF Long-form Translation Workflow

This skill provides a structured, 5-stage workflow for translating long-form PDF documents (like whitepapers, reports, or books) into Markdown files, split by chapter. Act as an active guide, walking users through the process.

## When to Offer This Workflow

**Trigger conditions:**
- User wants to "translate a PDF"
- User provides a long PDF and asks for translation to Chinese (or another language)
- User mentions "translate whitepaper", "translate report", etc.

## Stage 1: Exploration & Setup

**Goal:** Understand the environment, locate the document, and configure parameters.

1. **Locate PDF**: Ask the user for the absolute path to the PDF if not provided.
2. **Determine Target Language**: Ask the user what the target language should be (default is Chinese).
3. **Environment Check**: Verify if `pdfminer.six`, `pymupdf` (fitz) are installed. If not, ask the user for permission to install them (`pip install pdfminer.six pymupdf`).
4. **Setup Workspace**: Create a working directory for the output within the current directory (e.g., `<pdf_name>_translation/`), and an `images/` subfolder inside it.

## Stage 2: Extraction

**Goal:** Extract raw text and images from the PDF programmatically.

1. **Text Extraction**: Use the `extract_pdf.py` script provided in this skill's `scripts/` directory to extract the text. The script will output a text file containing the content with page number boundaries marked.
2. **Image Extraction**: Use the `extract_images.py` script in the `scripts/` directory to extract images from the PDF into the `images/` subfolder.
3. **Verify Extraction**: Check the output of `extract_pdf.py` to ensure the total page count matches the user's expectations or the PDF's actual length.

## Stage 3: Analysis & Planning

**Goal:** Analyze the extracted text, detect the source language, and plan the chapter splits.

1. **Language Detection**: Read the first few pages of the extracted text to automatically detect the source language. Inform the user (e.g., "Detected source language: English").
2. **Chapter Identification**: Analyze the table of contents or headers to identify logical chapter breaks.
3. **Word Count Evaluation**: Estimate the word/character count for each chapter.
   - The default maximum length per file is **8,000 characters/words**.
   - If a chapter exceeds this limit, plan to split it into `part1`, `part2`, etc.
4. **Confirm Plan**: Present the planned file structure to the user for confirmation before translating.

*Example Plan:*
```
whitepaper_ch01_{src_lang}.md
whitepaper_ch01_{tgt_lang}.md
whitepaper_ch02_part1_{src_lang}.md
whitepaper_ch02_part1_{tgt_lang}.md
...
```

## Stage 4: Translation & Generation

**Goal:** Generate the dual-language Markdown files.

For each planned chapter/part:
1. **Source File Generation**: Generate the `{src_lang}.md` file containing the raw extracted text for that section.
   - **Crucial**: Include a header at the top of the file: `> 📄 Original Document: <pdf_name> | Pages: p.X - p.Y`
   - Insert Markdown image tags `![Figure X](images/...)` where appropriate based on context or captions.
2. **Target File Generation**: Translate the source text and generate the `{tgt_lang}.md` file.
   - Follow the same header and image embedding rules.
   - Retain key technical terms in English (or source language) in parentheses during translation.

*Note: Process chapters sequentially. For very long documents, you may ask the user if they want to proceed in batches.*

## Stage 5: Verification

**Goal:** Verify the integrity and quality of the translation programmatically.

1. **Run Verification Script**: Execute the `verify_translation.py` script from the `scripts/` directory. This script takes the working directory and target language as arguments.
   - The script will perform structural checks (file counts, page headers, limits).
   - The script will also automatically sample paragraphs from the source files, prompt YOU (the LM) via a special hidden subprocess or via the terminal to translate them, and then compare the result against the actual target files.
2. **Report Results**: Parse the JSON output from `verify_translation.py` and present the findings to the user.
   - Confirm structural integrity.
   - Present the Semantic Match Score for the sampled paragraphs.
3. **Final Polish**: If the script identifies missing figure links or structural gaps, fix them before concluding the task.
