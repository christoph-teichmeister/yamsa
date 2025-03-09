from django.db.models import Manager

from apps.news.querysets.news import NewsQuerySet


class NewsManager(Manager.from_queryset(NewsQuerySet)):
    pass
