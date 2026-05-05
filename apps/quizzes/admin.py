from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from .models import Quiz, Question, Option


class OptionInline(TabularInline):
    model = Option
    extra = 4
    fields = ("text", "is_correct", "order")
    min_num = 2


class QuestionInline(StackedInline):
    model = Question
    extra = 1
    show_change_link = True
    fields = ("text", "question_type", "points", "order", "explanation")
    readonly_fields = ("edit_options_link",)

    def edit_options_link(self, obj):
        if obj.pk:
            url = reverse("admin:quizzes_question_change", args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank" style="color:#7c5df0;font-weight:600">'
                '⚙ Edit options for this question</a>', url
            )
        return "Save the quiz first, then click the change link above to add options."
    edit_options_link.short_description = "Options"


@admin.register(Quiz)
class QuizAdmin(ModelAdmin):
    list_display = ("title", "language", "quiz_type", "topic", "difficulty", "question_count", "time_limit", "is_published", "created_at")
    list_filter = ("is_published", "quiz_type", "difficulty", "language", "topic")
    search_fields = ("title", "description", "topic__title")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published",)
    inlines = [QuestionInline]
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ["language", "topic"]


def _ai_generate_button_html(obj):
    """Render the ✨ Generate with AI button + its inline JS."""
    if not obj or not obj.pk:
        return "Save the question first to enable AI generation."

    generate_url = reverse("ai_solutions:generate", args=[obj.pk])
    return format_html(
        """
        <div id="ai-gen-wrapper" style="margin-top:8px">
          <button type="button" id="ai-gen-btn"
            onclick="aiGenerateExplanation('{url}', {pk})"
            style="
              display:inline-flex;align-items:center;gap:6px;
              padding:8px 16px;border-radius:8px;font-weight:600;
              background:#7c5df0;color:#fff;border:none;cursor:pointer;
              font-size:13px;transition:opacity .2s;
            ">
            <span id="ai-gen-icon">✨</span>
            <span id="ai-gen-label">Generate with AI</span>
          </button>
          <span id="ai-gen-status" style="margin-left:10px;font-size:13px;"></span>
        </div>
        <script>
        function aiGenerateExplanation(url, pk) {{
          const btn = document.getElementById('ai-gen-btn');
          const label = document.getElementById('ai-gen-label');
          const icon = document.getElementById('ai-gen-icon');
          const status = document.getElementById('ai-gen-status');
          const textarea = document.getElementById('id_explanation');

          btn.disabled = true;
          icon.textContent = '⏳';
          label.textContent = 'Generating…';
          status.textContent = '';
          status.style.color = '';

          const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
          fetch(url, {{
            method: 'POST',
            headers: {{'X-CSRFToken': csrf}},
          }})
          .then(r => r.json())
          .then(data => {{
            if (data.ok) {{
              if (textarea) textarea.value = data.explanation;
              icon.textContent = '✅';
              label.textContent = 'Generated!';
              status.style.color = '#22c55e';
              status.textContent = 'Explanation filled — remember to Save.';
            }} else {{
              icon.textContent = '❌';
              label.textContent = 'Generate with AI';
              status.style.color = '#ef4444';
              status.textContent = data.error || 'Generation failed.';
              btn.disabled = false;
            }}
          }})
          .catch(err => {{
            icon.textContent = '❌';
            label.textContent = 'Generate with AI';
            status.style.color = '#ef4444';
            status.textContent = 'Network error: ' + err.message;
            btn.disabled = false;
          }});
        }}
        </script>
        """,
        url=generate_url,
        pk=obj.pk,
    )


@admin.action(description="✨ Generate AI explanations for selected questions")
def generate_ai_explanations(modeladmin, request, queryset):
    from apps.ai_solutions.services import generate_explanation
    ok, failed = 0, 0
    errors = []
    for question in queryset.prefetch_related("options"):
        if not question.options.exists() or not question.options.filter(is_correct=True).exists():
            failed += 1
            errors.append(f"Q{question.pk}: no options or no correct option marked")
            continue
        try:
            generate_explanation(question)
            ok += 1
        except Exception as exc:
            failed += 1
            errors.append(f"Q{question.pk}: {exc}")

    if ok:
        modeladmin.message_user(request, f"✅ Generated explanations for {ok} question(s).", messages.SUCCESS)
    if failed:
        detail = "; ".join(errors[:5])
        modeladmin.message_user(
            request,
            f"⚠ Skipped {failed} question(s): {detail}",
            messages.WARNING,
        )


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = ("text_short", "quiz", "question_type", "option_count", "points", "order")
    list_filter = ("question_type", "quiz__language", "quiz")
    search_fields = ("text", "quiz__title")
    inlines = [OptionInline]
    autocomplete_fields = ["quiz"]
    actions = [generate_ai_explanations]
    readonly_fields = ("ai_generate_button",)
    fieldsets = (
        (None, {
            "fields": ("quiz", "text", "question_type", "points", "order"),
        }),
        ("Explanation", {
            "fields": ("explanation", "ai_generate_button"),
            "description": (
                "Write an explanation manually or click the button to generate one "
                "automatically using the configured AI model."
            ),
        }),
    )

    def ai_generate_button(self, obj):
        return _ai_generate_button_html(obj)
    ai_generate_button.short_description = ""

    def text_short(self, obj):
        return obj.text[:80] + "…" if len(obj.text) > 80 else obj.text
    text_short.short_description = "Question"

    def option_count(self, obj):
        count = obj.options.count()
        correct = obj.options.filter(is_correct=True).count()
        if count == 0:
            return format_html('<span style="color:red">⚠ No options</span>')
        if correct == 0:
            return format_html('<span style="color:orange">{} options, no correct</span>', count)
        return format_html('<span style="color:green">{} options ✓</span>', count)
    option_count.short_description = "Options"


@admin.register(Option)
class OptionAdmin(ModelAdmin):
    list_display = ("text", "question", "is_correct", "order")
    list_filter = ("is_correct", "question__quiz__language")
    search_fields = ("text", "question__text")
    list_editable = ("is_correct", "order")
    autocomplete_fields = ["question"]

