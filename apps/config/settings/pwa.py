from django.urls import reverse_lazy

from apps.config.settings.base import DEBUG, STATIC_URL

# PWA
# ------------------------------------------------------------------------------


PWA_OFFLINE_URL = reverse_lazy("core:offline")
PWA_SERVICE_WORKER = {
    # Every cache the service worker owns starts with this, so purging by prefix also reaches the
    # caches left behind by earlier naming schemes.
    "cache_prefix": "yamsa",
    "offline_url": PWA_OFFLINE_URL,
    # Names, not URLs. What a name is served under is only known once the app registry stands, and
    # the two kinds do not agree: ManifestStaticFilesStorage hashes a static file, render_bundle
    # leaves a bundle unhashed. ServiceWorkerView therefore resolves each kind through the same
    # machinery the templates use - a precached URL the page never requests caches nothing.
    "precache_static": [
        "base.css",
        "customClasses.css",
        "htmxIndicatorRequest.css",
        "icons/sprite.svg",
    ],
    # The extension per bundle mirrors what base.html asks for: `tailwind` also emits a .js stub
    # that no page loads.
    "precache_bundles": {
        "tailwind": "css",
        "htmx": "js",
        "navigation": "js",
        "offline": "js",
        "dialog": "js",
        "transaction-list": "js",
        "charts": "js",
    },
    "static_url_prefix": STATIC_URL,
    # Ceiling on the HTML pages kept for offline reading. Room pages are the point of the cache and
    # a busy account visits many of them, so without a bound the cache grows until the browser
    # evicts the whole origin - which takes the precached app shell with it.
    "max_cached_pages": 40,
}

MANIFEST = {
    "background_color": "#2d2a2e",
    "categories": ["finance", "lifestyle", "productivity", "shopping", "utilities"],
    "description": "Yet another money split app",
    "dir": "auto",
    "display": "fullscreen",
    "display_override": ["window-controls-overlay", "fullscreen"],
    "edge_side_panel": {},
    "features": [],
    "icons": [
        {"src": "/static/images/favicon.ico", "sizes": "48x48", "type": "image/ico"},
        {"src": "/static/images/favicons/windows11/SmallTile.scale-100.png", "sizes": "71x71"},
        {"src": "/static/images/favicons/windows11/SmallTile.scale-125.png", "sizes": "89x89"},
        {"src": "/static/images/favicons/windows11/SmallTile.scale-150.png", "sizes": "107x107"},
        {"src": "/static/images/favicons/windows11/SmallTile.scale-200.png", "sizes": "142x142"},
        {"src": "/static/images/favicons/windows11/SmallTile.scale-400.png", "sizes": "284x284"},
        {"src": "/static/images/favicons/windows11/Square150x150Logo.scale-100.png", "sizes": "150x150"},
        {"src": "/static/images/favicons/windows11/Square150x150Logo.scale-125.png", "sizes": "188x188"},
        {"src": "/static/images/favicons/windows11/Square150x150Logo.scale-150.png", "sizes": "225x225"},
        {"src": "/static/images/favicons/windows11/Square150x150Logo.scale-200.png", "sizes": "300x300"},
        {"src": "/static/images/favicons/windows11/Square150x150Logo.scale-400.png", "sizes": "600x600"},
        {"src": "/static/images/favicons/windows11/Wide310x150Logo.scale-100.png", "sizes": "310x150"},
        {"src": "/static/images/favicons/windows11/Wide310x150Logo.scale-125.png", "sizes": "388x188"},
        {"src": "/static/images/favicons/windows11/Wide310x150Logo.scale-150.png", "sizes": "465x225"},
        {"src": "/static/images/favicons/windows11/Wide310x150Logo.scale-200.png", "sizes": "620x300"},
        {"src": "/static/images/favicons/windows11/Wide310x150Logo.scale-400.png", "sizes": "1240x600"},
        {"src": "/static/images/favicons/windows11/LargeTile.scale-100.png", "sizes": "310x310"},
        {"src": "/static/images/favicons/windows11/LargeTile.scale-125.png", "sizes": "388x388"},
        {"src": "/static/images/favicons/windows11/LargeTile.scale-150.png", "sizes": "465x465"},
        {"src": "/static/images/favicons/windows11/LargeTile.scale-200.png", "sizes": "620x620"},
        {"src": "/static/images/favicons/windows11/LargeTile.scale-400.png", "sizes": "1240x1240"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.scale-100.png", "sizes": "44x44"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.scale-125.png", "sizes": "55x55"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.scale-150.png", "sizes": "66x66"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.scale-200.png", "sizes": "88x88"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.scale-400.png", "sizes": "176x176"},
        {"src": "/static/images/favicons/windows11/StoreLogo.scale-100.png", "sizes": "50x50"},
        {"src": "/static/images/favicons/windows11/StoreLogo.scale-125.png", "sizes": "63x63"},
        {"src": "/static/images/favicons/windows11/StoreLogo.scale-150.png", "sizes": "75x75"},
        {"src": "/static/images/favicons/windows11/StoreLogo.scale-200.png", "sizes": "100x100"},
        {"src": "/static/images/favicons/windows11/StoreLogo.scale-400.png", "sizes": "200x200"},
        {"src": "/static/images/favicons/windows11/SplashScreen.scale-100.png", "sizes": "620x300"},
        {"src": "/static/images/favicons/windows11/SplashScreen.scale-125.png", "sizes": "775x375"},
        {"src": "/static/images/favicons/windows11/SplashScreen.scale-150.png", "sizes": "930x450"},
        {"src": "/static/images/favicons/windows11/SplashScreen.scale-200.png", "sizes": "1240x600"},
        {"src": "/static/images/favicons/windows11/SplashScreen.scale-400.png", "sizes": "2480x1200"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-16.png", "sizes": "16x16"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-20.png", "sizes": "20x20"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-24.png", "sizes": "24x24"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-30.png", "sizes": "30x30"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-32.png", "sizes": "32x32"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-36.png", "sizes": "36x36"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-40.png", "sizes": "40x40"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-44.png", "sizes": "44x44"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-48.png", "sizes": "48x48"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-60.png", "sizes": "60x60"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-64.png", "sizes": "64x64"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-72.png", "sizes": "72x72"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-80.png", "sizes": "80x80"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-96.png", "sizes": "96x96"},
        {"src": "/static/images/favicons/windows11/Square44x44Logo.targetsize-256.png", "sizes": "256x256"},
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-16.png",
            "sizes": "16x16",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-20.png",
            "sizes": "20x20",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-24.png",
            "sizes": "24x24",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-30.png",
            "sizes": "30x30",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-32.png",
            "sizes": "32x32",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-36.png",
            "sizes": "36x36",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-40.png",
            "sizes": "40x40",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-44.png",
            "sizes": "44x44",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-48.png",
            "sizes": "48x48",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-60.png",
            "sizes": "60x60",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-64.png",
            "sizes": "64x64",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-72.png",
            "sizes": "72x72",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-80.png",
            "sizes": "80x80",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-96.png",
            "sizes": "96x96",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-unplated_targetsize-256.png",
            "sizes": "256x256",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-16.png",
            "sizes": "16x16",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-20.png",
            "sizes": "20x20",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-24.png",
            "sizes": "24x24",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-30.png",
            "sizes": "30x30",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-32.png",
            "sizes": "32x32",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-36.png",
            "sizes": "36x36",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-40.png",
            "sizes": "40x40",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-44.png",
            "sizes": "44x44",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-48.png",
            "sizes": "48x48",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-60.png",
            "sizes": "60x60",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-64.png",
            "sizes": "64x64",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-72.png",
            "sizes": "72x72",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-80.png",
            "sizes": "80x80",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-96.png",
            "sizes": "96x96",
        },
        {
            "src": "/static/images/favicons/windows11/Square44x44Logo.altform-lightunplated_targetsize-256.png",
            "sizes": "256x256",
        },
        {
            "src": "/static/images/favicons/android/android-launchericon-512-512.png",
            "sizes": "512x512",
            "purpose": "any maskable",
        },
        {
            "src": "/static/images/favicons/android/android-launchericon-192-192.png",
            "sizes": "192x192",
            "purpose": "any maskable",
        },
        {
            "src": "/static/images/favicons/android/android-launchericon-144-144.png",
            "sizes": "144x144",
            "purpose": "any maskable",
        },
        {
            "src": "/static/images/favicons/android/android-launchericon-96-96.png",
            "sizes": "96x96",
            "purpose": "any maskable",
        },
        {
            "src": "/static/images/favicons/android/android-launchericon-72-72.png",
            "sizes": "72x72",
            "purpose": "any maskable",
        },
        {
            "src": "/static/images/favicons/android/android-launchericon-48-48.png",
            "sizes": "48x48",
            "purpose": "any maskable",
        },
        {"src": "/static/images/favicons/ios/16.png", "sizes": "16x16"},
        {"src": "/static/images/favicons/ios/20.png", "sizes": "20x20"},
        {"src": "/static/images/favicons/ios/29.png", "sizes": "29x29"},
        {"src": "/static/images/favicons/ios/32.png", "sizes": "32x32"},
        {"src": "/static/images/favicons/ios/40.png", "sizes": "40x40"},
        {"src": "/static/images/favicons/ios/50.png", "sizes": "50x50"},
        {"src": "/static/images/favicons/ios/57.png", "sizes": "57x57"},
        {"src": "/static/images/favicons/ios/58.png", "sizes": "58x58"},
        {"src": "/static/images/favicons/ios/60.png", "sizes": "60x60"},
        {"src": "/static/images/favicons/ios/64.png", "sizes": "64x64"},
        {"src": "/static/images/favicons/ios/72.png", "sizes": "72x72"},
        {"src": "/static/images/favicons/ios/76.png", "sizes": "76x76"},
        {"src": "/static/images/favicons/ios/80.png", "sizes": "80x80"},
        {"src": "/static/images/favicons/ios/87.png", "sizes": "87x87"},
        {"src": "/static/images/favicons/ios/100.png", "sizes": "100x100"},
        {"src": "/static/images/favicons/ios/114.png", "sizes": "114x114"},
        {"src": "/static/images/favicons/ios/120.png", "sizes": "120x120", "purpose": "any maskable"},
        {"src": "/static/images/favicons/ios/128.png", "sizes": "128x128", "purpose": "any maskable"},
        {"src": "/static/images/favicons/ios/144.png", "sizes": "144x144", "purpose": "any maskable"},
        {"src": "/static/images/favicons/ios/152.png", "sizes": "152x152", "purpose": "any maskable"},
        {"src": "/static/images/favicons/ios/167.png", "sizes": "167x167", "purpose": "any maskable"},
        {"src": "/static/images/favicons/ios/180.png", "sizes": "180x180", "purpose": "any maskable"},
        {"src": "/static/images/favicons/ios/192.png", "sizes": "192x192", "purpose": "any maskable"},
        {"src": "/static/images/favicons/ios/256.png", "sizes": "256x256", "purpose": "any maskable"},
        {"src": "/static/images/favicons/ios/512.png", "sizes": "512x512", "purpose": "any maskable"},
        {"src": "/static/images/favicons/ios/1024.png", "sizes": "1024x1024", "purpose": "any maskable"},
    ],
    "id": "yamsa",
    "lang": "en-US",
    "launch_handler": {"client_mode": ["navigate-existing", "auto"]},
    "name": "yamsa - Yet another money split app",
    "orientation": "any",
    "related_applications": [],
    "prefer_related_applications": False,
    "screenshots": [],
    "scope": "/",
    "short_name": "yamsa",
    "splash_screens": [],
    "start_url": "/",
    "theme_color": "#2d2a2e",
}
PWA_SERVICE_WORKER_DEBUG = DEBUG
