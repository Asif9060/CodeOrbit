"""Leaderboard views."""
from django.shortcuts import render
from apps.leaderboard.models import LeaderboardEntry, LeaderboardCategory
from apps.languages.models import Language


def leaderboard_index(request):
    active_tab = request.GET.get("tab", "all")

    entries = (
        LeaderboardEntry.objects
        .filter(language__isnull=True, category=LeaderboardCategory.GENERAL)
        .select_related("user")
        .order_by("rank")[:50]
    )

    languages = Language.objects.filter(is_published=True).order_by("sort_order", "name")

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

    return render(request, "leaderboard/index.html", {
        "leaders": leaders,
        "podium": leaders[:3],
        "rest": leaders[3:],
        "languages": languages,
        "active_tab": active_tab,
    })
