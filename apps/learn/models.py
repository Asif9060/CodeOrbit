"""
Learn app models.
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from apps.core.models import PublishableModel, TimeStampedModel


class Topic(PublishableModel):
    language = models.ForeignKey("languages.Language", on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    summary = models.TextField(blank=True)
    content = models.TextField(blank=True, help_text="Lesson content. Supports markdown-style headings.")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["language", "sort_order", "title"]
        unique_together = [("language", "slug")]
        verbose_name = "Topic"
        verbose_name_plural = "Topics"

    def __str__(self):
        return f"{self.language.name} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("learn:topic_detail", kwargs={
            "language_slug": self.language.slug,
            "topic_slug": self.slug,
        })


class TopicResource(PublishableModel):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="resources")
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True, help_text="Short overview shown in the resource list.")
    content = models.TextField(help_text="Markdown content. Use triple backticks for code blocks.")
    resource_url = models.URLField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["topic", "sort_order", "title"]
        verbose_name = "Topic Resource"
        verbose_name_plural = "Topic Resources"

    def __str__(self):
        return f"{self.topic.title} - {self.title}"


class TopicProgress(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topic_progress")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="progress")
    completed_at = models.DateTimeField(null=True, blank=True)
    last_result = models.ForeignKey(
        "results.UserResult",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="topic_progress",
    )

    class Meta:
        unique_together = [("user", "topic")]
        ordering = ["-updated_at"]
        verbose_name = "Topic Progress"
        verbose_name_plural = "Topic Progress"

    def __str__(self):
        return f"{self.user} - {self.topic}"

    @property
    def is_completed(self):
        return self.completed_at is not None
