
import re


# --------------------------------------------------
# CHUNKING CONFIGURATION
# --------------------------------------------------

MAX_CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
MIN_CHUNK_SIZE = 100


# --------------------------------------------------
# 1. CLEAN TEXT
# --------------------------------------------------

def clean_text(text):

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Normalize spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Normalize excessive blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


# --------------------------------------------------
# 2. IDENTIFY HEADINGS
# --------------------------------------------------

def is_heading(line):

    line = line.strip()

    if not line:
        return False

    # Markdown headings
    if line.startswith("#"):
        return True

    # Short uppercase headings
    if len(line) <= 70 and line.isupper():
        return True

    return False


# --------------------------------------------------
# 3. SPLIT TEXT INTO UNITS
# --------------------------------------------------

def split_into_units(text):

    paragraphs = re.split(r"\n\s*\n", text)

    units = []

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        # Keep headings as separate units
        if is_heading(paragraph):
            units.append(paragraph)
            continue

        # OCR often returns one line per detected text region.
        # Preserve those lines as units rather than treating
        # every line as an independent semantic paragraph.
        lines = [
            line.strip()
            for line in paragraph.splitlines()
            if line.strip()
        ]

        units.extend(lines)

    return units


# --------------------------------------------------
# 4. SPLIT VERY LONG UNITS
# --------------------------------------------------

def split_long_unit(text, max_size):

    chunks = []

    start = 0

    while start < len(text):

        end = start + max_size

        if end < len(text):

            # Prefer splitting at a sentence boundary
            sentence_end = max(
                text.rfind(". ", start, end),
                text.rfind("? ", start, end),
                text.rfind("! ", start, end)
            )

            # Otherwise prefer a word boundary
            if sentence_end > start:
                end = sentence_end + 1

            else:
                space_position = text.rfind(
                    " ",
                    start,
                    end
                )

                if space_position > start:
                    end = space_position

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(0, end - CHUNK_OVERLAP)

    return chunks


# --------------------------------------------------
# 5. BUILD STRUCTURE-AWARE CHUNKS
# --------------------------------------------------

def create_chunks(page_data):

    text = clean_text(page_data["text"])

    source = page_data["source"]

    page_number = page_data["page"]

    extraction_method = page_data.get(
        "extraction_method",
        "unknown"
    )

    ocr_confidence = page_data.get(
        "ocr_average_confidence"
    )

    units = split_into_units(text)

    chunks = []

    current_heading = "General"

    current_units = []

    current_length = 0

    def save_chunk():

        nonlocal current_units
        nonlocal current_length

        if not current_units:
            return

        chunk_text = "\n".join(current_units).strip()

        if not chunk_text:
            return

        chunks.append({

            "text": chunk_text,

            "metadata": {

                "source": source,

                "page": int(page_number),

                "heading": current_heading,

                "extraction_method": extraction_method,

                "ocr_confidence": (
                    float(ocr_confidence)
                    if ocr_confidence is not None
                    else -1.0
                ),

                "chunk_id": len(chunks),

                "char_count": len(chunk_text)

            }

        })

        current_units = []

        current_length = 0

    for unit in units:

        # Update the current heading
        if is_heading(unit):

            save_chunk()

            current_heading = unit.strip("# ").strip()

            continue

        # Split units that are too long
        if len(unit) > MAX_CHUNK_SIZE:

            save_chunk()

            long_chunks = split_long_unit(
                unit,
                MAX_CHUNK_SIZE
            )

            for part in long_chunks:

                chunks.append({

                    "text": part,

                    "metadata": {

                        "source": source,

                        "page": int(page_number),

                        "heading": current_heading,

                        "extraction_method": extraction_method,

                        "ocr_confidence": (
                            float(ocr_confidence)
                            if ocr_confidence is not None
                            else -1.0
                        ),

                        "chunk_id": len(chunks),

                        "char_count": len(part)

                    }

                })

            continue

        added_length = len(unit) + 1

        # Save current chunk if adding the next unit
        # would exceed the maximum chunk size
        if (
            current_length + added_length
            > MAX_CHUNK_SIZE
        ):

            save_chunk()

            # Carry a small amount of previous context
            # into the next chunk
            if chunks:

                previous_text = chunks[-1]["text"]

                overlap_text = previous_text[
                    -CHUNK_OVERLAP:
                ].strip()

                if overlap_text:

                    current_units = [overlap_text]

                    current_length = len(overlap_text)

        current_units.append(unit)

        current_length += added_length

    save_chunk()

    # Merge an extremely small final chunk into the
    # previous chunk when they share the same page/heading.
    if len(chunks) >= 2:

        last_chunk = chunks[-1]

        previous_chunk = chunks[-2]

        if (
            len(last_chunk["text"]) < MIN_CHUNK_SIZE
            and last_chunk["metadata"]["heading"]
            == previous_chunk["metadata"]["heading"]
        ):

            combined_text = (
                previous_chunk["text"]
                + "\n"
                + last_chunk["text"]
            )

            if len(combined_text) <= MAX_CHUNK_SIZE:

                previous_chunk["text"] = combined_text

                previous_chunk["metadata"]["char_count"] = (
                    len(combined_text)
                )

                chunks.pop()

    return chunks


# --------------------------------------------------
# 6. PROCESS ALL EXTRACTED PAGES
# --------------------------------------------------

def chunk_pages(extracted_pages):

    all_chunks = []

    for page_data in extracted_pages:

        page_chunks = create_chunks(page_data)

        all_chunks.extend(page_chunks)

    return all_chunks
