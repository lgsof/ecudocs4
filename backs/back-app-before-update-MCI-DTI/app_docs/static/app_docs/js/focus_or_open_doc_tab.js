/*
 * Open a document in a new tab or focus
 * on this tab if already opened
 */

function focusOrOpen (winName, url) {
    try {
      const w = window.open ('', winName);  // Reuse if it exists
      const mustNavigate = !w || w.closed || w.location.href === 'about:blank';
      if (mustNavigate) {
        window.open (url, winName);        // Open/navigate first time
      } else {
        w.focus();                         // Just focus, keeps unsaved state
      }
    } catch (e) {
      window.open(url, winName);           // Fallback: open/navigate
    }
    return false; // prevent default anchor navigation
}

// Delegate clicks from links with class="open-doc"
document.addEventListener ('click', function (e) {
    const a = e.target.closest('a.open-doc');
    if (!a) return;
    e.preventDefault();
    focusOrOpen(a.dataset.win, a.href);
})
