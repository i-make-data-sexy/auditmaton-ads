// ========================================================================
//   Platform filter (Ads edition)
//
//   The active-platform selector on the dashboard. A single dropdown that
//   mirrors the Topic filter: click the trigger to open the grouped list,
//   click an option to navigate to that platform, click outside to close.
//   Options are plain links (navigation), so there is no multi-select state
//   to manage here, only open/close.
// ========================================================================

document.addEventListener('DOMContentLoaded', function () {
    var filter = document.getElementById('platform-filter');
    if (!filter) return;

    var trigger = document.getElementById('platform-filter-trigger');
    if (!trigger) return;

    // Toggle the menu open/closed. stopPropagation so the document-level
    // close handler below does not immediately re-close it.
    trigger.addEventListener('click', function (e) {
        e.stopPropagation();
        var open = filter.classList.toggle('open');
        trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    // Close when clicking anywhere outside the dropdown.
    document.addEventListener('click', function (e) {
        if (!filter.contains(e.target)) {
            filter.classList.remove('open');
            trigger.setAttribute('aria-expanded', 'false');
        }
    });
});
