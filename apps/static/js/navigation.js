import * as bootstrap from "bootstrap";

window.bootstrap = bootstrap;

(function () {
  if (window.__yamsaNavigationInitialized) {
    return;
  }
  window.__yamsaNavigationInitialized = true;

  const THEME_STORAGE_KEY = 'theme';
  const THEME_PREFERENCES = ['light', 'dark', 'auto'];
  // No stored preference means the system decides; the inline head script resolves it the same way.
  const DEFAULT_THEME_PREFERENCE = 'auto';
  const prefersDark = typeof window.matchMedia === 'function'
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null;

  const getStoredPreference = () => {
    try {
      const stored = localStorage.getItem(THEME_STORAGE_KEY);
      return THEME_PREFERENCES.includes(stored) ? stored : DEFAULT_THEME_PREFERENCE;
    } catch (error) {
      console.error('Unable to read theme preference from localStorage', error);
      return DEFAULT_THEME_PREFERENCE;
    }
  };

  const setStoredPreference = (preference) => {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, preference);
    } catch (error) {
      console.error('Unable to persist theme preference to localStorage', error);
    }
  };

  const resolveTheme = (preference) => {
    if (preference !== 'auto') {
      return preference;
    }

    // Without matchMedia there is no system theme to follow, so fall back to the app's default.
    if (!prefersDark) {
      return 'dark';
    }

    return prefersDark.matches ? 'dark' : 'light';
  };

  // The browser paints its own chrome (address bar, task switcher) from this, so a theme switch
  // that leaves it alone shows the old theme around the page.
  const applyBrowserThemeColor = () => {
    const meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) {
      return;
    }

    const canvas = getComputedStyle(document.documentElement).getPropertyValue('--yamsa-canvas').trim();
    if (canvas) {
      meta.setAttribute('content', canvas);
    }
  };

  // The buttons offer the preference, not the resolved theme: `auto` stays pressed while the
  // system flips the page between light and dark.
  const applyThemeToggleState = (preference) => {
    document.querySelectorAll('[data-theme-value]').forEach((button) => {
      const isSelected = button.dataset.themeValue === preference;
      button.setAttribute('aria-pressed', String(isSelected));
      button.classList.toggle('active', isSelected);
    });
  };

  const applyPreference = (preference) => {
    document.documentElement.setAttribute('data-bs-theme', resolveTheme(preference));
    applyBrowserThemeColor();
    applyThemeToggleState(preference);
  };

  const initThemeToggle = () => {
    applyPreference(getStoredPreference());

    document.addEventListener('click', (event) => {
      const button = event.target.closest('[data-theme-value]');
      if (!button) {
        return;
      }

      const value = button.dataset.themeValue;
      if (!THEME_PREFERENCES.includes(value)) {
        return;
      }

      setStoredPreference(value);
      applyPreference(value);
    });

    if (prefersDark) {
      const handleColorSchemeChange = () => {
        if (getStoredPreference() === 'auto') {
          applyPreference('auto');
        }
      };

      if (typeof prefersDark.addEventListener === 'function') {
        prefersDark.addEventListener('change', handleColorSchemeChange);
      } else if (typeof prefersDark.addListener === 'function') {
        prefersDark.addListener(handleColorSchemeChange);
      }
    }
  };

  const initShareButtons = () => {
    if (!navigator.clipboard) {
      return;
    }

    document.addEventListener('click', (event) => {
      const button = event.target.closest('[data-copy-share-url]');
      if (!button) {
        return;
      }

      const shareUrl = (button.dataset.shareUrl || window.location.href).trim();
      navigator.clipboard.writeText(shareUrl).catch((error) => {
        console.error('Failed to copy share URL', error);
      });
    });
  };

  const initOffcanvasCleanup = () => {
    const removeExcessBackdrops = () => {
      const backdrops = document.getElementsByClassName('offcanvas-backdrop');
      while (backdrops.length > 1) {
        const target = backdrops[0];
        if (target && target.parentNode) {
          target.parentNode.removeChild(target);
        } else {
          break;
        }
      }
    };

    document.addEventListener('shown.bs.offcanvas', (event) => {
      if (event.target.id === 'offcanvasNavbar') {
        removeExcessBackdrops();
      }
    });

    document.addEventListener('hidden.bs.offcanvas', (event) => {
      if (event.target.id === 'offcanvasNavbar') {
        removeExcessBackdrops();
      }
    });
  };

  const scrollDocumentToTop = () => {
    if (typeof window.scrollTo === 'function') {
      window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
      return;
    }

    if (document.documentElement) {
      document.documentElement.scrollTop = 0;
    }

    if (document.body) {
      document.body.scrollTop = 0;
    }
  };

  const initRoomNavigationScrollReset = () => {
    const isBodyTarget = (target) => {
      if (!target) {
        return false;
      }

      if (target === document.body) {
        return true;
      }

      const targetId = typeof target.id === 'string' ? target.id.toLowerCase() : '';
      return targetId === 'body';
    };

    const handleSwap = (event) => {
      const detail = event ? event.detail : null;
      const target = detail && detail.target ? detail.target : event.target;
      if (!isBodyTarget(target)) {
        return;
      }

      if (typeof window.requestAnimationFrame === 'function') {
        window.requestAnimationFrame(scrollDocumentToTop);
      } else {
        scrollDocumentToTop();
      }
    };

    document.addEventListener('htmx:afterSwap', handleSwap);
    document.addEventListener('htmx:historyRestore', handleSwap);
  };

  const PROFILE_PICTURE_FALLBACK_SELECTOR = '[data-profile-picture-fallback-url]';
  const CATEGORY_COLOR_SELECTOR = '[data-category-color]';

  const initProfilePictureFallbacks = () => {
    document.querySelectorAll(PROFILE_PICTURE_FALLBACK_SELECTOR).forEach((img) => {
      if (img.dataset.profilePictureFallbackBound === 'true') {
        return;
      }

      const fallbackUrl = img.dataset.profilePictureFallbackUrl;
      if (!fallbackUrl) {
        return;
      }

      const handleError = () => {
        if (img.src !== fallbackUrl) {
          img.src = fallbackUrl;
        }
        img.removeEventListener('error', handleError);
      };

      img.addEventListener('error', handleError);
      img.dataset.profilePictureFallbackBound = 'true';

      if (img.complete && img.naturalWidth === 0) {
        handleError();
      }
    });
  };

  const applyDataStyleVars = () => {
    document.querySelectorAll(CATEGORY_COLOR_SELECTOR).forEach((element) => {
      const categoryColor = element.dataset.categoryColor;
      if (categoryColor) {
        element.style.setProperty('--category-color', categoryColor);
      }
    });
  };

  const refreshDynamicElements = () => {
    initProfilePictureFallbacks();
    applyDataStyleVars();
    // A swap of #body brings a fresh side menu, and with it toggle buttons that know nothing
    // about the stored preference.
    applyThemeToggleState(getStoredPreference());
  };

  const KEYBOARD_CLICK_SELECTOR = '[data-keyboard-click]';

  /*
   * Enter/Space activation for elements that only look like buttons.
   *
   * htmx cannot carry this itself: its `keyup[...]` trigger filters and `hx-on:` handlers are
   * compiled with new Function(), which the CSP (script-src without unsafe-eval) refuses - htmx
   * then fires the trigger unconditionally, on any key. A delegated listener in this nonce'd
   * bundle has neither problem, and being on `document` it survives every HTMX swap.
   */
  const handleKeyboardActivation = (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') {
      return;
    }

    const target = event.target;
    // The marked element itself only. A focused descendant that is a real control already gets a
    // synthetic click from the browser, and clicking the ancestor too would navigate twice.
    if (!target || typeof target.matches !== 'function' || !target.matches(KEYBOARD_CLICK_SELECTOR)) {
      return;
    }

    // Space would scroll the page.
    event.preventDefault();
    target.click();
  };

  const handleNavigationClick = (event) => {
    const stopPropagationEl = event.target.closest('[data-stop-propagation]');
    if (stopPropagationEl) {
      event.stopPropagation();
    }

    const removeButton = event.target.closest('[data-split-row-remove]');
    if (removeButton) {
      const splitRow = removeButton.closest('.split-row');
      if (splitRow) {
        splitRow.remove();
      }
    }

    const dismissButton = event.target.closest('[data-dismiss]');
    if (dismissButton) {
      const dismissable = dismissButton.closest('[data-dismissable]');
      if (dismissable) {
        dismissable.remove();
      }
    }
  };

  const init = () => {
    initThemeToggle();
    initShareButtons();
    initOffcanvasCleanup();
    initRoomNavigationScrollReset();
    refreshDynamicElements();
    document.addEventListener('click', handleNavigationClick);
    document.addEventListener('keydown', handleKeyboardActivation);

    if (document.body) {
      document.body.addEventListener('htmx:afterSwap', refreshDynamicElements);
      document.body.addEventListener('htmx:historyRestore', refreshDynamicElements);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
