from django.forms import ModelForm

from apps.news.models import NewsComment


class NewsCommentCreateForm(ModelForm):
    class Meta:
        model = NewsComment
        fields = ("news", "comment")
