
import re
import unicodedata
from pathlib import Path

import pymupdf
import easyocr


# --------------------------------------------------
# 1. PROJECT CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

PDF_PATH = BASE_DIR / "docs" / "HR_POLICY.pdf"

# Initialize EasyOCR only once
print("Initializing EasyOCR...")

reader = easyocr.Reader(["en"], gpu=False)


# --------------------------------------------------
# 2. TEXT CLEANING
# --------------------------------------------------

def clean_text(text):

    # Normalize Unicode characters
    text = unicodedata.normalize("NFKC", text)

    # Remove unnecessary spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


# --------------------------------------------------
# 3. NORMAL PDF TEXT EXTRACTION
# --------------------------------------------------

def extract_normal_text(page):

    text = page.get_text("text")

    return clean_text(text)


# --------------------------------------------------
# 4. OCR EXTRACTION
# --------------------------------------------------

def extract_ocr_text(page):

    # Convert PDF page into an image at 300 DPI
    pix = page.get_pixmap(dpi=300)

    # Convert the image into PNG bytes
    image_bytes = pix.tobytes("png")

    # Run EasyOCR
    results = reader.readtext(
        image_bytes,
        detail=1,
        paragraph=False
    )

    extracted_lines = []

    for result in results:

        bounding_box, detected_text, confidence = result

        extracted_lines.append({
            "text": detected_text,
            "confidence": float(confidence),
            "box": bounding_box
        })

    # Sort detected text approximately from top to bottom,
    # then from left to right.
    extracted_lines.sort(
        key=lambda item: (
            round(min(point[1] for point in item["box"]) / 10),
            min(point[0] for point in item["box"])
        )
    )

    ocr_text = "\n".join(
        item["text"] for item in extracted_lines
    )

    ocr_text = clean_text(ocr_text)

    return ocr_text, extracted_lines


# --------------------------------------------------
# 5. PDF INGESTION PIPELINE
# --------------------------------------------------

def extract_pdf(pdf_path):

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            "The supplied file must be a PDF."
        )

    extracted_pages = []

    with pymupdf.open(pdf_path) as document:

        print("\nPDF:", pdf_path.name)
        print("Total pages:", len(document))

        for page_index, page in enumerate(document):

            page_number = page_index + 1

            print("\n" + "=" * 60)
            print("PROCESSING PAGE:", page_number)
            print("=" * 60)

            # Step A: Normal extraction
            normal_text = extract_normal_text(page)

            # Step B: Count embedded images
            image_count = len(
                page.get_images(full=True)
            )

            # Step C: OCR the entire page
            ocr_text, ocr_details = extract_ocr_text(page)

            # Step D: Display extraction diagnostics
            print("\nEmbedded images:", image_count)

            print(
                "Normal extraction characters:",
                len(normal_text)
            )

            print(
                "OCR extraction characters:",
                len(ocr_text)
            )

            print(
                "OCR detected text regions:",
                len(ocr_details)
            )

            # Step E: Display both extraction results
            print("\n--- NORMAL TEXT ---")

            if normal_text:
                print(normal_text)
            else:
                print("No normal text found.")

            print("\n--- OCR TEXT ---")

            if ocr_text:
                print(ocr_text)
            else:
                print("No OCR text recognized.")

            # Step F: Select the extraction result.
            # For this diagnostic version, prefer the result
            # containing more characters.
            if len(ocr_text) > len(normal_text):
                final_text = ocr_text
                extraction_method = "OCR"
            else:
                final_text = normal_text
                extraction_method = "NORMAL"

            final_text = clean_text(final_text)

            # Step G: Preserve page metadata
            if final_text:

                average_confidence = (
                    sum(
                        item["confidence"]
                        for item in ocr_details
                    ) / len(ocr_details)
                    if ocr_details else None
                )

                extracted_pages.append({

                    "text": final_text,

                    "source": pdf_path.name,

                    "page": page_number,

                    "extraction_method": extraction_method,

                    "ocr_average_confidence": average_confidence

                })

            else:

                print(
                    "\nWarning: No recognizable text "
                    "found on this page."
                )

    return extracted_pages


# --------------------------------------------------
# 6. MAIN PROGRAM
# --------------------------------------------------

if __name__ == "__main__":

    extracted_pages = extract_pdf(PDF_PATH)

    print("\n\n")
    print("=" * 60)
    print("FINAL EXTRACTION SUMMARY")
    print("=" * 60)

    print("Total extracted pages:", len(extracted_pages))

    for page in extracted_pages:

        print("\n" + "-" * 60)

        print("Source:", page["source"])

        print("Page:", page["page"])

        print(
            "Extraction method:",
            page["extraction_method"]
        )

        print(
            "OCR confidence:",
            page["ocr_average_confidence"]
        )

        print("\nExtracted text:")

        print(page["text"])

    print("\nPDF INGESTION COMPLETED.")
