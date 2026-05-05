from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Core pages (home)
    path("", include("apps.core.urls", namespace="core")),

    # Authentication
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),

    # Languages & Quizzes
    path("languages/", include("apps.languages.urls", namespace="languages")),
    path("quizzes/", include("apps.quizzes.urls", namespace="quizzes")),

    # Learn
    path("learn/", include("apps.learn.urls", namespace="learn")),

    # Results
    path("results/", include("apps.results.urls", namespace="results")),

    # Leaderboard
    path("leaderboard/", include("apps.leaderboard.urls", namespace="leaderboard")),

    # AI Explanations (staff-only AJAX)
    path("ai/", include("apps.ai_solutions.urls", namespace="ai_solutions")),

    # Future: contests, api
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    try:
        urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
    except ImportError:
        pass
