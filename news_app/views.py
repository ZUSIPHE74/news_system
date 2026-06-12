from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db.utils import OperationalError

from .models import Article, User, Publisher, Newsletter
from .signals import create_groups_and_permissions
from .forms import (
    PublisherForm,
    NewsletterForm,
    ArticleForm,
    JournalistArticleForm,
)
import requests
from rest_framework.authtoken.models import Token


def home(request):
    """
    Render the public homepage with only approved articles.
    """
    articles = Article.objects.filter(status=Article.APPROVED).order_by(
        "-date_posted"
    )
    return render(request, "news_app/home.html", {"articles": articles})


def ensure_demo_accounts():
    """
    Ensure role demo accounts exist with known credentials for evaluation.
    """
    try:
        publisher, _ = Publisher.objects.get_or_create(
            name="Demo Publisher",
            defaults={"website": "https://example.com"},
        )

        demo_users = [
            ("reader_demo", User.READER, None),
            ("journalist_demo", User.JOURNALIST, publisher),
            ("editor_demo", User.EDITOR, publisher),
        ]

        for username, role, assigned_publisher in demo_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "role": role,
                    "publisher": assigned_publisher,
                },
            )
            if not created:
                user.role = role
                user.publisher = assigned_publisher
                user.set_password("DemoPass123!")
                user.save()
    except OperationalError:
        # Database may not be migrated yet (e.g., very first startup).
        return


def login_view(request):
    """
    Authenticate a user with username/password and start a session.
    """
    ensure_demo_accounts()
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        normalized_username = username.lower()

        user = authenticate(request, username=username, password=password)
        if not user and normalized_username != username:
            # Be permissive for accidental casing differences in usernames.
            user = authenticate(
                request, username=normalized_username, password=password
            )

        if user:
            login(request, user)
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)

            # Role-specific dashboard redirection
            if user.role == User.READER:
                return redirect("reader_dashboard")
            elif user.role == User.JOURNALIST:
                return redirect("journalist_dashboard")
            elif user.role == User.EDITOR:
                return redirect("editor_dashboard")
            return redirect("home")
        messages.error(request, "Invalid credentials.")
    return render(request, "news_app/login.html")


def signup_view(request):
    """
    Create a new user account with a specific role.
    Validates that the username and email are unique.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        role = request.POST.get("role", User.READER)

        if not username or not email or not password:
            messages.error(
                request, "Username, email, and password are required."
            )
            return render(request, "news_app/signup.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "news_app/signup.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
            return render(request, "news_app/signup.html")

        if User.objects.filter(email=email).exists():
            messages.error(
                request, "This email address is already registered."
            )
            return render(request, "news_app/signup.html")

        # Validate role
        if role not in [User.READER, User.JOURNALIST, User.EDITOR]:
            role = User.READER

        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
        )
        messages.success(
            request, "Account created successfully. Please log in."
        )
        return redirect("login")

    return render(request, "news_app/signup.html")


@login_required
def reader_dashboard(request):
    """
    Display user-specific content for readers, including followed
    publishers/journalists.
    """
    # Allow all authenticated users to see the reader dashboard (public feed)
    pass

    articles = Article.objects.filter(status=Article.APPROVED).order_by(
        "-date_posted"
    )[:10]
    return render(
        request, "news_app/reader_dashboard.html", {"articles": articles}
    )


def logout_view(request):
    """
    End the current session and send the user to the login page.
    """
    logout(request)
    return redirect("login")


@login_required
def article_detail(request, pk):
    """
    Show a single approved article to authenticated users.
    Includes suggested articles (latest 3 approved excluding current).
    """
    article = get_object_or_404(Article, pk=pk, status=Article.APPROVED)
    suggested_articles = (
        Article.objects.filter(status=Article.APPROVED)
        .exclude(pk=pk)
        .order_by("-date_posted")[:3]
    )
    suggested_publishers = Publisher.objects.all()[:3]
    return render(
        request,
        "news_app/article_detail.html",
        {
            "article": article,
            "suggested_articles": suggested_articles,
            "suggested_publishers": suggested_publishers,
        },
    )


@login_required
def journalist_dashboard(request):
    """
    Display journalist-owned articles and newsletters.
    """
    if request.user.role != User.JOURNALIST:
        return HttpResponseForbidden("Access denied.")
    articles = Article.objects.filter(author=request.user).order_by(
        "-date_posted"
    )
    return render(
        request, "news_app/journalist_dashboard.html", {"articles": articles}
    )


@login_required
def submit_article(request):
    """
    Allow journalists to submit new articles for editor review.
    Allows selection of poster type (Independent vs Publisher).
    """
    if request.user.role != User.JOURNALIST:
        return HttpResponseForbidden("Access denied.")

    if request.method == "POST":
        form = JournalistArticleForm(
            request.POST, request.FILES, user=request.user
        )
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            # Only set publisher if they chose POSTER_PUBLISHER
            if article.poster_type == Article.POSTER_PUBLISHER:
                article.publisher = request.user.publisher
            else:
                article.publisher = None

            article.status = Article.PENDING
            article.save()
            messages.success(
                request, f'Article "{article.title}" submitted for review.'
            )
            return redirect("journalist_dashboard")
        else:
            messages.error(
                request, "Error submitting article. Please check the form."
            )
    else:
        form = JournalistArticleForm(user=request.user)

    return render(request, "news_app/submit_article.html", {"form": form})


@login_required
def editor_dashboard(request):
    """
    List pending articles for editors to review, and provide access to
    article management.
    """
    if request.user.role != User.EDITOR and not request.user.is_staff:
        return HttpResponseForbidden(
            f"Access denied. Your account ({request.user.username}) "
            f"has the role: {request.user.role}. "
            "You must be an Editor to access this."
        )
    base_qs = Article.objects.all()
    if request.user.publisher:
        base_qs = base_qs.filter(publisher=request.user.publisher)

    pending_articles = base_qs.filter(status=Article.PENDING).order_by(
        "-date_posted"
    )
    all_articles = base_qs.order_by("-date_posted")
    return render(
        request,
        "news_app/editor_dashboard.html",
        {"pending_articles": pending_articles, "all_articles": all_articles},
    )


def _log_approved_article(request, article):
    """
    Internal helper to simulate sharing by posting to the /api/approved/ endpoint.
    """
    try:
        # Get or create token for the approving editor
        token, _ = Token.objects.get_or_create(user=request.user)
        api_url = request.build_absolute_uri("/api/approved/")

        # Prepare data (simulating serialization)
        data = {
            "title": article.title,
            "content": article.content,
            "poster_type": article.poster_type,
            # We skip nested objects for simplicity in this simulated POST
        }

        headers = {"Authorization": f"Token {token.key}"}
        response = requests.post(api_url, json=data, headers=headers)
        if response.status_code == 201:
            print(f"Successfully logged article {article.id} via API.")
        else:
            print(f"Failed to log article via API: {response.status_code}")
    except Exception as e:
        print(f"Error during API logging: {e}")


@login_required
def approve_article(request, pk):
    """
    Approve or reject a pending article. Editor-only.
    """
    if request.user.role != User.EDITOR and not request.user.is_staff:
        return HttpResponseForbidden("Access denied.")
    article = get_object_or_404(Article, pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "approve":
            article.status = Article.APPROVED
            article.approved_by = request.user
            if request.user.publisher:
                article.publisher = request.user.publisher
            article.save()
            # Requirement 4: Log approved articles to REST API
            _log_approved_article(request, article)
            messages.success(
                request,
                f'Article "{article.title}" approved and logged to sharing API.',
            )
        elif action == "reject":
            article.status = Article.REJECTED
            article.approved_by = request.user
            article.save()
            messages.warning(request, f'Article "{article.title}" rejected.')
        return redirect("editor_dashboard")
    return render(
        request, "news_app/approve_article.html", {"article": article}
    )


@login_required
def update_article(request, pk):
    """
    Allow editors and journalists (authors) to update articles.
    """
    article = get_object_or_404(Article, pk=pk)

    # Permission check:
    # 1. Editor/Staff can edit if they share the publisher (if they have one).
    # 2. Journalist can edit if they are the author of the article.
    if request.user.role == User.EDITOR or request.user.is_staff:
        if (
            article.publisher
            and request.user.publisher
            and request.user.publisher != article.publisher
        ):
            return HttpResponseForbidden(
                "Access denied. You can only update articles from your own publisher."
            )
    elif request.user.role == User.JOURNALIST:
        if article.author != request.user:
            return HttpResponseForbidden(
                "Access denied. You can only update your own articles."
            )
    else:
        return HttpResponseForbidden("Access denied.")

    if request.method == "POST":
        if request.user.role == User.JOURNALIST:
            form = JournalistArticleForm(
                request.POST,
                request.FILES,
                instance=article,
                user=request.user,
            )
        else:
            form = ArticleForm(request.POST, request.FILES, instance=article)

        if form.is_valid():
            saved_article = form.save(commit=False)
            if request.user.role == User.JOURNALIST:
                if saved_article.poster_type == Article.POSTER_PUBLISHER:
                    saved_article.publisher = request.user.publisher
                else:
                    saved_article.publisher = None
                saved_article.status = Article.PENDING

            saved_article.save()
            form.save_m2m()
            messages.success(
                request, f'Article "{saved_article.title}" updated.'
            )

            if request.user.role == User.JOURNALIST:
                return redirect("journalist_dashboard")
            return redirect("editor_dashboard")
        else:
            messages.error(
                request, "Error updating article. Please check the form."
            )
    else:
        if request.user.role == User.JOURNALIST:
            form = JournalistArticleForm(instance=article, user=request.user)
        else:
            form = ArticleForm(instance=article)

    return render(
        request,
        "news_app/update_article.html",
        {"form": form, "article": article},
    )


@login_required
def delete_article(request, pk):
    """
    Allow editors and journalists (authors) to delete articles.
    """
    article = get_object_or_404(Article, pk=pk)

    # Permission check:
    # 1. Editor/Staff can delete if they share the publisher (if they have one).
    # 2. Journalist can delete if they are the author of the article.
    if request.user.role == User.EDITOR or request.user.is_staff:
        if (
            article.publisher
            and request.user.publisher
            and request.user.publisher != article.publisher
        ):
            return HttpResponseForbidden(
                "Access denied. You can only delete articles from your own publisher."
            )
    elif request.user.role == User.JOURNALIST:
        if article.author != request.user:
            return HttpResponseForbidden(
                "Access denied. You can only delete your own articles."
            )
    else:
        return HttpResponseForbidden("Access denied.")

    if request.method == "POST":
        title = article.title
        article.delete()
        messages.success(request, f'Article "{title}" deleted.')

        if request.user.role == User.JOURNALIST:
            return redirect("journalist_dashboard")
        return redirect("editor_dashboard")
    return render(
        request, "news_app/delete_article.html", {"article": article}
    )


@login_required
def publisher_create(request):
    """
    Allow Editors to create a new publisher.
    """
    if request.user.role != User.EDITOR and not request.user.is_staff:
        return HttpResponseForbidden(
            "Access denied. Only editors can create publishers."
        )
    if request.method == "POST":
        form = PublisherForm(request.POST)
        if form.is_valid():
            publisher = form.save()
            messages.success(
                request, f'Publisher "{publisher.name}" created successfully.'
            )
            return redirect("home")
    else:
        form = PublisherForm()
    return render(request, "news_app/create_publisher.html", {"form": form})


@login_required
def publisher_list(request):
    """
    Display a list of all publishers. Accessible to Editors.
    """
    if request.user.role != User.EDITOR and not request.user.is_staff:
        return HttpResponseForbidden(
            "Access denied. Only editors can view publishers."
        )
    publishers = Publisher.objects.all().order_by("-date_created")
    return render(
        request, "news_app/publisher_list.html", {"publishers": publishers}
    )


@login_required
def newsletter_create(request):
    """
    Allow journalists and editors to create newsletters and select articles.
    """
    if (
        request.user.role not in [User.JOURNALIST, User.EDITOR]
        and not request.user.is_staff
    ):
        return HttpResponseForbidden("Access denied.")

    if request.method == "POST":
        form = NewsletterForm(request.POST, publisher=request.user.publisher)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.publisher = request.user.publisher
            newsletter.save()
            form.save_m2m()
            messages.success(request, "Newsletter created successfully.")
            return redirect("newsletter_list")
    else:
        form = NewsletterForm(publisher=request.user.publisher)

    return render(request, "news_app/create_newsletter.html", {"form": form})


@login_required
def newsletter_update(request, pk):
    """
    Allow journalists (authors) and editors to update newsletters.
    Restricts access so that editors can only edit within their own publisher.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    # Permission check:
    # 1. Editor/Staff can edit if they share the publisher (if they have one).
    # 2. Journalist can edit if they are the author of the newsletter.
    if request.user.role == User.EDITOR or request.user.is_staff:
        if (
            newsletter.publisher
            and request.user.publisher
            and request.user.publisher != newsletter.publisher
        ):
            return HttpResponseForbidden(
                "Access denied. You can only update newsletters from your own publisher."
            )
    elif request.user.role == User.JOURNALIST:
        if newsletter.author != request.user:
            return HttpResponseForbidden(
                "Access denied. You can only update your own newsletters."
            )
    else:
        return HttpResponseForbidden("Access denied.")

    if request.method == "POST":
        form = NewsletterForm(
            request.POST, instance=newsletter, publisher=request.user.publisher
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Newsletter "{newsletter.title}" updated successfully.',
            )
            return redirect("newsletter_detail", pk=newsletter.pk)
    else:
        form = NewsletterForm(
            instance=newsletter, publisher=request.user.publisher
        )

    return render(
        request,
        "news_app/update_newsletter.html",
        {"form": form, "newsletter": newsletter},
    )


@login_required
def newsletter_delete(request, pk):
    """
    Allow journalists (authors) and editors to delete newsletters.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    # Permission check:
    # 1. Editor/Staff can delete if they share the publisher (if they have one).
    # 2. Journalist can delete if they are the author of the newsletter.
    if request.user.role == User.EDITOR or request.user.is_staff:
        if (
            newsletter.publisher
            and request.user.publisher
            and request.user.publisher != newsletter.publisher
        ):
            return HttpResponseForbidden(
                "Access denied. You can only delete newsletters from your own publisher."
            )
    elif request.user.role == User.JOURNALIST:
        if newsletter.author != request.user:
            return HttpResponseForbidden(
                "Access denied. You can only delete your own newsletters."
            )
    else:
        return HttpResponseForbidden("Access denied.")

    if request.method == "POST":
        title = newsletter.title
        newsletter.delete()
        messages.success(request, f'Newsletter "{title}" deleted.')
        return redirect("newsletter_list")

    return render(
        request, "news_app/delete_newsletter.html", {"newsletter": newsletter}
    )


@login_required
def newsletter_list(request):
    """
    Display a list of all newsletters. Accessible to all logged-in users.
    """
    newsletters = Newsletter.objects.all().order_by("-date_posted")
    return render(
        request, "news_app/newsletter_list.html", {"newsletters": newsletters}
    )


@login_required
def newsletter_detail(request, pk):
    """
    Display the details of a specific newsletter.
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return render(
        request, "news_app/newsletter_detail.html", {"newsletter": newsletter}
    )


@login_required
def subscribe_to_publisher(request, pk):
    """
    Subscribe the current reader to a publisher.
    """
    if request.user.role != User.READER:
        return JsonResponse({"error": "Access denied."}, status=403)
    publisher = get_object_or_404(Publisher, pk=pk)
    request.user.subscribed_publishers.add(publisher)
    return JsonResponse(
        {"status": "subscribed", "message": f"Subscribed to {publisher.name}!"}
    )


@login_required
def unsubscribe_from_publisher(request, pk):
    """
    Unsubscribe the current reader from a publisher.
    """
    if request.user.role != User.READER:
        return JsonResponse({"error": "Access denied."}, status=403)
    publisher = get_object_or_404(Publisher, pk=pk)
    request.user.subscribed_publishers.remove(publisher)
    return JsonResponse(
        {
            "status": "unsubscribed",
            "message": f"Unsubscribed from {publisher.name}.",
        }
    )


@login_required
def subscribe_to_journalist(request, pk):
    """
    Subscribe the current reader to a journalist.
    """
    if request.user.role != User.READER:
        return JsonResponse({"error": "Access denied."}, status=403)
    journalist = get_object_or_404(
        User, pk=pk, role__in=[User.JOURNALIST, User.EDITOR]
    )
    request.user.subscribed_journalists.add(journalist)
    return JsonResponse(
        {
            "status": "subscribed",
            "message": f"Subscribed to {journalist.username}!",
        }
    )


@login_required
def unsubscribe_from_journalist(request, pk):
    """
    Unsubscribe the current reader from a journalist.
    """
    if request.user.role != User.READER:
        return JsonResponse({"error": "Access denied."}, status=403)
    journalist = get_object_or_404(
        User, pk=pk, role__in=[User.JOURNALIST, User.EDITOR]
    )
    request.user.subscribed_journalists.remove(journalist)
    return JsonResponse(
        {
            "status": "unsubscribed",
            "message": f"Unsubscribed from {journalist.username}.",
        }
    )


@login_required
def setup_permissions_view(request):
    """
    Create default role groups/permissions. Superuser-only utility endpoint.
    """
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    create_groups_and_permissions()
    messages.success(request, "Groups and permissions created.")
    return redirect("home")


@login_required
def journalist_profile(request, pk):
    """
    Public platform for a journalist showing their articles and trust metrics.
    """
    journalist = get_object_or_404(User, pk=pk)
    # Readers don't have public journalist stats, but they can have a profile
    is_journalist = journalist.role != User.READER

    from django.db.models import Q

    articles = (
        Article.objects.filter(
            Q(author=journalist) | Q(approved_by=journalist),
            status=Article.APPROVED,
        )
        .distinct()
        .order_by("-date_posted")
    )
    subscriber_count = journalist.subscribers.count()
    return render(
        request,
        "news_app/profile.html",
        {
            "profile_user": journalist,
            "articles": articles,
            "subscriber_count": subscriber_count,
            "is_journalist": is_journalist,
        },
    )


@login_required
def publisher_profile(request, pk):
    """
    Public platform for a publisher showing their articles and trust metrics.
    """
    publisher = get_object_or_404(Publisher, pk=pk)
    articles = Article.objects.filter(
        publisher=publisher, status=Article.APPROVED
    ).order_by("-date_posted")
    subscriber_count = publisher.subscribers.count()
    return render(
        request,
        "news_app/profile.html",
        {
            "publisher": publisher,
            "articles": articles,
            "subscriber_count": subscriber_count,
            "is_journalist": False,
        },
    )


@login_required
def edit_profile(request):
    """
    Allow journalists (and editors) to edit their profile picture and bio.
    """
    # Everyone can edit their profile picture and bio
    if request.method == "POST":
        bio = request.POST.get("bio", "").strip()
        request.user.bio = bio

        publisher_name = request.POST.get("publisher_name")
        if publisher_name:
            publisher = Publisher.objects.filter(
                name__iexact=publisher_name
            ).first()
            if publisher:
                request.user.publisher = publisher
            else:
                messages.error(
                    request,
                    f"Publisher '{publisher_name}' not found. Please choose from the list.",
                )
                return redirect("edit_profile")

        if "profile_picture" in request.FILES:
            request.user.profile_picture = request.FILES["profile_picture"]
        request.user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("journalist_profile", pk=request.user.pk)

    publishers = Publisher.objects.all()
    return render(
        request,
        "news_app/edit_profile.html",
        {"user_obj": request.user, "publishers": publishers},
    )


@login_required
def change_status(request, pk):
    """
    Quickly change the status of an article.
    """
    article = get_object_or_404(Article, pk=pk)
    if request.user.role != User.EDITOR:
        return HttpResponseForbidden("Access denied.")

    # Only enforce publisher restriction if BOTH the article and user have one
    if (
        article.publisher
        and request.user.publisher
        and request.user.publisher != article.publisher
    ):
        return HttpResponseForbidden("Access denied.")

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Article.STATUS_CHOICES):
            article.status = new_status
            if new_status == Article.APPROVED:
                article.approved_by = request.user
                if request.user.publisher:
                    article.publisher = request.user.publisher
            article.save()
            messages.success(
                request, f"Status updated to {article.get_status_display()}."
            )
        else:
            messages.error(request, "Invalid status.")

    return redirect(request.META.get("HTTP_REFERER", "editor_dashboard"))


@login_required
def publisher_edit(request, pk):
    """
    Allow editors to edit their publisher's details.
    """
    publisher = get_object_or_404(Publisher, pk=pk)
    if request.user.role != User.EDITOR or request.user.publisher != publisher:
        return HttpResponseForbidden(
            "You do not have permission to edit this publisher."
        )

    if request.method == "POST":
        publisher.name = request.POST.get("name")
        publisher.website = request.POST.get("website")
        publisher.description = request.POST.get("description")
        publisher.is_verified = "is_verified" in request.POST
        publisher.save()
        messages.success(request, "Publisher details updated.")
        return redirect("publisher_profile", pk=publisher.pk)

    return render(
        request, "news_app/publisher_edit.html", {"publisher": publisher}
    )
