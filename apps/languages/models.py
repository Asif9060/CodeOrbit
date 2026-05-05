"""
Languages app models — programming language catalog.
"""
from django.db import models
from django.utils.text import slugify
from apps.core.models import PublishableModel


class Language(PublishableModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon = models.ImageField(upload_to="language_icons/", null=True, blank=True)
    icon_svg = models.TextField(blank=True, help_text="Raw SVG markup (optional)")
    description = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0, help_text="Lower = listed first")

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Language"
        verbose_name_plural = "Languages"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("languages:detail", kwargs={"slug": self.slug})

    @property
    def published_quiz_count(self):
        from apps.quizzes.models import QuizType
        return self.quiz_set.filter(is_published=True, quiz_type=QuizType.GENERAL).count()
