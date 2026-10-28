from whitenoise.storage import CompressedManifestStaticFilesStorage


class ManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    # manifest_strict only guards stored_name() (runtime), not _stored_name()
    # (post-processing). Override _stored_name() so missing source-map references
    # from third-party packages don't abort collectstatic.
    # Still needed with django-passkeys 2.1, whose bootstrap-toggle.min.js references a .map file it does not ship.
    def _stored_name(self, name: str, hashed_files: dict) -> str:
        try:
            return super()._stored_name(name, hashed_files)
        except ValueError:
            if name.endswith("bootstrap-toggle.min.js.map"):
                return name
            raise
