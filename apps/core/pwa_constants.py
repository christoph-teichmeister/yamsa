# Names the service worker template reads back from the response it just fetched, so both sides
# have to agree on the spelling.
SCOPE_HEADER_NAME = "X-Yamsa-Scope"
CACHED_AT_HEADER_NAME = "X-Yamsa-Cached-At"

# Sent on a request the client makes only to fill its offline cache. Views that would otherwise
# treat a GET as a visit check for it.
PREFETCH_HEADER_NAME = "X-Yamsa-Prefetch"

ANONYMOUS_SCOPE = "anon"
