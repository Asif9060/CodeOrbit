"""Quizzes views — quiz-taking experience."""
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from apps.quizzes.models import Quiz, Option, QuizType
from apps.learn.services import get_language_progress
from apps.results.services import create_quiz_attempt, submit_answer, complete_quiz
from apps.results.models import UserResult


@login_required
def quiz_take(request, slug):
    quiz = get_object_or_404(
        Quiz.objects.select_related("language")
        .prefetch_related("questions__options"),
        slug=slug,
        is_published=True,
    )

    if quiz.quiz_type == QuizType.FINAL:
        progress = get_language_progress(request.user, quiz.language)
        if progress["total"] == 0 or progress["completed"] < progress["total"]:
            messages.warning(request, "Complete all topics to unlock the final quiz.")
            return redirect("learn:language_detail", language_slug=quiz.language.slug)

    # Create a new attempt for this user
    result = create_quiz_attempt(request.user, quiz)

    # Serialize questions WITHOUT is_correct (never expose answers to client)
    questions_data = [
        {
            "id": q.id,
            "text": q.text,
            "options": [
                {"id": opt.id, "text": opt.text}
                for opt in q.options.all()
            ],
        }
        for q in quiz.questions.all()
    ]

    return render(request, "quizzes/take.html", {
        "quiz": quiz,
        "language": quiz.language,
        "questions": questions_data,
        "total_questions": len(questions_data),
        "results_url": reverse("results:detail", kwargs={"pk": result.pk}),
        "result_id": result.pk,
    })


@require_POST
@login_required
def submit_answer_view(request):
    """AJAX endpoint: save one answer as the user selects it."""
    try:
        data = json.loads(request.body)
        result_id = data["result_id"]
        question_id = data["question_id"]
        option_id = data["option_id"]
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"ok": False, "error": "Invalid payload"}, status=400)

    result = get_object_or_404(UserResult, pk=result_id, user=request.user)
    if result.is_completed:
        return JsonResponse({"ok": False, "error": "Quiz already completed"}, status=400)

    question = get_object_or_404(result.quiz.questions, pk=question_id)
    option = get_object_or_404(Option, pk=option_id, question=question)

    submit_answer(result, question, option)
    return JsonResponse({"ok": True})


@require_POST
@login_required
def complete_quiz_view(request, result_pk):
    """AJAX endpoint: finalize score, fire signal, return redirect URL."""
    result = get_object_or_404(UserResult, pk=result_pk, user=request.user)
    if not result.is_completed:
        complete_quiz(result)
    return JsonResponse({
        "ok": True,
        "redirect_url": reverse("results:detail", kwargs={"pk": result.pk}),
    })

