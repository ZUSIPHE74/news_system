from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from rest_framework.authtoken.models import Token

from .models import User, Publisher, Article, Newsletter
from .signals import create_groups_and_permissions


class UserGroupAssignmentTest(TestCase):

    def setUp(self):
        create_groups_and_permissions()

    def test_reader_assigned_to_reader_group(self):
        user = User.objects.create_user(
            username="reader1",
            password="pass",
            role=User.READER,
            email="reader1@test.com",
        )
        self.assertTrue(user.groups.filter(name="Reader").exists())

    def test_journalist_assigned_to_journalist_group(self):
        user = User.objects.create_user(
            username="journalist1",
            password="pass",
            role=User.JOURNALIST,
            email="journalist1@test.com",
        )
        self.assertTrue(user.groups.filter(name="Journalist").exists())

    def test_editor_assigned_to_editor_group(self):
        user = User.objects.create_user(
            username="editor1",
            password="pass",
            role=User.EDITOR,
            email="editor1@test.com",
        )
        self.assertTrue(user.groups.filter(name="Editor").exists())


class SubscribedArticlesAPITest(TestCase):

    def setUp(self):
        create_groups_and_permissions()

        self.publisher = Publisher.objects.create(
            name="Tech Weekly", website="http://techweekly.com"
        )

        self.journalist = User.objects.create_user(
            username="journalist_a",
            password="pass",
            role=User.JOURNALIST,
            email="journalist_a@test.com",
        )

        self.reader = User.objects.create_user(
            username="reader_a",
            password="pass",
            role=User.READER,
            email="reader_a@test.com",
        )
        self.reader.subscribed_publishers.add(self.publisher)

        self.journalist_subscriber = User.objects.create_user(
            username="reader_b",
            password="pass",
            role=User.READER,
            email="reader_b@test.com",
        )
        self.journalist_subscriber.subscribed_journalists.add(self.journalist)

        self.unsubscribed_reader = User.objects.create_user(
            username="reader_c",
            password="pass",
            role=User.READER,
            email="reader_c@test.com",
        )

        self.article_from_publisher = Article.objects.create(
            title="Publisher Article",
            content="Content about tech.",
            author=self.journalist,
            publisher=self.publisher,
            status=Article.APPROVED,
        )

        self.article_from_journalist = Article.objects.create(
            title="Independent Article",
            content="Content by journalist.",
            author=self.journalist,
            publisher=None,
            status=Article.APPROVED,
        )

        self.draft_article = Article.objects.create(
            title="Draft Article",
            content="Not yet published.",
            author=self.journalist,
            publisher=self.publisher,
            status=Article.DRAFT,
        )

        self.client = APIClient()

    def test_reader_subscribed_to_publisher_sees_publisher_article(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(reverse("api_articles_subscribed"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [a["title"] for a in response.data]
        self.assertIn("Publisher Article", titles)

    def test_reader_subscribed_to_journalist_sees_journalist_article(self):
        self.client.force_authenticate(user=self.journalist_subscriber)
        response = self.client.get(reverse("api_articles_subscribed"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [a["title"] for a in response.data]
        self.assertIn("Independent Article", titles)

    def test_unsubscribed_reader_sees_no_articles(self):
        self.client.force_authenticate(user=self.unsubscribed_reader)
        response = self.client.get(reverse("api_articles_subscribed"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_draft_articles_not_returned_in_api(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.get(reverse("api_articles_subscribed"))
        self.titles = [a["title"] for a in response.data]
        self.assertNotIn("Draft Article", self.titles)

    def test_unauthenticated_user_denied(self):
        response = self.client.get(reverse("api_articles_subscribed"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ArticleApprovalWorkflowTest(TestCase):

    def setUp(self):
        create_groups_and_permissions()
        self.journalist = User.objects.create_user(
            username="j_test",
            password="pass",
            role=User.JOURNALIST,
            email="j_test@test.com",
        )
        self.editor = User.objects.create_user(
            username="e_test",
            password="pass",
            role=User.EDITOR,
            email="e_test@test.com",
        )
        self.article = Article.objects.create(
            title="Test Article",
            content="Some content.",
            author=self.journalist,
            status=Article.PENDING,
        )

    def test_editor_can_approve_article(self):
        self.client.force_login(self.editor)
        self.client.post(
            reverse("approve_article", args=[self.article.pk]),
            {"action": "approve"},
        )
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, Article.APPROVED)
        self.assertEqual(self.article.approved_by, self.editor)

    def test_non_editor_cannot_approve_article(self):
        self.client.force_login(self.journalist)
        response = self.client.post(
            reverse("approve_article", args=[self.article.pk]),
            {"action": "approve"},
        )
        self.assertEqual(response.status_code, 403)
        self.article.refresh_from_db()
        self.assertNotEqual(self.article.status, Article.APPROVED)


class SignupViewTest(TestCase):
    """Validate account registration behavior from the public signup page."""

    def test_signup_page_is_accessible(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)

    def test_signup_creates_reader_and_redirects_to_login(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "new_reader",
                "email": "reader@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "role": User.READER,
            },
        )
        self.assertRedirects(response, reverse("login"))
        created_user = User.objects.get(username="new_reader")
        self.assertEqual(created_user.role, User.READER)

    def test_signup_creates_journalist_when_role_selected(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "new_journalist",
                "email": "journalist@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "role": User.JOURNALIST,
            },
        )
        self.assertRedirects(response, reverse("login"))
        created_user = User.objects.get(username="new_journalist")
        self.assertEqual(created_user.role, User.JOURNALIST)

    def test_signup_creates_editor_when_role_selected(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "new_editor",
                "email": "editor@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "role": User.EDITOR,
            },
        )
        self.assertRedirects(response, reverse("login"))
        created_user = User.objects.get(username="new_editor")
        self.assertEqual(created_user.role, User.EDITOR)

    def test_signup_with_invalid_role_falls_back_to_reader(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "invalid_role_user",
                "email": "invalid@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "role": "admin",
            },
        )
        self.assertRedirects(response, reverse("login"))
        created_user = User.objects.get(username="invalid_role_user")
        self.assertEqual(created_user.role, User.READER)

    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "bad_reader",
                "email": "reader@example.com",
                "password": "StrongPass123!",
                "confirm_password": "WrongPass123!",
                "role": User.READER,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="bad_reader").exists())

    def test_signup_rejects_duplicate_username(self):
        User.objects.create_user(
            username="existing",
            password="pass",
            role=User.READER,
            email="existing@test.com",
        )

        response = self.client.post(
            reverse("signup"),
            {
                "username": "existing",
                "email": "reader@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "role": User.READER,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="existing").count(), 1)

    def test_signup_requires_email(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "no_email_user",
                "email": "",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "role": User.READER,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(username="no_email_user").exists()
        )


class RoleLoginRedirectTest(TestCase):
    """Ensure users land on the correct dashboard after login."""

    def setUp(self):
        create_groups_and_permissions()
        self.reader = User.objects.create_user(
            username="reader_login",
            password="pass",
            role=User.READER,
            email="reader@login.test",
        )
        self.journalist = User.objects.create_user(
            username="journalist_login",
            password="pass",
            role=User.JOURNALIST,
            email="journalist@login.test",
        )
        self.editor = User.objects.create_user(
            username="editor_login",
            password="pass",
            role=User.EDITOR,
            email="editor@login.test",
        )

    def test_reader_redirected_to_reader_dashboard(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.reader.username, "password": "pass"},
        )
        self.assertRedirects(response, reverse("reader_dashboard"))

    def test_journalist_redirected_to_journalist_dashboard(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.journalist.username, "password": "pass"},
        )
        self.assertRedirects(response, reverse("journalist_dashboard"))

    def test_editor_redirected_to_editor_dashboard(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.editor.username, "password": "pass"},
        )
        self.assertRedirects(response, reverse("editor_dashboard"))


class RESTAPIComprehensiveTest(TestCase):
    """
    Rubric-focused automated tests verifying roles, subscriptions, auth token,
    and CRUD restrictions on the new REST API.
    """

    def setUp(self):
        create_groups_and_permissions()

        # Create test users
        self.reader = User.objects.create_user(
            username="api_reader",
            password="api_password123!",
            role=User.READER,
            email="api_reader@test.com",
        )
        self.journalist = User.objects.create_user(
            username="api_journalist",
            password="api_password123!",
            role=User.JOURNALIST,
            email="api_journalist@test.com",
        )
        self.editor = User.objects.create_user(
            username="api_editor",
            password="api_password123!",
            role=User.EDITOR,
            email="api_editor@test.com",
        )

        # Generate tokens
        self.reader_token = Token.objects.create(user=self.reader)
        self.journalist_token = Token.objects.create(user=self.journalist)
        self.editor_token = Token.objects.create(user=self.editor)

        self.publisher = Publisher.objects.create(
            name="API Chronicle", website="https://api.chronicle.org"
        )

        # Subscribe reader to the publisher
        self.reader.subscribed_publishers.add(self.publisher)

        # Create baseline articles
        self.approved_article = Article.objects.create(
            title="Approved Global News",
            content="Content accessible to everyone.",
            author=self.journalist,
            publisher=None,
            status=Article.APPROVED,
        )
        self.publisher_article = Article.objects.create(
            title="Publisher Exclusive",
            content="Branded publisher content.",
            author=self.journalist,
            publisher=self.publisher,
            status=Article.APPROVED,
        )

        self.client = APIClient()

    def test_token_retrieval_endpoint(self):
        response = self.client.post(
            reverse("api_token"),
            {"username": "api_reader", "password": "api_password123!"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_global_approved_articles_list(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.reader_token.key
        )
        response = self.client.get(reverse("api_articles"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both approved articles

    def test_subscribed_articles_feed(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.reader_token.key
        )
        response = self.client.get(reverse("api_articles_subscribed"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data), 1
        )  # Only the subscribed publisher one
        self.assertEqual(response.data[0]["title"], "Publisher Exclusive")

    def test_journalist_can_create_article_via_api(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.journalist_token.key
        )
        response = self.client.post(
            reverse("api_articles"),
            {
                "title": "API Journalist Draft",
                "content": "Article submitted via DRF.",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "pending")

    def test_reader_cannot_create_article_via_api(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.reader_token.key
        )
        response = self.client.post(
            reverse("api_articles"),
            {
                "title": "Malicious Reader Article",
                "content": "No permissions.",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_can_delete_article_via_api(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.editor_token.key
        )
        response = self.client.delete(
            reverse("api_article_detail", args=[self.approved_article.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Article.objects.filter(pk=self.approved_article.pk).exists()
        )

    @patch("news_app.signals.send_mail")
    def test_post_approval_subscriber_email_trigger(self, mock_send_mail):
        # Initial article is in PENDING state
        new_article = Article.objects.create(
            title="Subscriber Alert",
            content="Testing notifications.",
            author=self.journalist,
            status=Article.PENDING,
        )
        # Add a reader subscriber to the journalist
        self.reader.subscribed_journalists.add(self.journalist)

        # Approve the article using re-fetched entities to clear cached reverse managers
        db_article = Article.objects.get(pk=new_article.pk)
        db_article.author = User.objects.get(pk=self.journalist.pk)
        db_article.status = Article.APPROVED
        db_article.save()

        # Check mock send_mail call
        self.assertTrue(mock_send_mail.called)
        self.assertEqual(mock_send_mail.call_count, 1)


class JournalistAndEditorCRUDActionsTest(TestCase):
    """
    Test suite for new Journalist/Editor CRUD actions on articles and newsletters.
    """

    def setUp(self):
        create_groups_and_permissions()

        # Publishers
        self.pub_a = Publisher.objects.create(
            name="Publisher A", website="https://puba.com"
        )
        self.pub_b = Publisher.objects.create(
            name="Publisher B", website="https://pubb.com"
        )

        # Users
        self.journalist_a = User.objects.create_user(
            username="journalist_a",
            password="pass",
            role=User.JOURNALIST,
            email="ja@test.com",
            publisher=self.pub_a,
        )
        self.journalist_b = User.objects.create_user(
            username="journalist_b",
            password="pass",
            role=User.JOURNALIST,
            email="jb@test.com",
            publisher=self.pub_b,
        )
        self.editor_a = User.objects.create_user(
            username="editor_a",
            password="pass",
            role=User.EDITOR,
            email="ea@test.com",
            publisher=self.pub_a,
        )

        # Articles
        self.article_a = Article.objects.create(
            title="Article A",
            content="Content A",
            author=self.journalist_a,
            publisher=self.pub_a,
            status=Article.APPROVED,
        )
        self.article_b = Article.objects.create(
            title="Article B",
            content="Content B",
            author=self.journalist_b,
            publisher=self.pub_b,
            status=Article.APPROVED,
        )

        # Newsletters
        self.newsletter_a = Newsletter.objects.create(
            title="Newsletter A",
            content="Content NA",
            author=self.journalist_a,
            publisher=self.pub_a,
        )
        self.newsletter_a.articles.add(self.article_a)

    def test_journalist_can_update_own_article(self):
        self.client.force_login(self.journalist_a)
        response = self.client.post(
            reverse("update_article", args=[self.article_a.pk]),
            {
                "title": "Updated A",
                "content": "Updated content",
                "poster_type": Article.POSTER_PUBLISHER,
            },
        )
        self.assertRedirects(response, reverse("journalist_dashboard"))
        self.article_a.refresh_from_db()
        self.assertEqual(self.article_a.title, "Updated A")
        self.assertEqual(
            self.article_a.status, Article.PENDING
        )  # status resets to pending

    def test_journalist_cannot_update_other_article(self):
        self.client.force_login(self.journalist_a)
        response = self.client.post(
            reverse("update_article", args=[self.article_b.pk]),
            {"title": "Attempted Hack", "content": "Hack content"},
        )
        self.assertEqual(response.status_code, 403)

    def test_journalist_can_delete_own_article(self):
        self.client.force_login(self.journalist_a)
        response = self.client.post(
            reverse("delete_article", args=[self.article_a.pk])
        )
        self.assertRedirects(response, reverse("journalist_dashboard"))
        self.assertFalse(Article.objects.filter(pk=self.article_a.pk).exists())

    def test_journalist_cannot_delete_other_article(self):
        self.client.force_login(self.journalist_a)
        response = self.client.post(
            reverse("delete_article", args=[self.article_b.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_journalist_can_update_own_newsletter(self):
        self.client.force_login(self.journalist_a)
        response = self.client.post(
            reverse("newsletter_update", args=[self.newsletter_a.pk]),
            {"title": "Updated Newsletter", "content": "Updated news content"},
        )
        self.assertRedirects(
            response, reverse("newsletter_detail", args=[self.newsletter_a.pk])
        )
        self.newsletter_a.refresh_from_db()
        self.assertEqual(self.newsletter_a.title, "Updated Newsletter")

    def test_journalist_cannot_update_other_newsletter(self):
        # Create newsletter by journalist_b
        newsletter_b = Newsletter.objects.create(
            title="Newsletter B",
            content="Content NB",
            author=self.journalist_b,
            publisher=self.pub_b,
        )
        self.client.force_login(self.journalist_a)
        response = self.client.post(
            reverse("newsletter_update", args=[newsletter_b.pk]),
            {"title": "Hack News", "content": "Hack Content"},
        )
        self.assertEqual(response.status_code, 403)

    def test_editor_can_create_newsletter(self):
        self.client.force_login(self.editor_a)
        response = self.client.post(
            reverse("newsletter_create"),
            {
                "title": "Editor Newsletter",
                "content": "Curated by editor",
                "articles": [self.article_a.pk],
            },
        )
        self.assertRedirects(response, reverse("newsletter_list"))
        self.assertTrue(
            Newsletter.objects.filter(title="Editor Newsletter").exists()
        )

    def test_editor_can_update_newsletter_same_publisher(self):
        self.client.force_login(self.editor_a)
        response = self.client.post(
            reverse("newsletter_update", args=[self.newsletter_a.pk]),
            {"title": "Editor Updated", "content": "Updated by editor"},
        )
        self.assertRedirects(
            response, reverse("newsletter_detail", args=[self.newsletter_a.pk])
        )
        self.newsletter_a.refresh_from_db()
        self.assertEqual(self.newsletter_a.title, "Editor Updated")

    def test_editor_cannot_update_newsletter_different_publisher(self):
        newsletter_b = Newsletter.objects.create(
            title="Newsletter B",
            content="Content NB",
            author=self.journalist_b,
            publisher=self.pub_b,
        )
        self.client.force_login(self.editor_a)
        response = self.client.post(
            reverse("newsletter_update", args=[newsletter_b.pk]),
            {"title": "Editor Hack", "content": "Hack Content"},
        )
        self.assertEqual(response.status_code, 403)
