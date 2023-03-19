from model_bakery import seq
from model_bakery.recipe import Recipe

from apps.room.models import Room

room = Recipe(Room, name=seq("Vacation "), description="A description")
