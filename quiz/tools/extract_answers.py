
pdf_path='ISTQB_CTAL-TTA_Sample-Exam-Answers_v4.2.pdf'
import pdfplumber
import re
import json


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
questions = []

for block in blocks:
    # Question ID (supports X1, X2, etc.)
    num_match = re.match(r'^\s*(X?\d+)', block)
    qid = num_match.group(1).strip() if num_match else None

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

    questions.append({
        "question_id": qid,
        "answers": answers,
        "explanation": explanation,
        "learning_objective": lo,
        "klevel": klevel,
        "points": points
    })

print(f"✅ Parsed {len(questions)} question entries")

# --- 4️⃣ SAVE OUTPUT ---
with open("tta_answer_key_full_explanation.json", "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print("🎯 Output saved to tta_answer_key_full_explanation.json")