"""
Leaderboard app models — rankings aggregation.
Future: computed via Celery periodic tasks.
"""
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class LeaderboardCategory(models.TextChoices):
    GENERAL = "general", "General"
    FINAL = "final", "Final"


class LeaderboardEntry(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="leaderboard_entries")
    language = models.ForeignKey("languages.Language", null=True, blank=True, on_delete=models.CASCADE, help_text="Null = global leaderboard")
    category = models.CharField(max_length=20, choices=LeaderboardCategory.choices, default=LeaderboardCategory.GENERAL)
    total_score = models.PositiveIntegerField(default=0)
    quizzes_completed = models.PositiveIntegerField(default=0)
    rank = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["rank"]
        unique_together = [("user", "language", "category")]
        verbose_name = "Leaderboard Entry"
        verbose_name_plural = "Leaderboard Entries"

    def __str__(self):
        lang = self.language.name if self.language else "Global"
        return f"#{self.rank} {self.user} — {lang} ({self.total_score} pts)"
