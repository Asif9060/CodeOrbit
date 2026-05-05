from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import UserResult, UserAnswer


class UserAnswerInline(TabularInline):
    model = UserAnswer
    extra = 0
    readonly_fields = ("question", "selected_option", "is_correct", "answered_at")
    can_delete = False


@admin.register(UserResult)
class UserResultAdmin(ModelAdmin):
    list_display = ("user", "quiz", "score", "total_points", "percentage", "is_completed", "started_at")
    list_filter = ("is_completed", "quiz__language", "quiz__difficulty", "quiz__quiz_type")
    search_fields = ("user__username", "quiz__title")
    readonly_fields = ("user", "quiz", "score", "total_points", "started_at", "completed_at")
    inlines = [UserAnswerInline]
