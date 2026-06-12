from django import forms
from .models import Publisher, Newsletter, Article


class PublisherForm(forms.ModelForm):
    """
    Form for creating and updating Publishers.
    """

    class Meta:
        model = Publisher
        fields = ["name", "website", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Publisher Name"}),
            "website": forms.URLInput(
                attrs={"placeholder": "https://example.com"}
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "A brief description of the publisher...",
                    "rows": 4,
                }
            ),
        }


class NewsletterForm(forms.ModelForm):
    """
    Form for creating Newsletters, filtered by the publisher's approved articles.
    """

    class Meta:
        model = Newsletter
        fields = ["title", "content", "articles"]
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Newsletter Title"}
            ),
            "content": forms.Textarea(
                attrs={
                    "placeholder": "Write your newsletter content here...",
                    "rows": 8,
                }
            ),
            "articles": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        """
        Filter the articles queryset to show only approved articles from the publisher.
        """
        publisher = kwargs.pop("publisher", None)
        super().__init__(*args, **kwargs)
        if publisher:
            self.fields["articles"].queryset = Article.objects.filter(
                publisher=publisher, status=Article.APPROVED
            ).order_by("-date_posted")
        else:
            self.fields["articles"].queryset = Article.objects.filter(
                status=Article.APPROVED
            ).order_by("-date_posted")


class ArticleForm(forms.ModelForm):
    """
    Form for Editors to update articles.
    """

    class Meta:
        model = Article
        fields = [
            "title",
            "content",
            "image",
            "status",
            "poster_type",
            "publisher",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(
                attrs={"class": "form-control", "rows": 10}
            ),
            "status": forms.Select(attrs={"class": "form-control"}),
            "poster_type": forms.Select(attrs={"class": "form-control"}),
            "publisher": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["publisher"].required = False
        self.fields["image"].required = False


class JournalistArticleForm(forms.ModelForm):
    """
    Form for Journalists to submit articles, allowing them to choose the poster.
    """

    class Meta:
        model = Article
        fields = ["title", "content", "image", "poster_type"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter article title",
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 10,
                    "placeholder": "Write your content here...",
                }
            ),
            "poster_type": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user and not user.publisher:
            # If user has no publisher, they can only post as independent.
            self.fields["poster_type"].choices = [
                (Article.POSTER_JOURNALIST, "Independent Journalist")
            ]
            self.fields["poster_type"].initial = Article.POSTER_JOURNALIST
