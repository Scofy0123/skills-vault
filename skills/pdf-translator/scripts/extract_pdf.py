import argparse
import sys
import os

try:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

def extract_with_pdfminer(pdf_path, output_path):
    print(f"Using pdfminer.six to extract {pdf_path}...")
    page_count = 0
    full_text = []
    
    for page_layout in extract_pages(pdf_path):
        page_count += 1
        page_text = f"\n\n--- Page {page_count} ---\n\n"
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                page_text += element.get_text()
        full_text.append(page_text)
        
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("".join(full_text))
        
    return page_count

def extract_with_pypdf(pdf_path, output_path):
    print(f"Using pypdf to extract {pdf_path}...")
    reader = PdfReader(pdf_path)
    page_count = len(reader.pages)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, page in enumerate(reader.pages):
            f.write(f"\n\n--- Page {i + 1} ---\n\n")
            text = page.extract_text()
            if text:
                f.write(text)
                
    return page_count

def main():
    parser = argparse.ArgumentParser(description="Extract text from PDF with page numbers.")
    parser.add_argument("input_pdf", help="Path to the input PDF file")
    parser.add_argument("output_txt", help="Path to the output text file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_pdf):
        print(f"Error: File '{args.input_pdf}' not found.")
        sys.exit(1)
        
    try:
        if PDFMINER_AVAILABLE:
            page_count = extract_with_pdfminer(args.input_pdf, args.output_txt)
        elif PYPDF_AVAILABLE:
            page_count = extract_with_pypdf(args.input_pdf, args.output_txt)
        else:
            print("Error: Neither pdfminer.six nor pypdf is installed.")
            print("Please install one: pip install pdfminer.six OR pip install pypdf")
            sys.exit(1)
            
        print(f"Successfully extracted {page_count} pages to {args.output_txt}")
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
