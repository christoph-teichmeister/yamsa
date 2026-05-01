from whitenoise.storage import CompressedManifestStaticFilesStorage


class ManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    # manifest_strict only guards stored_name() (runtime), not _stored_name()
    # (post-processing). Override _stored_name() so missing source-map references
    # from third-party packages don't abort collectstatic.
    # TODO CT: Check if django-passkeys has fixed the missing bootstrap-toggle.min.js.map
    #       and remove this class + revert settings.py to CompressedManifestStaticFilesStorage.
    #       Tracking issue: https://github.com/mkalioby/django-passkeys/issues
    def _stored_name(self, name, hashed_files):
        try:
            return super()._stored_name(name, hashed_files)
        except ValueError:
            if name.endswith(".map"):
                return name
            raise
