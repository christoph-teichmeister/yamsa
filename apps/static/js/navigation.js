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
    const resolved = resolveTheme(theme);
    if (resolved === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
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

  // --- Custom Drawer ---

  const openDrawer = (el) => {
    el.classList.add('show');
    el.removeAttribute('aria-hidden');
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('role', 'dialog');

    let backdrop = document.getElementById('yamsa-offcanvas-backdrop');
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.className = 'ym-drawer-backdrop';
      backdrop.id = 'yamsa-offcanvas-backdrop';
      backdrop.addEventListener('click', () => closeDrawer(el));
      document.body.appendChild(backdrop);
    }

    document.body.style.overflow = 'hidden';
    el.dispatchEvent(new CustomEvent('ym:drawer:shown', { bubbles: true }));
  };

  const closeDrawer = (el) => {
    el.classList.remove('show');
    el.setAttribute('aria-hidden', 'true');
    el.removeAttribute('aria-modal');

    const backdrop = document.getElementById('yamsa-offcanvas-backdrop');
    if (backdrop) {
      backdrop.remove();
    }

    document.body.style.overflow = '';
    el.dispatchEvent(new CustomEvent('ym:drawer:hidden', { bubbles: true }));
  };

  const initDrawer = () => {
    document.addEventListener('click', (event) => {
      const trigger = event.target.closest('[data-ym-toggle="drawer"]');
      if (!trigger) {
        return;
      }
      const targetId = trigger.getAttribute('data-ym-target');
      if (!targetId) {
        return;
      }
      const drawer = document.querySelector(targetId);
      if (!drawer) {
        return;
      }
      openDrawer(drawer);
    });

    document.addEventListener('click', (event) => {
      const trigger = event.target.closest('[data-ym-dismiss="drawer"]');
      if (!trigger) {
        return;
      }
      const targetId = trigger.getAttribute('data-ym-target');
      const drawer = targetId
        ? document.querySelector(targetId)
        : trigger.closest('.ym-drawer');
      if (drawer) {
        closeDrawer(drawer);
      }
    });

    document.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape') {
        return;
      }
      const openDrawerEl = document.querySelector('.ym-drawer.show');
      if (openDrawerEl) {
        closeDrawer(openDrawerEl);
      }
    });
  };

  // --- Custom Modal ---

  const openModal = (el) => {
    el.classList.add('show');
    document.body.style.overflow = 'hidden';
    el.dispatchEvent(new CustomEvent('ym:dialog:shown', { bubbles: true }));
  };

  const closeModal = (el) => {
    el.classList.remove('show');
    document.body.style.overflow = '';
    el.dispatchEvent(new CustomEvent('ym:dialog:hidden', { bubbles: true }));
  };

  const initModal = () => {
    document.addEventListener('click', (event) => {
      const trigger = event.target.closest('[data-ym-toggle="dialog"]');
      if (!trigger) {
        return;
      }
      const targetId = trigger.getAttribute('data-ym-target');
      if (!targetId) {
        return;
      }
      const modal = document.querySelector(targetId);
      if (!modal) {
        return;
      }
      openModal(modal);
    });

    document.addEventListener('click', (event) => {
      const trigger = event.target.closest('[data-ym-dismiss="dialog"]');
      if (!trigger) {
        return;
      }
      const modal = trigger.closest('.ym-dialog');
      if (modal) {
        closeModal(modal);
      }
    });

    document.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape') {
        return;
      }
      const openModalEl = document.querySelector('.ym-dialog.show');
      if (openModalEl) {
        closeModal(openModalEl);
      }
    });
  };

  // --- Collapse ---

  const initCollapse = () => {
    document.addEventListener('click', (event) => {
      const trigger = event.target.closest('[data-ym-toggle="collapse"]');
      if (!trigger) return;
      const targetId = trigger.getAttribute('data-ym-target');
      if (!targetId) return;
      const target = document.querySelector(targetId);
      if (!target) return;
      target.classList.toggle('hidden');
      // Update aria-expanded
      const isExpanded = !target.classList.contains('hidden');
      trigger.setAttribute('aria-expanded', isExpanded);
    });
  };

  // Expose for inline scripts that need to close modals
  window.yamsa = window.yamsa || {};
  window.yamsa.closeModal = closeModal;

  // ---

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
  };

  const init = () => {
    initThemeToggle();
    initShareButtons();
    initDrawer();
    initModal();
    initCollapse();
    initRoomNavigationScrollReset();
    refreshDynamicElements();
    document.addEventListener('click', handleNavigationClick);

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
