// ========================================================================
//   Platform filter (Ads edition)
//
//   The dashboard dropdowns: the active-platform selector and the Side
//   filter beside it. Each is a .platform-filter that mirrors the Topic
//   filter: click the trigger to open the list, click an option to
//   navigate, click outside to close. Options are plain links (navigation),
//   so there is no multi-select state to manage, only open/close. One
//   handler drives every .platform-filter on the page.
// ========================================================================

document.addEventListener('DOMContentLoaded', function () {
    var filters = document.querySelectorAll('.platform-filter');
    if (!filters.length) return;

    filters.forEach(function (filter) {
        var trigger = filter.querySelector('.platform-filter-trigger');
        if (!trigger) return;

        // Toggle this menu open/closed. stopPropagation so the document
        // close handler below does not immediately re-close it.
        trigger.addEventListener('click', function (e) {
            e.stopPropagation();
            var open = filter.classList.toggle('open');
            trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
    });

    // Close every dropdown when clicking outside it.
    document.addEventListener('click', function (e) {
        filters.forEach(function (filter) {
            if (!filter.contains(e.target)) {
                filter.classList.remove('open');
                var trigger = filter.querySelector('.platform-filter-trigger');
                if (trigger) trigger.setAttribute('aria-expanded', 'false');
            }
        });
    });
});
