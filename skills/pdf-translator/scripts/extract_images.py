import argparse
import sys
import os

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

def extract_images(pdf_path, output_dir):
    print(f"Extracting images from {pdf_path} to {output_dir}...")
    doc = fitz.open(pdf_path)
    image_count = 0
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for page_index in range(len(doc)):
        page = doc[page_index]
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list, start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            image_filename = f"image_p{page_index + 1}_{img_index}.{image_ext}"
            image_path = os.path.join(output_dir, image_filename)
            
            with open(image_path, "wb") as f:
                f.write(image_bytes)
                
            image_count += 1
            print(f"Saved {image_filename}")
            
    print(f"Successfully extracted {image_count} images.")

def main():
    parser = argparse.ArgumentParser(description="Extract images from PDF.")
    parser.add_argument("input_pdf", help="Path to the input PDF file")
    parser.add_argument("output_dir", help="Directory to save extracted images")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_pdf):
        print(f"Error: File '{args.input_pdf}' not found.")
        sys.exit(1)
        
    if not PYMUPDF_AVAILABLE:
        print("Error: PyMuPDF (fitz) is not installed.")
        print("Please install it running: pip install pymupdf")
        sys.exit(1)
        
    try:
        extract_images(args.input_pdf, args.output_dir)
    except Exception as e:
        print(f"Error extracting images: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
