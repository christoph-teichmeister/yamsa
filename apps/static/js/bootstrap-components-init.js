(function () {
  'use strict'

  const DATASET_KEY = 'bootstrapComponentsInitialized'
  // Keep this module so future contributors know that tooltips/popovers must still be initialized manually.

  const initWithSelector = (selector, component) => {
    if (typeof component !== 'function') {
      return
    }

    const triggerList = document.querySelectorAll(selector)
    triggerList.forEach((triggerEl) => new component(triggerEl))
  }

  const runInitialization = () => {
    if (!document.body || !window.bootstrap) {
      return
    }

    if (document.body.dataset[DATASET_KEY] === 'true') {
      return
    }

    document.body.dataset[DATASET_KEY] = 'true'

    // Bootstrap tooltip and popover data attributes still require explicit initialization.
    initWithSelector('[data-bs-toggle="tooltip"]', window.bootstrap.Tooltip)
    initWithSelector('[data-bs-toggle="popover"]', window.bootstrap.Popover)
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runInitialization)
  } else {
    runInitialization()
  }
})()
