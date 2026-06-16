"""
Seeding script to create mock publishers, journalists, editors, and articles
for demonstration and testing purposes.
"""

import os
import django

# Set up Django environment before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "news_system.settings")
django.setup()

# noqa: E402
from news_app.models import Article, User, Publisher  # noqa: E402

publisher, _ = Publisher.objects.get_or_create(
    name="Tech Insights",
    defaults={
        "website": "https://techinsights.example.com",
        "description": "Software Engineering News",
        "is_verified": True,
    },
)
publisher.is_verified = True
publisher.save()

# Journalist author
author, _ = User.objects.get_or_create(
    username="se_journalist",
    defaults={
        "email": "se_writer@example.com",
        "role": User.JOURNALIST,
        "publisher": publisher,
        "is_verified": True,
    },
)
author.is_verified = True
if not author.password:
    author.set_password("SecurePassword123!")
author.save()

# Editor for approval (Requirement 6: Only Editor can approve)
editor, _ = User.objects.get_or_create(
    username="se_editor",
    defaults={
        "email": "se_editor@example.com",
        "role": User.EDITOR,
        "publisher": publisher,
        "is_verified": True,
    },
)
editor.is_verified = True
if not editor.password:
    editor.set_password("SecurePassword123!")
editor.save()

articles_data = [
    {
        "title": "The Future of AI in Software Engineering",
        "content": (
            "Artificial Intelligence is revolutionizing how code is written, "
            "tested, and deployed."
        ),
        "status": Article.APPROVED,
    },
    {
        "title": "Understanding Microservices Architecture",
        "content": (
            "Microservices allow large teams to build scalable software by "
            "breaking down monoliths."
        ),
        "status": Article.APPROVED,
    },
    {
        "title": "Best Practices for CI/CD Pipelines",
        "content": (
            "Continuous Integration and Deployment are essential for modern "
            "agile methodologies."
        ),
        "status": Article.APPROVED,
    },
    {
        "title": "Demystifying Rust for Systems Programming",
        "content": (
            "Rust offers memory safety without garbage collection, making it "
            "a popular choice."
        ),
        "status": Article.APPROVED,
    },
]

added = 0
for data in articles_data:
    obj, created = Article.objects.get_or_create(
        title=data["title"],
        defaults={
            "content": data["content"],
            "status": data["status"],
            "author": author,
            "publisher": publisher,
            "poster_type": Article.POSTER_PUBLISHER,
            "approved_by": editor,
        },
    )
    if created:
        added += 1

print(
    f"Successfully seeded {added} Software Engineering articles with Editor approval."
)
