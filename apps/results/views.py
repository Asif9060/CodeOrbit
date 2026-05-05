"""Results views — score and review screen."""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.results.models import UserResult


@login_required
def result_detail(request, pk):
    result = get_object_or_404(
        UserResult.objects
        .select_related("quiz__language", "quiz__topic")
        .prefetch_related("answers__question__options", "answers__selected_option"),
        pk=pk,
        user=request.user,
    )

    review = []
    for i, answer in enumerate(
        result.answers.select_related("question", "selected_option")
        .prefetch_related("question__options")
        .order_by("question__order"), 1
    ):
        correct_opt = answer.question.options.filter(is_correct=True).first()
        review.append({
            "number": i,
            "text": answer.question.text,
            "your_answer": answer.selected_option.text if answer.selected_option else "(skipped)",
            "correct_answer": correct_opt.text if correct_opt else "",
            "is_correct": answer.is_correct,
            "explanation": answer.question.explanation or "",
        })

    correct = sum(1 for item in review if item["is_correct"])
    incorrect = sum(1 for item in review if item["your_answer"] != "(skipped)" and not item["is_correct"])
    skipped = sum(1 for item in review if item["your_answer"] == "(skipped)")

    return render(request, "results/detail.html", {
        "result": result,
        "review": review,
        "correct": correct,
        "incorrect": incorrect,
        "skipped": skipped,
    })
