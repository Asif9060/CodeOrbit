"""
Leaderboard signal receivers.
Connected in LeaderboardConfig.ready().
"""
from django.dispatch import receiver
from apps.core.signals import quiz_completed


@receiver(quiz_completed)
def update_leaderboard(sender, user, quiz, **kwargs):
    """
    Upsert the user's LeaderboardEntry (global + language-specific) and
    reassign ranks for the affected scope.
    Fires after every completed quiz via quiz_completed signal.
    """
    from django.db.models import Sum, Count
    from apps.results.models import UserResult
    from apps.leaderboard.models import LeaderboardEntry, LeaderboardCategory
    from apps.quizzes.models import QuizType

    language = quiz.language

    if quiz.quiz_type == QuizType.PRACTICE:
        return

    if quiz.quiz_type == QuizType.FINAL:
        _update_final_entry(user, language)
        _reassign_ranks(language=language, category=LeaderboardCategory.FINAL)
        return

    # Update for both global (language=None) and language-specific
    for lang in (None, language):
        qs = UserResult.objects.filter(
            user=user,
            is_completed=True,
            quiz__quiz_type=QuizType.GENERAL,
        )
        if lang:
            qs = qs.filter(quiz__language=lang)

        agg = qs.aggregate(
            total_score=Sum("score"),
            quizzes_completed=Count("id"),
        )

        entry, _ = LeaderboardEntry.objects.get_or_create(
            user=user,
            language=lang,
            category=LeaderboardCategory.GENERAL,
            defaults={"total_score": 0, "quizzes_completed": 0, "rank": 0},
        )
        entry.total_score = agg["total_score"] or 0
        entry.quizzes_completed = agg["quizzes_completed"] or 0
        entry.save(update_fields=["total_score", "quizzes_completed"])

    # Reassign ranks for the general leaderboard
    _reassign_ranks(language=None, category=LeaderboardCategory.GENERAL)
    _reassign_ranks(language=language, category=LeaderboardCategory.GENERAL)


def _update_final_entry(user, language):
    """Update the final-quiz leaderboard entry for one user and language."""
    from apps.results.models import UserResult
    from apps.leaderboard.models import LeaderboardEntry, LeaderboardCategory
    from apps.quizzes.models import QuizType

    qs = UserResult.objects.filter(
        user=user,
        is_completed=True,
        quiz__language=language,
        quiz__quiz_type=QuizType.FINAL,
    )
    latest = qs.order_by("-completed_at", "-started_at").first()

    entry, _ = LeaderboardEntry.objects.get_or_create(
        user=user,
        language=language,
        category=LeaderboardCategory.FINAL,
        defaults={"total_score": 0, "quizzes_completed": 0, "rank": 0},
    )
    entry.total_score = latest.score if latest else 0
    entry.quizzes_completed = qs.count()
    entry.save(update_fields=["total_score", "quizzes_completed"])


def _reassign_ranks(language, category):
    """Re-number rank field for all entries in one leaderboard scope."""
    from apps.leaderboard.models import LeaderboardEntry
    entries = LeaderboardEntry.objects.filter(language=language, category=category).order_by("-total_score")
    for i, entry in enumerate(entries, start=1):
        if entry.rank != i:
            entry.rank = i
            entry.save(update_fields=["rank"])
