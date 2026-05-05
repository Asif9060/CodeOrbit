"""
Quizzes app models — Quiz, Question, Option.
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from apps.core.models import PublishableModel


class DifficultyLevel(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"


class QuizType(models.TextChoices):
    GENERAL = "general", "General"
    PRACTICE = "practice", "Practice"
    FINAL = "final", "Final"


class QuestionType(models.TextChoices):
    MCQ = "mcq", "Multiple Choice"
    TRUE_FALSE = "true_false", "True / False"
    MULTI_SELECT = "multi_select", "Multi-Select"


class Quiz(PublishableModel):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    language = models.ForeignKey("languages.Language", on_delete=models.CASCADE)
    difficulty = models.CharField(max_length=20, choices=DifficultyLevel.choices, default=DifficultyLevel.BEGINNER)
    quiz_type = models.CharField(max_length=20, choices=QuizType.choices, default=QuizType.GENERAL)
    topic = models.ForeignKey("learn.Topic", null=True, blank=True, on_delete=models.SET_NULL, related_name="quizzes")
    description = models.TextField(blank=True)
    time_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Time limit in seconds. Leave blank for no limit.")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["language", "difficulty", "title"]
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return f"{self.title} ({self.language})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("quizzes:take", kwargs={"slug": self.slug})

    @property
    def question_count(self):
        return self.question_set.count()


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    explanation = models.TextField(blank=True, help_text="Shown after answering. Can be auto-filled by AI.")
    order = models.PositiveSmallIntegerField(default=0)
    points = models.PositiveSmallIntegerField(default=1)
    question_type = models.CharField(max_length=20, choices=QuestionType.choices, default=QuestionType.MCQ)

    class Meta:
        ordering = ["order"]
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        return f"Q{self.order}: {self.text[:60]}"


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name = "Option"
        verbose_name_plural = "Options"

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.text[:60]}"
