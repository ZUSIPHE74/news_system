"""
URL routing configuration for the news_app application.
Maps views to endpoints for Reader, Editor, and Journalist actions,
as well as subscription operations and REST API endpoints.
"""

from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token
from .api_views import (
    ArticleListCreateAPIView,
    SubscribedArticlesAPIView,
    ArticleDetailAPIView,
    ApprovedArticleLogView,
)

urlpatterns = [
    # General
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    # Dashboards
    path("reader/", views.reader_dashboard, name="reader_dashboard"),
    path(
        "journalist/", views.journalist_dashboard, name="journalist_dashboard"
    ),
    path("editor/", views.editor_dashboard, name="editor_dashboard"),
    # Articles
    path("article/<int:pk>/", views.article_detail, name="article_detail"),
    path("journalist/submit/", views.submit_article, name="submit_article"),
    path(
        "editor/approve/<int:pk>/",
        views.approve_article,
        name="approve_article",
    ),
    path(
        "editor/update/<int:pk>/", views.update_article, name="update_article"
    ),
    path("editor/status/<int:pk>/", views.change_status, name="change_status"),
    path(
        "editor/delete/<int:pk>/", views.delete_article, name="delete_article"
    ),
    # Publisher and Newsletter
    path("publishers/", views.publisher_list, name="publisher_list"),
    path("publisher/create/", views.publisher_create, name="publisher_create"),
    path(
        "newsletter/create/", views.newsletter_create, name="newsletter_create"
    ),
    path(
        "newsletter/update/<int:pk>/",
        views.newsletter_update,
        name="newsletter_update",
    ),
    path(
        "newsletter/delete/<int:pk>/",
        views.newsletter_delete,
        name="newsletter_delete",
    ),
    path("newsletters/", views.newsletter_list, name="newsletter_list"),
    path(
        "newsletter/<int:pk>/",
        views.newsletter_detail,
        name="newsletter_detail",
    ),
    # Subscriptions
    path(
        "subscribe/publisher/<int:pk>/",
        views.subscribe_to_publisher,
        name="subscribe_to_publisher",
    ),
    path(
        "unsubscribe/publisher/<int:pk>/",
        views.unsubscribe_from_publisher,
        name="unsubscribe_from_publisher",
    ),
    path(
        "subscribe/journalist/<int:pk>/",
        views.subscribe_to_journalist,
        name="subscribe_to_journalist",
    ),
    path(
        "unsubscribe/journalist/<int:pk>/",
        views.unsubscribe_from_journalist,
        name="unsubscribe_from_journalist",
    ),
    # API Endpoints
    path(
        "api/articles/",
        ArticleListCreateAPIView.as_view(),
        name="api_articles",
    ),
    path(
        "api/articles/subscribed/",
        SubscribedArticlesAPIView.as_view(),
        name="api_articles_subscribed",
    ),
    path(
        "api/articles/<int:pk>/",
        ArticleDetailAPIView.as_view(),
        name="api_article_detail",
    ),
    path(
        "api/approved/", ApprovedArticleLogView.as_view(), name="api_approved"
    ),
    path("api/token/", obtain_auth_token, name="api_token"),
    # Profiles
    path(
        "journalist-profile/<int:pk>/",
        views.journalist_profile,
        name="journalist_profile",
    ),
    path(
        "publisher-profile/<int:pk>/",
        views.publisher_profile,
        name="publisher_profile",
    ),
    path(
        "publisher/edit/<int:pk>/", views.publisher_edit, name="publisher_edit"
    ),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    # Utility
    path(
        "setup-permissions/",
        views.setup_permissions_view,
        name="setup_permissions",
    ),
]
