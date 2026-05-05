"""Learn app service layer."""
from __future__ import annotations

import json
from typing import Iterable

from django.db import transaction

from apps.ai_solutions.providers import get_active_provider
from apps.languages.models import Language
from apps.learn.models import Topic, TopicProgress
from apps.quizzes.models import Quiz, Question, Option, QuizType, DifficultyLevel, QuestionType


def get_published_topics_for_language(language: Language):
    return Topic.objects.filter(language=language, is_published=True).order_by("sort_order", "title")


def get_topic_progress_map(user, topics: Iterable[Topic]):
    if not user.is_authenticated:
        return {}
    progress = TopicProgress.objects.filter(user=user, topic__in=topics).select_related("last_result")
    return {item.topic_id: item for item in progress}


def get_language_progress(user, language: Language):
    total = Topic.objects.filter(language=language, is_published=True).count()
    if not user.is_authenticated or total == 0:
        return {"total": total, "completed": 0, "percent": 0}

    completed = TopicProgress.objects.filter(
        user=user,
        topic__language=language,
        topic__is_published=True,
        completed_at__isnull=False,
    ).count()
    percent = round((completed / total) * 100) if total else 0
    return {"total": total, "completed": completed, "percent": percent}


def get_topic_practice_quiz(topic: Topic):
    return Quiz.objects.filter(
        topic=topic,
        quiz_type=QuizType.PRACTICE,
    ).order_by("-created_at").first()


def get_language_final_quiz(language: Language):
    return Quiz.objects.filter(
        language=language,
        quiz_type=QuizType.FINAL,
    ).order_by("-created_at").first()


def generate_topic_content(topic: Topic) -> Topic:
    provider = get_active_provider()
    prompt = _build_topic_content_prompt(topic)
    text, _, _ = provider.generate(prompt)
    payload = _extract_json_payload(text)

    summary = (payload.get("summary") or "").strip()
    content = (payload.get("content") or "").strip()
    if not content:
        raise ValueError("AI response missing content")

    topic.summary = summary or topic.summary
    topic.content = content
    topic.save(update_fields=["summary", "content", "updated_at"])
    return topic


@transaction.atomic
def generate_practice_quiz(topic: Topic, question_count: int = 5) -> Quiz:
    if question_count < 3:
        question_count = 3
    if question_count > 5:
        question_count = 5

    quiz = Quiz.objects.filter(topic=topic, quiz_type=QuizType.PRACTICE).first()
    if not quiz:
        quiz = Quiz(
            title=f"{topic.title} Practice",
            slug=_build_unique_quiz_slug(f"{topic.language.slug}-{topic.slug}-practice"),
            language=topic.language,
            difficulty=DifficultyLevel.BEGINNER,
            quiz_type=QuizType.PRACTICE,
            topic=topic,
            description=f"Practice questions for {topic.title}.",
            is_published=False,
        )
    else:
        quiz.questions.all().delete()
        quiz.title = f"{topic.title} Practice"
        quiz.difficulty = DifficultyLevel.BEGINNER
        quiz.description = f"Practice questions for {topic.title}."
        quiz.quiz_type = QuizType.PRACTICE
        quiz.topic = topic
        quiz.is_published = False

    quiz.save()

    prompt = _build_practice_questions_prompt(topic, question_count)
    _populate_quiz_questions(quiz, prompt, question_count)
    quiz.publish()
    return quiz


@transaction.atomic
def generate_final_quiz(language: Language, question_count: int = 20) -> Quiz:
    if question_count < 10:
        question_count = 10
    if question_count > 40:
        question_count = 40

    quiz = Quiz.objects.filter(language=language, quiz_type=QuizType.FINAL).first()
    if not quiz:
        quiz = Quiz(
            title=f"{language.name} Final Quiz",
            slug=_build_unique_quiz_slug(f"{language.slug}-final-quiz"),
            language=language,
            difficulty=DifficultyLevel.BEGINNER,
            quiz_type=QuizType.FINAL,
            description=f"Final assessment for {language.name}.",
            is_published=False,
        )
    else:
        quiz.questions.all().delete()
        quiz.title = f"{language.name} Final Quiz"
        quiz.description = f"Final assessment for {language.name}."
        quiz.quiz_type = QuizType.FINAL
        quiz.is_published = False

    quiz.save()

    topics = list(
        Topic.objects.filter(language=language)
        .prefetch_related("resources")
        .order_by("sort_order", "title")
    )
    topic_contexts = [context for context in (_build_topic_context(topic) for topic in topics) if context]
    if not topic_contexts:
        raise ValueError("No topic materials available for final quiz generation")
    prompt = _build_final_questions_prompt(language, topic_contexts, question_count)
    _populate_quiz_questions(quiz, prompt, question_count)
    return quiz


def _build_topic_content_prompt(topic: Topic) -> str:
    return (
        "You are an expert programming instructor. "
        "Create a beginner-friendly lesson for the following topic. "
        "Return JSON with keys: summary, content. "
        "Content should use markdown-style headings and bullet lists. "
        "Keep it concise but complete for a beginner.\n\n"
        f"Language: {topic.language.name}\n"
        f"Topic: {topic.title}\n"
        "Output JSON only."
    )


def _build_practice_questions_prompt(topic: Topic, count: int) -> str:
    topic_context = _build_topic_context(topic)
    if not topic_context:
        raise ValueError("Topic has no content or resources to base a quiz on")
    return (
        "You are an expert programming instructor. "
        "Create a practice quiz for beginners. "
        "Use ONLY the material provided in the Topic Materials section. "
        "Do not introduce any external facts. "
        "Return JSON with a list of questions. "
        "Each question must have exactly 4 options and one correct_index. "
        "Include an explanation for the correct answer.\n\n"
        f"Language: {topic.language.name}\n"
        f"Topic Materials:\n{topic_context}\n"
        f"Number of questions: {count}\n"
        "JSON schema: {\"questions\":[{\"text\":...,\"options\":[...],\"correct_index\":0,\"explanation\":...}]}\n"
        "Output JSON only."
    )


def _build_final_questions_prompt(language: Language, topic_contexts: list[str], count: int) -> str:
    topic_block = "\n\n".join(topic_contexts)
    return (
        "You are an expert programming instructor. "
        "Create a final assessment quiz for beginners. "
        "Use ONLY the material provided in the Topic Materials section. "
        "Do not introduce any external facts. "
        "Return JSON with a list of questions. "
        "Each question must have exactly 4 options and one correct_index. "
        "Include an explanation for the correct answer.\n\n"
        f"Language: {language.name}\n"
        f"Topic Materials:\n{topic_block}\n"
        f"Number of questions: {count}\n"
        "JSON schema: {\"questions\":[{\"text\":...,\"options\":[...],\"correct_index\":0,\"explanation\":...}]}\n"
        "Output JSON only."
    )


def _truncate_prompt_block(text: str, max_chars: int) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rstrip() + "\n...(truncated)"


def _build_topic_context(topic: Topic) -> str:
    summary = (topic.summary or "").strip()
    content = _truncate_prompt_block(topic.content or "", 3500)
    resources = _build_resource_context(topic)

    if not summary and not content and not resources:
        return ""

    parts = [f"Topic: {topic.title}"]
    if summary:
        parts.append(f"Summary: {summary}")
    if content:
        parts.append(f"Lesson content:\n{content}")
    if resources:
        parts.append(f"Resources:\n{resources}")
    return "\n".join(parts)


def _build_resource_context(topic: Topic) -> str:
    resources = list(topic.resources.filter(is_published=True).order_by("sort_order", "title"))
    if not resources:
        return ""

    blocks = []
    for resource in resources:
        lines = [f"Resource: {resource.title}"]
        if resource.resource_url:
            lines.append(f"URL: {resource.resource_url}")
        if resource.summary:
            lines.append(f"Summary: {resource.summary.strip()}")
        if resource.content:
            content = _truncate_prompt_block(resource.content, 3500)
            lines.append(f"Content:\n{content}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def _extract_json_payload(text: str):
    cleaned = text.strip()
    if cleaned.startswith("{") or cleaned.startswith("["):
        return json.loads(cleaned)

    obj_start = cleaned.find("{")
    arr_start = cleaned.find("[")
    if obj_start == -1 and arr_start == -1:
        raise ValueError("No JSON payload found")

    if arr_start != -1 and (arr_start < obj_start or obj_start == -1):
        start = arr_start
        end = cleaned.rfind("]")
    else:
        start = obj_start
        end = cleaned.rfind("}")

    if end == -1:
        raise ValueError("JSON payload is incomplete")

    return json.loads(cleaned[start : end + 1])


def _populate_quiz_questions(quiz: Quiz, prompt: str, expected: int):
    provider = get_active_provider()
    text, _, _ = provider.generate(prompt)
    payload = _extract_json_payload(text)

    if isinstance(payload, dict):
        questions = payload.get("questions") or []
    elif isinstance(payload, list):
        questions = payload
    else:
        raise ValueError("Invalid question payload")

    if not questions:
        raise ValueError("No questions returned")

    created = 0
    for idx, item in enumerate(questions, start=1):
        if created >= expected:
            break

        question_text = (item.get("text") or "").strip()
        options = item.get("options") or []
        correct_index = item.get("correct_index")
        explanation = (item.get("explanation") or "").strip()

        if not question_text or len(options) != 4:
            continue
        if not isinstance(correct_index, int) or correct_index < 0 or correct_index >= len(options):
            continue

        question = Question.objects.create(
            quiz=quiz,
            text=question_text,
            explanation=explanation,
            order=idx,
            points=1,
            question_type=QuestionType.MCQ,
        )

        for opt_index, opt_text in enumerate(options):
            opt_value = opt_text.get("text") if isinstance(opt_text, dict) else opt_text
            Option.objects.create(
                question=question,
                text=str(opt_value).strip(),
                is_correct=opt_index == correct_index,
                order=opt_index + 1,
            )

        created += 1

    if created == 0:
        raise ValueError("No valid questions were created")


def _build_unique_quiz_slug(base_slug: str) -> str:
    slug = base_slug
    counter = 2
    while Quiz.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
