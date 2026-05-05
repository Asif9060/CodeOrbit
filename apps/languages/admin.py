from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Language


@admin.action(description="Generate AI final quiz")
def generate_ai_final_quiz(modeladmin, request, queryset):
    from django.contrib import messages
    from apps.learn.services import generate_final_quiz

    ok, failed = 0, 0
    errors = []
    for language in queryset:
        try:
            generate_final_quiz(language)
            ok += 1
        except Exception as exc:
            failed += 1
            errors.append(f"{language.pk}: {exc}")

    if ok:
        modeladmin.message_user(request, f"Generated final quizzes for {ok} language(s).", messages.SUCCESS)
    if failed:
        detail = "; ".join(errors[:5])
        modeladmin.message_user(request, f"Failed {failed} language(s): {detail}", messages.WARNING)


@admin.register(Language)
class LanguageAdmin(ModelAdmin):
    list_display = ("name", "slug", "sort_order", "is_published", "published_quiz_count", "created_at")
    list_filter = ("is_published",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("sort_order", "is_published")
    ordering = ("sort_order", "name")
    readonly_fields = ("created_at", "updated_at")
    actions = [generate_ai_final_quiz]
