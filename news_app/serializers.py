from rest_framework import serializers
from .models import Article, Publisher, User, Newsletter


class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializer for the Publisher model.
    """

    class Meta:
        model = Publisher
        fields = ["id", "name", "website", "description"]


class AuthorSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model, focusing on author details.
    """

    class Meta:
        model = User
        fields = ["id", "username", "role"]


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Article model, including nested author and publisher details.
    """

    author = AuthorSerializer(read_only=True)
    publisher = PublisherSerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "date_posted",
            "author",
            "publisher",
            "poster_type",
            "status",
            "approved",
        ]


class NewsletterSerializer(serializers.ModelSerializer):
    """
    Serializer for the Newsletter model.
    """

    author = AuthorSerializer(read_only=True)
    articles = ArticleSerializer(many=True, read_only=True)

    class Meta:
        model = Newsletter
        fields = [
            "id",
            "title",
            "description",
            "content",
            "created_at",
            "date_posted",
            "author",
            "articles",
        ]


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the Custom User model, enforcing mutual exclusivity of role-based fields.
    """

    subscribed_publishers = PublisherSerializer(many=True, read_only=True)
    subscribed_journalists = AuthorSerializer(many=True, read_only=True)
    authored_articles = ArticleSerializer(many=True, read_only=True)
    authored_newsletters = NewsletterSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "subscribed_publishers",
            "subscribed_journalists",
            "authored_articles",
            "authored_newsletters",
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.role == User.JOURNALIST:
            ret["subscribed_publishers"] = None
            ret["subscribed_journalists"] = None
        elif instance.role == User.READER:
            ret["authored_articles"] = None
            ret["authored_newsletters"] = None
        return ret
