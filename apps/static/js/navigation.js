(function () {
  if (window.__yamsaNavigationInitialized) {
    return;
  }
  window.__yamsaNavigationInitialized = true;

  const THEME_STORAGE_KEY = 'theme';
  const prefersDark = typeof window.matchMedia === 'function'
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null;

  const getStoredTheme = () => {
    try {
      return localStorage.getItem(THEME_STORAGE_KEY);
    } catch (error) {
      console.error('Unable to read theme preference from localStorage', error);
      return null;
    }
  };

  const setStoredTheme = (theme) => {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch (error) {
      console.error('Unable to persist theme preference to localStorage', error);
    }
  };

  const resolveTheme = (theme) => {
    if (theme === 'auto') {
      if (!prefersDark) {
        return 'dark';
      }

      return prefersDark.matches ? 'dark' : 'light';
    }

    return theme;
  };

  const applyTheme = (theme) => {
    if (!theme) {
      return;
    }

    document.documentElement.setAttribute('data-bs-theme', resolveTheme(theme));
  };

  const initThemeToggle = () => {
    applyTheme(getStoredTheme() || resolveTheme('auto'));

    document.addEventListener('click', (event) => {
      const button = event.target.closest('[data-theme-value]');
      if (!button) {
        return;
      }

      const value = button.dataset.themeValue;
      if (!value) {
        return;
      }

      setStoredTheme(value);
      applyTheme(value);
    });

    if (prefersDark) {
      const handleColorSchemeChange = () => {
        const storedTheme = getStoredTheme();
        if (storedTheme !== 'light' && storedTheme !== 'dark') {
          applyTheme(resolveTheme('auto'));
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

  const init = () => {
    initThemeToggle();
    initShareButtons();
    initOffcanvasCleanup();
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
