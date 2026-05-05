"""Accounts views — login, register, profile."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum

User = get_user_model()


# ─── Login ────────────────────────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        remember_me = request.POST.get("remember_me")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember_me:
                # Session expires when browser closes
                request.session.set_expiry(0)
            next_url = request.GET.get("next") or "core:home"
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html", {})


# ─── Register ─────────────────────────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        # Validate
        if not username or not email or not password1:
            messages.error(request, "All fields are required.")
        elif password1 != password2:
            messages.error(request, "Passwords do not match.")
        elif len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "An account with this email already exists.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            login(request, user)
            messages.success(request, f"Welcome to CodeOrbit, {user.username}!")
            return redirect("core:home")

    return render(request, "accounts/register.html", {})


# ─── Profile ──────────────────────────────────────────────────────────────────
@login_required
def profile_view(request, username=None):
    if username is None:
        profile_user = request.user
    else:
        profile_user = get_object_or_404(User, username=username)

    # Handle profile update (own profile only)
    if request.method == "POST" and profile_user == request.user:
        bio = request.POST.get("bio", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        profile_user.bio = bio
        profile_user.first_name = first_name
        profile_user.last_name = last_name
        if "avatar" in request.FILES:
            profile_user.avatar = request.FILES["avatar"]
        profile_user.save()
        messages.success(request, "Profile updated.")
        return redirect("accounts:profile", username=profile_user.username)

    # Quiz history
    history_qs = (
        profile_user.results
        .filter(is_completed=True)
        .select_related("quiz__language")
        .order_by("-completed_at")[:20]
    )
    history = [
        {
            "quiz": r.quiz.title,
            "quiz_slug": r.quiz.slug,
            "language": r.quiz.language.name,
            "score": r.score,
            "total": r.total_points,
            "percentage": r.percentage,
            "date": r.completed_at.strftime("%b %d, %Y") if r.completed_at else "",
            "result_id": r.pk,
        }
        for r in history_qs
    ]

    # Aggregated stats
    agg = profile_user.results.filter(is_completed=True).aggregate(
        avg_score=Avg("score"),
        total_correct=Sum("score"),
        languages_tried=Count("quiz__language", distinct=True),
    )

    return render(request, "accounts/profile.html", {
        "profile_user": profile_user,
        "history": history,
        "stats": {
            "avg_score": round(agg["avg_score"] or 0),
            "languages_tried": agg["languages_tried"] or 0,
            "total_correct": agg["total_correct"] or 0,
        },
        "is_own_profile": profile_user == request.user,
    })

