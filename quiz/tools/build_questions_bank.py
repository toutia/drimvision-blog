# scripts/populate_questions.py
import os
import django
import json
import sys
# Setup Django environment
# --- Adjust paths as needed ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append('./../../')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "drimvision.settings.base")
django.setup()

from quiz.models import ExamQuestion, ExamType

# 1. Get or create exam type
tta_exam_type, _ = ExamType.objects.get_or_create(
    code="tta",
    defaults={
        "name": "TTA",
        "default_question_count": 40,
        "default_duration_minutes": 60
    }
)



with open("tta_questions_1.json") as f:
    question_data = json.load(f)






# 3. Insert into the database
for q in question_data:
    ExamQuestion.objects.create(
        exam_type=tta_exam_type,
        question_text=q["question_text"],
        options=q["options"],
        answers=q["answers"],
        explanation = q['explanation'],
        points=q["points"]
    )

print(f"{len(question_data)} questions added to TTA exam.")
