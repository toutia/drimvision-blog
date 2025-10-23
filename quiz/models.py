from types import SimpleNamespace
from django.db import models
from django.shortcuts import redirect, render
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.models import Page
import random
import time
# --- ExamType remains the same ---
@register_snippet
class ExamType(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    default_question_count = models.PositiveIntegerField(default=40)
    default_duration_minutes = models.PositiveIntegerField(default=60)

    panels = [
        FieldPanel("code"),
        FieldPanel("name"),
        FieldPanel("default_question_count"),
        FieldPanel("default_duration_minutes"),
    ]

    def __str__(self):
        return self.name

@register_snippet
class ExamQuestion(models.Model):
    """Question bank entry with options and answers."""
    exam_type = models.ForeignKey(
        ExamType, on_delete=models.CASCADE, related_name="questions"
    )
    module = models.CharField(max_length=100, blank=True)
    question_text = models.TextField(help_text="The main question text.")

    # Options JSON: simple dict {label: option_text}
    options = models.JSONField(
        help_text="JSON dict of options, e.g. {'A': 'Option 1', 'B': 'Option 2'}",
        default=dict
    )

    # Correct answers stored as JSON list
    answers = models.JSONField(
        help_text="List of correct labels, e.g. ['A'] or ['A', 'C']",
        default=list
    )

    points = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    panels = [
        FieldPanel("exam_type"),
        FieldPanel("module"),
        FieldPanel("question_text"),
        FieldPanel("options"),
        FieldPanel("answers"),
        FieldPanel("points"),
        FieldPanel("explanation"),
    ]

    def __str__(self):
        return f"[{self.exam_type.name}] {self.question_text[:80]}"

    # --- Helper ---
    def options_items(self):
        return self.options

    def is_correct(self, selected):
        """Compare list of selected labels with correct answers"""
        return set(selected) == set(self.answers)


class MockExamPage(Page):
    """Mock exam page drawing questions from the bank."""
    template = "quiz/mock_exam_page.html"

    exam_type = models.ForeignKey(ExamType, on_delete=models.PROTECT, related_name="+")
    question_count = models.PositiveIntegerField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(blank=True, null=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("exam_type"),
            FieldPanel("question_count"),
            FieldPanel("duration_minutes"),
        ], heading="Exam configuration"),
    ]

    def get_effective_settings(self):
        return {
            "question_count": self.question_count or self.exam_type.default_question_count,
            "duration_minutes": self.duration_minutes or self.exam_type.default_duration_minutes,
        }

    def get_random_questions(self):
        settings = self.get_effective_settings()
        qs = self.exam_type.questions.all()
        total = qs.count()
        if total == 0:
            return []
        return random.sample(list(qs), min(settings["question_count"], total))

    def serve(self, request):
        settings = self.get_effective_settings()
        max_duration = settings["duration_minutes"] * 60

        # ✅ Initialize session ONCE per exam type
        if (
            "questions_data" not in request.session
            or request.session.get("exam_type_id") != self.exam_type.id
            or 'start_time' not in request.session
        
        ):
            questions = self.get_random_questions()
            request.session["exam_type_id"] = self.exam_type.id
            request.session["questions_data"] = [
                {
                    "id": q.id,
                    "text": q.question_text,
                    "choices": q.options,  # ✅ store options here
                    'points': q.points,
                    'answers': q.answers,
                    'explanation': q.explanation
                }
                for q in questions
            ]
            
            request.session["start_time"] = time.time()
            request.session["submitted_answers"] = {}
            current_index = 0
            remaining_time = max_duration
        else:
            # Load questions from session (no DB query)

            current_index = int(request.GET.get("q", 0))
            start_time = request.session.get("start_time")
            remaining_time = max_duration - int(time.time() - start_time)


        questions_data = request.session["questions_data"]
        questions = [
                SimpleNamespace(
                    id=q["id"],
                    text=q["text"]+ f'\nSelect {len(q["answers"])} option(s).' if 'Select' not in q["text"] else q["text"] ,
                    choices=q["choices"],
                    points= q.get('points', 0),
                    answers = q['answers'],
                    explanation = q['explanation']
                )
                for q in questions_data
            ]
        total = len(questions)
        question = questions[current_index]
 
        
        # Get previously selected labels for this question
        answer_key = f"q_{question.id}"
        submitted_answers = request.session.get("submitted_answers", {})
        selected_labels = submitted_answers.get(answer_key, [])
        
    
        # ✅ Timeout check
        if remaining_time <= 0:
            return self.render_results(request, questions)

        # ✅ Handle POST
        if request.method == "POST":
            submitted_answers = request.session.get("submitted_answers", {})

            for key, values in request.POST.lists():
                if key.startswith("q_"):
                    submitted_answers[key] = values
            request.session["submitted_answers"] = submitted_answers
            request.session.modified = True

            # Navigation
            if "next" in request.POST and current_index + 1 < total:
                current_index += 1
            elif "prev" in request.POST and current_index > 0:
                current_index -= 1
            else:
                return self.render_results(request, questions)

            return redirect(f"{request.path}?q={current_index}")

        

        return render(request, self.template, {
            "page": self,
            "question": question,
            "current_index": current_index,
            "total": total,
            "submitted":False,
            "remaining_time": remaining_time,
            "selected_labels": selected_labels,  # ✅ pass to template
        })

    



    def render_results(self, request, questions):
        submitted_answers = request.session.get("submitted_answers", {})
        total_points = sum(getattr(q, "points", 0) for q in questions)
        earned_points = 0
        details = []

        for q in questions:
            qid = getattr(q, "id", None)
            selected = submitted_answers.get(f"q_{qid}", [])

            # Determine correct answers and check correctness
           
            correct_answers = getattr(q, "answers", [])  # maybe store in session if needed
            is_correct = set(selected) == set(correct_answers)
            options = getattr(q, "choices", {})
            points = getattr(q, "points", 0)
            explanation = getattr(q, "explanation", "")
            question_text = getattr(q, "text", "")

            if is_correct:
                earned_points += points

            details.append({
                "question": question_text,
                "options": options,
                "selected": selected,
                "correct_answers": correct_answers,
                "is_correct": is_correct,
                "points": points,
                "explanation": explanation,
            })

        # Clear session after exam
        print(request.session)
        for key in ["submitted_answers", "questions_data", "exam_type_id", "start_time"]:
            if key in request.session:
                del request.session[key]

        print(request.session)

        return render(request, self.template, {
            "page": self,
            "submitted": True,
            "details": details,
            "score": {
                "earned_points": earned_points,
                "total_points": total_points,
                "percentage": round(earned_points / total_points * 100, 1) if total_points else 0,
            },
        })