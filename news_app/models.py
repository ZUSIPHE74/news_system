from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Publisher(models.Model):
    """
    Represents a news publishing organization.
    """

    name = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return the name of the publisher."""
        return self.name

    @property
    def editors(self):
        """Return all editors associated with this publisher."""
        return self.staff.filter(role="editor")

    @property
    def journalists(self):
        """Return all journalists associated with this publisher."""
        return self.staff.filter(role="journalist")


class User(AbstractUser):
    """
    Custom user model supporting roles: Reader, Editor, and Journalist.
    Enforces unique email addresses.
    """

    READER = "reader"
    EDITOR = "editor"
    JOURNALIST = "journalist"

    ROLE_CHOICES = [
        (READER, "Reader"),
        (EDITOR, "Editor"),
        (JOURNALIST, "Journalist"),
    ]

    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default=READER
    )
    email = models.EmailField(unique=True)  # Enforce unique email
    is_verified = models.BooleanField(default=False)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", null=True, blank=True
    )
    bio = models.TextField(blank=True, default="")
    publisher = models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="staff",
    )

    subscribed_publishers = models.ManyToManyField(
        Publisher, blank=True, related_name="subscribers"
    )
    subscribed_journalists = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="subscribers"
    )

    def save(self, *args, **kwargs):
        """
        Custom save logic to enforce mutual exclusivity of role-based fields.
        """
        super().save(*args, **kwargs)
        if self.role == self.JOURNALIST:
            self.subscribed_publishers.clear()
            self.subscribed_journalists.clear()
        elif self.role == self.READER:
            if self.pk:
                self.authored_articles.all().delete()
                self.authored_newsletters.all().delete()

    def __str__(self):
        """Return username and role."""
        return f"{self.username} ({self.role})"


class Article(models.Model):
    """
    Represents a news article with a workflow: Draft -> Pending -> Approved/Rejected.
    """

    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

    STATUS_CHOICES = [
        (DRAFT, "Draft"),
        (PENDING, "Pending Review"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    ]

    POSTER_JOURNALIST = "journalist"
    POSTER_PUBLISHER = "publisher"
    POSTER_CHOICES = [
        (POSTER_JOURNALIST, "Independent Journalist"),
        (POSTER_PUBLISHER, "Publisher-Branded"),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="authored_articles"
    )
    publisher = models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="articles",
    )
    poster_type = models.CharField(
        max_length=20, choices=POSTER_CHOICES, default=POSTER_JOURNALIST
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=DRAFT
    )
    approved = models.BooleanField(default=False)
    image = models.ImageField(
        upload_to="article_images/", null=True, blank=True
    )
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_articles",
    )

    def save(self, *args, **kwargs):
        """Auto-synchronize approved Boolean with Article status choices."""
        self.approved = self.status == self.APPROVED
        super().save(*args, **kwargs)

    def __str__(self):
        """Return the title and poster info."""
        poster = (
            self.author.username
            if self.poster_type == self.POSTER_JOURNALIST
            else self.publisher.name
        )
        return f"{self.title} (By: {poster})"


class Newsletter(models.Model):
    """
    A collection of articles curated for a publisher's subscribers.
    Integrates many-to-many relationship with approved publisher articles.
    """

    title = models.CharField(max_length=255)
    content = models.TextField()
    description = models.TextField(blank=True, null=True)
    date_posted = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="authored_newsletters"
    )
    publisher = models.ForeignKey(
        Publisher,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="newsletters",
    )
    articles = models.ManyToManyField(
        Article, blank=True, related_name="newsletters"
    )

    def save(self, *args, **kwargs):
        """Ensure content and description are aligned."""
        if self.content and not self.description:
            self.description = self.content
        elif self.description and not self.content:
            self.content = self.description
        super().save(*args, **kwargs)

    def __str__(self):
        """Return the title of the newsletter."""
        return self.title
