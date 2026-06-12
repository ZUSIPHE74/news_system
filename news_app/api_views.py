from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from .models import Article, User
from .serializers import ArticleSerializer


class IsJournalist(BasePermission):
    """
    Permission class allowing only Journalists to perform write operations (POST).
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.JOURNALIST
        )


class IsEditorOrAuthor(BasePermission):
    """
    Permission class allowing only Editors or the original Author to update/delete.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.EDITOR:
            return True
        return obj.author == request.user


class ArticleListCreateAPIView(ListAPIView, CreateAPIView):
    """
    GET /api/articles/ - Return all approved articles.
    POST /api/articles/ - Create article (journalists only).
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Article.objects.filter(status=Article.APPROVED).order_by(
            "-date_posted"
        )

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsJournalist()]
        return super().get_permissions()

    def perform_create(self, serializer):
        # Default newly submitted articles to PENDING review status
        serializer.save(author=self.request.user, status=Article.PENDING)


class SubscribedArticlesAPIView(ListAPIView):
    """
    GET /api/articles/subscribed/ - Return articles only from followed publishers/journalists.
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        subscribed_publishers = user.subscribed_publishers.all()
        subscribed_journalists = user.subscribed_journalists.all()
        return (
            Article.objects.filter(status=Article.APPROVED)
            .filter(
                Q(publisher__in=subscribed_publishers)
                | Q(author__in=subscribed_journalists)
            )
            .distinct()
            .order_by("-date_posted")
        )


class ArticleDetailAPIView(RetrieveUpdateDestroyAPIView):
    """
    GET /api/articles/<id>/ - Retrieve an article.
    PUT /api/articles/<id>/ - Update article (editors/journalists).
    DELETE /api/articles/<id>/ - Delete article (editors/journalists).
    """

    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated(), IsEditorOrAuthor()]
        return super().get_permissions()

    def perform_update(self, serializer):
        # Prevent non-editors from setting the status to APPROVED
        if "status" in self.request.data or "approved" in self.request.data:
            if self.request.user.role != User.EDITOR:
                serializer.save(
                    status=self.get_object().status,
                    approved=self.get_object().approved,
                )
                return
        serializer.save()


class ApprovedArticleLogView(CreateAPIView):
    """
    API endpoint to log approved articles.
    Simulates external sharing by receiving article details via POST.
    """

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            print(
                f"LOG: Article '{serializer.validated_data.get('title')}' "
                "has been approved and shared."
            )
            return Response(
                {
                    "status": "Article logged successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
