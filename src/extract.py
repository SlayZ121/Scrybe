import fitz  # PyMuPDF
import statistics
from collections import Counter
import re
from collections import defaultdict

def normalize_font_name(font_name):
    return font_name.split(",")[0].strip()

def group_blocks_into_rows(blocks, y_tolerance=2):
    rows = defaultdict(list)
    for block in blocks:
        y_key = round(block["y0"] / y_tolerance) * y_tolerance
        rows[y_key].append(block)
    return list(rows.values())

def detect_table_like_groups(rows, x_tolerance=5):
    column_patterns = defaultdict(list)

    for row in rows:
        x_positions = sorted([round((b["x0"] + b["x1"]) / 2) for b in row])
        key = tuple([round(x / x_tolerance) * x_tolerance for x in x_positions])
        if len(key) > 1:
            column_patterns[key].append(row)

    tables = [rows for key, rows in column_patterns.items() if len(rows) >= 3]
    return tables

def flatten_table_blocks(tables):
    return [block for table in tables for row in table for block in row]



def normalize(text):
    # Lowercase, remove punctuation, strip whitespace
    return re.sub(r'[^\w\s]', '', text.lower()).strip()

def is_duplicate_title(heading_text, title_text):
    return normalize(heading_text) == normalize(title_text)

def is_decorative_text(text):
    disallowed_keywords = [
        "copyright", "issued", "published", "approved", "confidential"
    ]
    lower_text = text.lower()
    for keyword in disallowed_keywords:
        if re.search(rf"\b{re.escape(keyword)}\b", lower_text):
            return True
    return False

def has_good_follower(i, blocks, body_font):
    for j in range(i + 1, min(i + 3, len(blocks))):
        follower = blocks[j]
        fsize = follower["font_size"]
        ftext = follower["text"].strip()
        fwords = ftext.split()

        if is_decorative_text(ftext):
            return False

        if fsize >= body_font and len(fwords) < 10:
            return True
        if fsize >= body_font and len(fwords) >= 10:
            return True

    return False

def determine_heading_level(i, blocks, body_font, h1_font, h2_font):
    current = blocks[i]
    text = current["text"].strip()
    size = current["font_size"]

    if re.search(r"\b\d+\s*$", text):
       return None
    
    if re.search(r"\s{2,}", text):
        return None

    if re.search(r"[•\-*·•◦‣∙⦁]", text):
     return None
    
    if not re.match(r"^[A-Z0-9]", text):
        return None
    
    next = blocks[i + 1] if i + 1 < len(blocks) else None
    if next and current["page"] == next["page"]:
        same_line_threshold = 3.0  # px
        if abs(current["y0"] - next["y0"]) <= same_line_threshold:
            return None

    allowed_short_words = {"to", "of", "in", "on", "by", "at", "up", "an", "as", "or", "if", "is", "be", "a","it",",","ll","re","s"}
    words = re.findall(r"\b\w+(?:'\w+)?\b", text.lower())
    for word in words:
        if len(word) <= 2 and word not in allowed_short_words and not word.isdigit():
            return None

    disallowed_keywords = {"version", "remarks", "confidential", "appendix", "draft","please"}
    lower_text = text.lower()
    if any(kw in lower_text for kw in disallowed_keywords):
        return None

    if re.search(r"/\s", text):
        return None

    if '"' in text:
        return None

    if ":" in text and not text.strip().endswith(":"):
        return None
    
    if text.strip().endswith("."):
        return None

    is_bold = "bold" in current["font_name"].lower()
    is_all_caps = text.isupper() and len(text.split()) <= 6
    is_short = len(text.split()) <= 15
    y0 = current["y0"]

    prev = blocks[i - 1] if i > 0 else None
    next = blocks[i + 1] if i + 1 < len(blocks) else None
    spacing_above = (
        current["y0"] - prev["y1"]
        if prev and current["page"] == prev["page"]
        else 0
    )
    spacing_below = (
        next["y0"] - current["y1"]
        if next and current["page"] == next["page"]
        else 0
    )

    
    if size >= body_font and is_short and spacing_above > 150:
        return "H1"

    if size >= body_font and spacing_above>=10 and spacing_below>=5 and is_short:
        return "H2"

    if  size>=body_font and is_short and spacing_above >=10 and spacing_below > 15:
        return "H3"

    return None


def extract_outline(pdf_path):
    doc = fitz.open(pdf_path)
    blocks = []

    for page_num, page in enumerate(doc, start=1):
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                text = ""
                font_sizes = []
                font_names = []
                bbox = line["bbox"]
                for span in line["spans"]:
                    text += span["text"]
                    font_sizes.append(span["size"])
                    font_names.append(span["font"])
                clean_text = text
                if clean_text:
                    avg_size = statistics.mean(font_sizes)
                    primary_font = font_names[0] if font_names else "Unknown"
                    blocks.append({
                        "text": clean_text,
                        "font_size": round(avg_size, 2),
                        "font_name": primary_font,
                        "page": page_num - 1,
                        "x0": bbox[0],
                        "x1": bbox[2],
                        "y0": bbox[1],
                        "y1": bbox[3]
                    })



    rows = group_blocks_into_rows(blocks)
    tables = detect_table_like_groups(rows)
    table_blocks = flatten_table_blocks(tables)
    blocks = [b for b in blocks if b not in table_blocks]

    if not blocks:
        return {"title": "", "outline": []}
    
    

    merged_blocks = []
    skip_next = False
    for i in range(len(blocks)):
        if skip_next:
            skip_next = False
            continue
        current = blocks[i]
        merged_text = current["text"]
        font_size = current["font_size"]
        font_name = current["font_name"]
        page = current["page"]
        y1 = current["y1"]

        if i + 1 < len(blocks):
            next_block = blocks[i + 1]
            same_font = next_block["font_size"] == font_size
            same_style = normalize_font_name(next_block["font_name"]) == normalize_font_name(font_name)
            same_page = next_block["page"] == page
            close_vertically = abs(next_block["y0"] - y1) < 30
            
            if same_font and same_style and same_page and close_vertically:
                merged_text += next_block["text"]
                skip_next = True
            

        merged_blocks.append({
            "text": merged_text,
            "font_size": font_size,
            "font_name": font_name,
            "page": page,
            "x0": current["x0"],
            "x1": current["x1"],
            "y0": current["y0"],
            "y1": current["y1"]
        })


    font_counter = Counter(b["font_size"] for b in merged_blocks)
    body_font = font_counter.most_common(1)[0][0]

    cleaned_blocks = []
    for i, block in enumerate(merged_blocks):
        size = block["font_size"]
        text = block["text"]
        if size >= body_font:
            if has_good_follower(i, merged_blocks, body_font):
                cleaned_blocks.append(block)
        else:
            cleaned_blocks.append(block)

    filtered_font_counter = Counter(b["font_size"] for b in cleaned_blocks)
    font_ranks = sorted(set(filtered_font_counter.keys()), reverse=True)

    title_font = font_ranks[0]
    h1_font = font_ranks[1] if len(font_ranks) > 1 else title_font
    h2_font = font_ranks[2] if len(font_ranks) > 2 else h1_font

    skip_outline = h1_font == h2_font

    title = ""
    title_block = None
    outline = []
    seen = set()

    for i, block in enumerate(cleaned_blocks):
        text = block["text"]
        size = block["font_size"]
        page = block["page"]

        if not title and size == title_font:
            title = text
            title_block = block
            continue

        if skip_outline:
            continue

        level = determine_heading_level(i, cleaned_blocks, body_font, h1_font, h2_font)

        if level:
            if re.fullmatch(r"[.\-•*·\s]+", text):
             continue

            if re.search(r"\d+$", text):
             continue

            key = (text.lower(), page)
            if key not in seen:
             seen.add(key)
             outline.append({
            "level": level,
            "text": text,
            "page": page
        })



    existing_keys = set((item["text"].lower(), item["page"]) for item in outline)
    for i in reversed(range(len(cleaned_blocks))):
        block = cleaned_blocks[i]
        text = block["text"]
        page = block["page"]
        size = block["font_size"]
        words = text.split()

        if len(words) < 15 or (text.lower(), page) in existing_keys:
            continue

        for j in range(i - 1, max(i - 4, -1), -1):
            candidate = cleaned_blocks[j]
            cand_text = candidate["text"]
            cand_words = cand_text.split()
            cand_size = candidate["font_size"]

            if (
            len(cand_words) <= 10 and
            "bold" in candidate["font_name"].lower() and
            abs(block["y0"] - candidate["y1"]) > 10 and
            (cand_text.lower(), candidate["page"]) not in existing_keys
        ):
                level = determine_heading_level(j, cleaned_blocks, body_font, h1_font, h2_font)
                if level:
                    outline.append({
                    "level": level,
                    "text": cand_text,
                    "page": candidate["page"]
                })
                    existing_keys.add((cand_text.lower(), candidate["page"]))
                break


    

    outline = [entry for entry in outline if not is_duplicate_title(entry["text"], title)]
        # Sort outline by page and y-coordinate
    outline.sort(key=lambda x: (x["page"], next(
        (b["y0"] for b in cleaned_blocks if b["text"] == x["text"] and b["page"] == x["page"]), 0.0
    )))

    # Now attach section text for each heading
    outline_with_text = []
    for idx, heading in enumerate(outline):
        current_page = heading["page"]
        current_text = heading["text"]

        # Start position
        start_index = next((i for i, b in enumerate(cleaned_blocks)
                            if normalize(b["text"]) == normalize(current_text) and b["page"] == current_page
), None)
        if start_index is None:
            continue

        # End position: next heading (or end of doc)
        if idx + 1 < len(outline):
            next_heading = outline[idx + 1]
            end_index = next((i for i, b in enumerate(cleaned_blocks)
                              if b["text"] == next_heading["text"] and b["page"] == next_heading["page"]), len(cleaned_blocks))
        else:
            end_index = len(cleaned_blocks)

        # Get section text from in-between blocks
        section_blocks = cleaned_blocks[start_index + 1:end_index]
        section_text = " ".join([b["text"].strip() for b in section_blocks if b["text"].strip()])
        section_text = re.sub(r'\s+', ' ', section_text).strip()

        outline_with_text.append({
            "level": heading["level"],
            "text": heading["text"],
            "page": heading["page"],
            "section_text": section_text
        })

    if h1_font ==h2_font and h2_font==body_font:
        return {
            "title":title,
            "outline": outline_with_text
        }

    


    if title and title_block:
        title_page = title_block["page"]
        title_index = cleaned_blocks.index(title_block)
        earlier_h1_h2 = any(
            (b["font_size"] in {h1_font, h2_font} and cleaned_blocks.index(b) < title_index)
            for b in cleaned_blocks
        )
        if earlier_h1_h2:
            return {
                "title": "",
                "outline": [{
                    "level": "H1",
                    "text": title,
                    "page": title_page
                }] 
            }
        else:
            
            return {"title": title, "outline": outline_with_text}
    else:
        return {"title": title, "outline": outline_with_text}
