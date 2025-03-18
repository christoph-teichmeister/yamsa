from django.db.models import Manager

from apps.news.querysets.feed_item import FeedItemQuerySet


class FeedItemManager(Manager.from_queryset(FeedItemQuerySet)):
    pass
