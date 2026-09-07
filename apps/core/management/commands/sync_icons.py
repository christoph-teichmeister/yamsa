from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core.icons import ICON_SOURCE_DIR, SPRITE_PATH, build_sprite, collect_icon_names, sprite_symbol_names


class Command(BaseCommand):
    help = "Rebuild apps/static/icons/sprite.svg from the icons the templates use."

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Report whether the sprite carries what the templates ask for, and write nothing.",
        )

    def handle(self, *args, **options):
        names = collect_icon_names(Path(settings.APPS_DIR))

        # Deliberately name-only, and deliberately without touching node_modules: the check
        # runs in a CI job that installs Python and nothing else. Rebuilding needs the source
        # SVGs; asking "does the sprite carry these icons" does not.
        if options["check"]:
            self._check(names)
            return

        if not ICON_SOURCE_DIR.is_dir():
            message = (
                f"{ICON_SOURCE_DIR} is missing. The sprite is built from the bootstrap-icons "
                f"devDependency; run `yarn install` first."
            )
            raise CommandError(message)

        sprite = build_sprite(names)
        if SPRITE_PATH.exists() and SPRITE_PATH.read_text(encoding="utf-8") == sprite:
            self.stdout.write(self.style.SUCCESS(f"Sprite is up to date ({len(names)} icons)."))
            return

        SPRITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SPRITE_PATH.write_text(sprite, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {SPRITE_PATH} ({len(names)} icons)."))

    def _check(self, names):
        if not SPRITE_PATH.exists():
            message = f"{SPRITE_PATH} is missing. Run `python manage.py sync_icons`."
            raise CommandError(message)

        in_sprite = sprite_symbol_names(SPRITE_PATH.read_text(encoding="utf-8"))
        missing = sorted(names - in_sprite)
        unused = sorted(in_sprite - names)

        if missing or unused:
            parts = []
            if missing:
                parts.append(f"used but not in the sprite: {', '.join(missing)}")
            if unused:
                parts.append(f"in the sprite but unused: {', '.join(unused)}")
            message = (
                "The icon sprite is out of date - "
                + "; ".join(parts)
                + ". Run `python manage.py sync_icons` and commit the result."
            )
            raise CommandError(message)

        self.stdout.write(self.style.SUCCESS(f"Sprite carries exactly the {len(names)} icons in use."))
