from django.urls import path
from . import views

app_name = "learn"

urlpatterns = [
    path("", views.learn_index, name="index"),
    path("<slug:language_slug>/", views.language_detail, name="language_detail"),
    path("<slug:language_slug>/leaderboard/", views.final_leaderboard, name="final_leaderboard"),
    path(
        "<slug:language_slug>/<slug:topic_slug>/generate-quiz/",
        views.generate_practice_quiz_view,
        name="generate_practice_quiz",
    ),
    path("<slug:language_slug>/<slug:topic_slug>/", views.topic_detail, name="topic_detail"),
]
