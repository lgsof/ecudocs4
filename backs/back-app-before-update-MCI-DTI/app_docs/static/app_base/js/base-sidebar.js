/* Utility functions for sidebar menu */
(function () {
  // IDs of collapsible sections
  var SECTION_IDS = ['cartaporte','manifiesto','declaracion','entidades','usuario','administracion'];

  function setShow(el, show) {
    if (!el) return;
    // Use Bootstrap API if present, otherwise fallback to classList
    var isBs5 = !!window.bootstrap; // rough check: BS5 exposes window.bootstrap
    if (isBs5) {
      var collapse = bootstrap.Collapse.getInstance(el) || new bootstrap.Collapse(el, { toggle: false });
      if (show) collapse.show(); else collapse.hide();
    } else {
      if (show) el.classList.add('show'); else el.classList.remove('show');
    }
  }

  function persistOn(el, key) {
    var isBs5 = !!window.bootstrap;
    if (isBs5) {
      el.addEventListener('shown.bs.collapse', function () { localStorage.setItem(key, '1'); });
      el.addEventListener('hidden.bs.collapse', function () { localStorage.setItem(key, '0'); });
    } else if (window.jQuery) {
      jQuery(el).on('shown.bs.collapse', function () { localStorage.setItem(key, '1'); });
      jQuery(el).on('hidden.bs.collapse', function () { localStorage.setItem(key, '0'); });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    SECTION_IDS.forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      var key = 'sb-open-' + id;

      // Restore previous state (default: keep server-rendered state)
      var saved = localStorage.getItem(key);
      if (saved === '1') setShow(el, true);
      if (saved === '0') setShow(el, false);

      // Persist on toggle
      persistOn(el, key);
    });
  });
})();

