import pdfplumber
import re
import json

pdf_path = "ISTQB_CTAL-TTA_Sample-Exam-Questions_v4.2.pdf"



# Step 1: Read all text from PDF
full_text = ""
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages[6:]:
        full_text += page.extract_text(x_tolerance=1, y_tolerance=1,layout=True) +'\n'

# Step 2: Define regex to capture each question block
# Starts with "Question #<number> (<points> Points)"
# Ends with "Select ONE option." or "Select TWO options."
pattern = re.compile(
    r'(Question #[X]?\d+ \(\d+ Point[s]?\).*?Select (?:ONE|TWO) option[s]??\.)',
    re.DOTALL
)

# Step 3: Find all question blocks
question_blocks = pattern.findall(full_text)
print(f"Found {len(question_blocks)} question blocks")




questions = {}
for block in question_blocks:

    print(block)
    # Extract question number
    num_match = re.search(r'Question #([X]?\d+)', block)
    qnum = num_match.group(1) if num_match else None

    # Extract points
    pts_match = re.search(r'\((\d+) Point[s]?\)', block)
    points = int(pts_match.group(1)) if pts_match else 1

    # Extract number of correct answers
    sel_match = re.search(r'Select (\w+) option[s]?', block)
    num_correct = 1 if sel_match and sel_match.group(1).upper() == "ONE" else 2

    # Extract question text
    q_text_match = re.search(r'(Question #[X]?\d+ \(\d+ Point[s]?\)(.*?)Select (?:ONE|TWO) option[s]??\.)', block, re.DOTALL)
    core = q_text_match.group(2).strip() if q_text_match else "Unknown question"

    split_pattern = re.compile(r'(?=\n?[a]\))')
    parts = re.split(split_pattern, core.strip(), maxsplit=1)
    
    if len(parts) == 2:

        question_text = parts[0].strip()
        options_text = parts[1]
    else:
        question_text = core.strip()
        options_text = ""
   
    option_pattern = re.compile(
        r'(?:^|\s)([a-zA-Z])\)\s*([^a-zA-Z]*?)(?=(?:\s[a-zA-Z]\))|\Z)',
        re.DOTALL
    )

    options = {}
    for m in option_pattern.finditer(options_text):
        label = m.group(1).upper()
        text_opt = re.sub(r'\s+', ' ', m.group(2).strip())
        if text_opt:
            options[label] = text_opt

    # Fallback: if only one key detected, retry more generously
    if len(options) <= 1:
        # Split on lowercase or uppercase + ")" followed by space
        parts = re.split(r'([a-zA-Z]\))', options_text)
        merged = []
        for i in range(1, len(parts), 2):
            key = parts[i][0].upper()
            val = parts[i+1] if i+1 < len(parts) else ""
            val = re.sub(r'\s+', ' ', val.strip())
            merged.append((key, val))
        options = dict(merged)

    questions[qnum]={
        "question_id": qnum,
        "points": points,
        "question_text": question_text.strip(),
        "options": options,
        "select_count": num_correct
    }
print(f"Extracted {len(questions)} question blocks")

    



pdf_path='ISTQB_CTAL-TTA_Sample-Exam-Answers_v4.2.pdf'



"""
<spaces><number><spaces><answers><spaces><first line of explanation><LO> <K> <points>
   <continuation lines of explanations>


"""

def read_pdf_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[7:]:
            t = page.extract_text(x_tolerance=1, y_tolerance=1, layout=True)
            if t:
                text += t + "\n"
    return text

text = read_pdf_text(pdf_path)

# Clean up header/footer junk
# Remove titles, sample exam labels, and page footers
text = re.sub(r'Technical Test Analyst, Advanced Level.*?(?=\n)', '', text)
text = re.sub(r'Sample Exam.*?(?=\n)', '', text)
text = re.sub(r'^\s*–+\s*$', '', text, flags=re.MULTILINE)
text = re.sub(r'©.*?Page \d+.*?\n', '', text)
text = re.sub(r'^\s*$', '', text, flags=re.MULTILINE)
text = re.sub(r'^\s*Answers\s*$', '', text, flags=re.MULTILINE)
text =re.sub(r'Version 4.2\s+Page.*?Board','', text,flags=re.DOTALL )
text = re.sub(r'Question\s+Correct.*?Points', '', text, flags=re.DOTALL)



print(text)

# --- 2️⃣ SPLIT INTO QUESTION BLOCKS ---
lines = text.splitlines()
blocks = []
current_block = []

for line in lines:
    # Start of new question: "1 a,b ..." or "X1 d ..."
    if re.match(r'^\s*(X?\d+)\s+[a-eA-E, ]+\s+', line):
        if current_block:
            blocks.append("\n".join(current_block))
            current_block = []
    if line.strip():
        current_block.append(line.rstrip())
if current_block:
    blocks.append("\n".join(current_block))

print(f"✅ Detected {len(blocks)} question blocks")

# --- 3️⃣ PARSE BLOCKS ---
final_questions = []

for block in blocks:
    # Question ID (supports X1, X2, etc.)
    num_match = re.match(r'^\s*(X?\d+)', block)
    qid = num_match.group(1).strip() if num_match else None
    print(block)
    print(qid)

    # Correct answers (a,b,c…)
    ans_match = re.search(r'^\s*X?\d+\s+([a-eA-E, ]+)\s+[aA]\)', block)
    answers = []
    if ans_match:
        answers = [a.strip().upper() for a in re.split(r'[, ]+', ans_match.group(1)) if a.strip()]

    # Learning Objective, K-level, Points
    lo_match = re.search(r'(TTA-\d+\.\d+\.\d+)\s+(K\d)\s+(\d+)', block)
    lo = lo_match.group(1) if lo_match else None
    klevel = lo_match.group(2) if lo_match else None
    points = int(lo_match.group(3)) if lo_match else 1

    # --- Keep entire explanation text ---
    # Remove the header "1 a,b ..." or "X1 d ..."
    explanation = re.sub(r'^\s*(X?\d+)\s+[a-eA-E, ]+\s+', '', block, count=1).strip()

    final_questions.append({
        "question_id": qid,
        "question_text": questions[qid]['question_text']+ '\n Select '+ str(questions[qid]['select_count'])+ ' option(s).' ,
        "options": questions[qid]['options'],
        "answers": answers,
        "explanation": explanation,
        "learning_objective": lo,
        "klevel": klevel,
        "points": points
    })

print(f"✅ Parsed {len(final_questions)} question entries")

# --- 4️⃣ SAVE OUTPUT ---
with open("tta_answer_key_full_explanation.json", "w", encoding="utf-8") as f:
    json.dump(final_questions, f, ensure_ascii=False, indent=2)

print("🎯 Output saved to tta_answer_key_full_explanation.json")