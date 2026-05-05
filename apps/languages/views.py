"""Languages views."""
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from apps.languages.models import Language
from apps.quizzes.models import Quiz, QuizType


def language_list(request):
    languages = (
        Language.objects
        .filter(is_published=True)
        .annotate(quiz_count=Count("quiz", filter=Q(quiz__is_published=True, quiz__quiz_type=QuizType.GENERAL)))
        .order_by("sort_order", "name")
    )
    return render(request, "languages/list.html", {"languages": languages})


def language_detail(request, slug):
    language = get_object_or_404(Language, slug=slug, is_published=True)
    quizzes = (
        Quiz.objects
        .filter(language=language, is_published=True, quiz_type=QuizType.GENERAL)
        .annotate(num_questions=Count("questions"))
        .order_by("difficulty", "title")
    )
    return render(request, "quizzes/list.html", {
        "language": language,
        "quizzes": quizzes,
    })
