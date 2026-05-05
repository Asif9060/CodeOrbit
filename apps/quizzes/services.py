"""
Quizzes service layer.
Business logic lives here — views call services, services call models.
"""
from apps.quizzes.models import Quiz, Question, QuizType


def get_published_quizzes_for_language(language_slug: str):
    """Return published quizzes for a given language slug."""
    return Quiz.objects.filter(
        language__slug=language_slug,
        is_published=True,
        quiz_type=QuizType.GENERAL,
    ).select_related("language").order_by("difficulty", "title")


def get_quiz_with_questions(quiz_slug: str):
    """Return a quiz with all its questions and options prefetched."""
    return (
        Quiz.objects.filter(slug=quiz_slug, is_published=True)
        .prefetch_related("questions__options")
        .select_related("language")
        .first()
    )
