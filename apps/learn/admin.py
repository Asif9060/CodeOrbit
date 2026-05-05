from django.contrib import admin
from django.contrib import messages
from unfold.admin import ModelAdmin, StackedInline

from apps.learn.forms import TopicAdminForm
from apps.learn.models import Topic, TopicProgress, TopicResource
from apps.learn.services import generate_practice_quiz


@admin.action(description="Generate practice quiz (AI)")
def generate_ai_practice_quiz(modeladmin, request, queryset):
    ok, failed = 0, 0
    errors = []
    for topic in queryset:
        try:
            generate_practice_quiz(topic)
            ok += 1
        except Exception as exc:
            failed += 1
            errors.append(f"{topic.pk}: {exc}")

    if ok:
        modeladmin.message_user(request, f"Generated practice quizzes for {ok} topic(s).", messages.SUCCESS)
    if failed:
        detail = "; ".join(errors[:5])
        modeladmin.message_user(request, f"Failed {failed} topic(s): {detail}", messages.WARNING)


class TopicResourceInline(StackedInline):
    model = TopicResource
    extra = 0
    fields = ("title", "summary", "resource_url", "content", "sort_order", "is_published")


@admin.register(Topic)
class TopicAdmin(ModelAdmin):
    form = TopicAdminForm
    list_display = ("title", "language", "sort_order", "is_published", "has_content", "resource_count", "updated_at")
    list_filter = ("language", "is_published")
    search_fields = ("title", "summary", "content", "resources__title")
    list_editable = ("sort_order", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("language", "sort_order", "title")
    readonly_fields = ("created_at", "updated_at")
    actions = [generate_ai_practice_quiz]
    autocomplete_fields = ["language"]
    inlines = [TopicResourceInline]

    def has_content(self, obj):
        return bool(obj.content)
    has_content.boolean = True
    has_content.short_description = "Content"

    def resource_count(self, obj):
        return obj.resources.count()
    resource_count.short_description = "Resources"


@admin.register(TopicProgress)
class TopicProgressAdmin(ModelAdmin):
    list_display = ("user", "topic", "is_completed", "completed_at", "updated_at")
    list_filter = ("topic__language", "completed_at")
    search_fields = ("user__username", "topic__title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(TopicResource)
class TopicResourceAdmin(ModelAdmin):
    list_display = ("title", "topic", "resource_url", "sort_order", "is_published", "updated_at")
    list_filter = ("topic__language", "is_published")
    search_fields = ("title", "summary", "content", "topic__title")
    list_editable = ("sort_order", "is_published")
    ordering = ("topic", "sort_order", "title")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ["topic"]


