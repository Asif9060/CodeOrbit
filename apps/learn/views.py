"""Learn views."""
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.languages.models import Language
from apps.learn.models import Topic, TopicProgress
from apps.learn.rendering import render_lesson_content
from apps.learn.services import (
    get_published_topics_for_language,
    get_language_progress,
    get_topic_practice_quiz,
    get_language_final_quiz,
    generate_practice_quiz,
)
from apps.quizzes.models import Quiz, QuizType
from apps.leaderboard.models import LeaderboardEntry, LeaderboardCategory


def learn_index(request):
    languages = Language.objects.filter(is_published=True).order_by("sort_order", "name")
    language_cards = []
    for lang in languages:
        progress = get_language_progress(request.user, lang)
        language_cards.append({
            "language": lang,
            "progress": progress,
        })
    return render(request, "learn/index.html", {
        "language_cards": language_cards,
    })


def language_detail(request, language_slug):
    language = get_object_or_404(Language, slug=language_slug, is_published=True)
    if request.user.is_staff:
        topics = list(Topic.objects.filter(language=language).order_by("sort_order", "title"))
    else:
        topics = list(get_published_topics_for_language(language))
    progress_map = {}
    if request.user.is_authenticated and topics:
        progress_map = {
            item.topic_id: item
            for item in TopicProgress.objects.filter(
                user=request.user,
                topic__in=topics,
            ).select_related("last_result")
        }
    quiz_map = {}
    if topics:
        quiz_map = {
            quiz.topic_id: quiz
            for quiz in Quiz.objects.filter(topic__in=topics, quiz_type=QuizType.PRACTICE)
        }
    progress = get_language_progress(request.user, language)

    final_quiz = get_language_final_quiz(language)
    final_unlocked = progress["total"] > 0 and progress["completed"] == progress["total"]

    topic_cards = [
        {
            "topic": topic,
            "progress": progress_map.get(topic.id),
            "practice_quiz": quiz_map.get(topic.id),
        }
        for topic in topics
    ]

    return render(request, "learn/language_detail.html", {
        "language": language,
        "topic_cards": topic_cards,
        "progress": progress,
        "final_quiz": final_quiz,
        "final_unlocked": final_unlocked,
    })


def topic_detail(request, language_slug, topic_slug):
    topic_queryset = Topic.objects.select_related("language")
    if not request.user.is_staff:
        topic_queryset = topic_queryset.filter(is_published=True)

    topic = get_object_or_404(
        topic_queryset,
        language__slug=language_slug,
        slug=topic_slug,
    )
    practice_quiz = get_topic_practice_quiz(topic)
    progress = None
    if request.user.is_authenticated:
        progress = topic.progress.filter(user=request.user).select_related("last_result").first()

    lesson_html = render_lesson_content(topic.content)
    has_resources = topic.resources.filter(is_published=True).exists()
    can_generate_quiz = request.user.is_staff and has_resources

    return render(request, "learn/topic_detail.html", {
        "topic": topic,
        "practice_quiz": practice_quiz,
        "progress": progress,
        "lesson_html": lesson_html,
        "can_generate_quiz": can_generate_quiz,
    })


@require_POST
@staff_member_required
def generate_practice_quiz_view(request, language_slug, topic_slug):
    topic = get_object_or_404(
        Topic.objects.select_related("language"),
        language__slug=language_slug,
        slug=topic_slug,
    )

    if not topic.resources.filter(is_published=True).exists():
        messages.warning(request, "Add at least one published resource before generating a quiz.")
        return redirect(topic.get_absolute_url())

    try:
        generate_practice_quiz(topic)
        messages.success(request, "Practice quiz generated and saved as a draft.")
    except Exception as exc:
        messages.error(request, f"Quiz generation failed: {exc}")

    return redirect(topic.get_absolute_url())


def final_leaderboard(request, language_slug):
    language = get_object_or_404(Language, slug=language_slug, is_published=True)
    entries = (
        LeaderboardEntry.objects
        .filter(language=language, category=LeaderboardCategory.FINAL)
        .select_related("user", "language")
        .order_by("rank")[:50]
    )

    leaders = [
        {
            "rank": e.rank,
            "username": e.user.username,
            "display_name": e.user.display_name,
            "total_score": e.total_score,
            "quizzes": e.quizzes_completed,
            "avatar": e.user.avatar.url if e.user.avatar else None,
        }
        for e in entries
    ]

    return render(request, "learn/final_leaderboard.html", {
        "language": language,
        "leaders": leaders,
        "podium": leaders[:3],
        "rest": leaders[3:],
    })
