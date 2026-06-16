// ========================================================================
//   Theme filter (Ads edition)
//
//   Multi-select dropdown that filters the check cards within a subcategory
//   by their theme_tags. Sibling of the Depth filter (tier-filter.js), with
//   two differences:
//   - it operates on check cards (data-themes) rather than subcategory
//     buttons (data-tier), and
//   - selection is multi-select with OR semantics: a card shows when it
//     carries any still-selected theme.
//   Only the themes present on the current subcategory's checks are rendered
//   as options, so a selection never returns an empty result. The last active
//   theme cannot be deselected, so the menu never empties. The selection is
//   reflected in a shareable ?themes= URL parameter.
// ========================================================================

document.addEventListener('DOMContentLoaded', function () {
    var filters = Array.prototype.slice.call(document.querySelectorAll('.theme-filter'));
    if (!filters.length) return;

    var PARAM = 'themes';

    function setup(filter) {
        var trigger = filter.querySelector('.theme-filter-trigger');
        var countSlot = filter.querySelector('.theme-filter-trigger-count');
        var pills = Array.prototype.slice.call(filter.querySelectorAll('.theme-pill'));
        var container = filter.closest('.subcategory-content') || document;
        var cards = Array.prototype.slice.call(container.querySelectorAll('.check-card'));
        if (!trigger || !pills.length) return;

        function activeThemes() {
            return pills
                .filter(function (p) { return p.classList.contains('active'); })
                .map(function (p) { return p.getAttribute('data-theme'); });
        }

        function apply(writeUrl) {
            var active = activeThemes();
            var filtered = active.length < pills.length;

            cards.forEach(function (card) {
                var raw = (card.getAttribute('data-themes') || '').trim();
                var themes = raw ? raw.split(/\s+/) : [];
                // A card with no themes always shows; it cannot be filtered by
                // theme. Otherwise show it when it carries an active theme.
                var show = !themes.length || themes.some(function (t) {
                    return active.indexOf(t) !== -1;
                });
                card.classList.toggle('theme-filtered-out', !show);
            });

            // Trigger cue: tint it and print the active count when filtered.
            trigger.classList.toggle('filtered', filtered);
            if (countSlot) countSlot.textContent = filtered ? String(active.length) : '';

            if (writeUrl) {
                var url = new URL(window.location.href);
                if (filtered) url.searchParams.set(PARAM, active.join(','));
                else url.searchParams.delete(PARAM);
                history.replaceState(null, '', url.pathname + url.search);
            }
        }

        // Collapsible trigger.
        trigger.addEventListener('click', function (e) {
            e.stopPropagation();
            var open = filter.classList.toggle('open');
            trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
        });

        // Pills toggle their theme; never allow an empty selection.
        pills.forEach(function (pill) {
            pill.addEventListener('click', function (e) {
                e.stopPropagation();
                pill.classList.toggle('active');
                if (!pills.some(function (p) { return p.classList.contains('active'); })) {
                    pill.classList.add('active');
                }
                pill.setAttribute(
                    'aria-selected',
                    pill.classList.contains('active') ? 'true' : 'false'
                );
                apply(true);
            });
        });

        // On load, apply any ?themes= parameter so a shared link opens filtered.
        var raw = new URL(window.location.href).searchParams.get(PARAM);
        if (raw) {
            var wanted = raw.split(',').map(function (s) {
                return s.trim().toLowerCase();
            }).filter(Boolean);
            pills.forEach(function (p) {
                var on = wanted.indexOf(p.getAttribute('data-theme')) !== -1;
                p.classList.toggle('active', on);
                p.setAttribute('aria-selected', on ? 'true' : 'false');
            });
            if (!pills.some(function (p) { return p.classList.contains('active'); })) {
                pills.forEach(function (p) {
                    p.classList.add('active');
                    p.setAttribute('aria-selected', 'true');
                });
            }
        }

        apply(false);
    }

    filters.forEach(setup);

    // A click anywhere outside an open menu closes it.
    document.addEventListener('click', function (e) {
        filters.forEach(function (filter) {
            if (!filter.contains(e.target)) {
                filter.classList.remove('open');
                var t = filter.querySelector('.theme-filter-trigger');
                if (t) t.setAttribute('aria-expanded', 'false');
            }
        });
    });
});
