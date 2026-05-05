from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import LeaderboardEntry


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(ModelAdmin):
    list_display = ("rank", "user", "language", "category", "total_score", "quizzes_completed", "updated_at")
    list_filter = ("language", "category")
    search_fields = ("user__username",)
    ordering = ("rank",)
