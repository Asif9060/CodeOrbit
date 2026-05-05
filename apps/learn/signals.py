"""
Learn signals.
"""
from django.dispatch import receiver
from django.utils import timezone
from apps.core.signals import quiz_completed
from apps.learn.models import TopicProgress
from apps.quizzes.models import QuizType


@receiver(quiz_completed)
def update_topic_progress(sender, user, quiz, **kwargs):
    if quiz.quiz_type != QuizType.PRACTICE or not quiz.topic:
        return

    progress, _ = TopicProgress.objects.get_or_create(user=user, topic=quiz.topic)
    progress.last_result = sender
    if not progress.completed_at:
        progress.completed_at = timezone.now()
    progress.save(update_fields=["last_result", "completed_at", "updated_at"])
