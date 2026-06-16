// ========================================================================
//   Depth filter (Ads edition)
//
//   Mirrors the Worth it filter's behavior:
//   - toggle pills to filter the subcategory list (deselected = grayed),
//   - print the active tier's icon in the trigger as a "filtered view" cue,
//   - reflect the selection in a shareable ?depth= URL parameter, and
//     preserve it across subcategory navigation,
//   - read ?depth= on load so a shared link opens the filtered view.
//   The last active pill cannot be deselected, so the rail never empties.
// ========================================================================

document.addEventListener('DOMContentLoaded', function () {
    var filter = document.getElementById('depth-filter');
    if (!filter) return;

    var trigger = document.getElementById('depth-filter-trigger');
    var iconSlot = filter.querySelector('.depth-filter-trigger-icons');
    var pills = Array.prototype.slice.call(filter.querySelectorAll('.depth-pill'));
    var rail = filter.closest('.category-rail') || document;
    if (!trigger || !pills.length) return;

    var PARAM = 'depth';
    var ICONS = {
        core:     { icon: 'fa-shield-halved', cls: 'depth-trigger-icon-core' },
        advanced: { icon: 'fa-rocket',        cls: 'depth-trigger-icon-advanced' }
    };

    function activeTiers() {
        return pills
            .filter(function (p) { return p.classList.contains('active'); })
            .map(function (p) { return p.getAttribute('data-tier'); });
    }

    // Write the active tiers onto a URL's ?depth= param (or drop it when all
    // tiers are selected, i.e. the view is unfiltered).
    function setParam(url, active) {
        if (active.length >= pills.length) url.searchParams.delete(PARAM);
        else url.searchParams.set(PARAM, active.join(','));
        return url;
    }

    // Trigger cue: tint the trigger and print the icon of each still-active
    // tier when the view is filtered; clear it when unfiltered.
    function paintTrigger(active) {
        var filtered = active.length < pills.length;
        trigger.classList.toggle('filtered', filtered);
        if (!iconSlot) return;
        iconSlot.innerHTML = '';
        if (!filtered) return;
        pills.forEach(function (p) {
            if (!p.classList.contains('active')) return;
            var spec = ICONS[p.getAttribute('data-tier')];
            if (!spec) return;
            var i = document.createElement('i');
            i.className = 'fa-solid ' + spec.icon + ' depth-trigger-icon ' + spec.cls;
            iconSlot.appendChild(i);
        });
    }

    function apply(writeUrl) {
        var active = activeTiers();

        rail.querySelectorAll('.subcategory-btn').forEach(function (btn) {
            var tier = btn.getAttribute('data-tier');
            var show = !tier || active.indexOf(tier) !== -1;
            btn.classList.toggle('depth-filtered-out', !show);

            // Preserve the filter across subcategory navigation by carrying
            // the param on each subcategory link.
            var href = btn.getAttribute('href');
            if (href) {
                var u = setParam(new URL(href, window.location.origin), active);
                btn.setAttribute('href', u.pathname + u.search);
            }
        });

        paintTrigger(active);

        if (writeUrl) {
            history.replaceState(null, '', setParam(new URL(window.location.href), active));
        }
    }

    // Collapsible trigger.
    trigger.addEventListener('click', function () {
        var open = filter.classList.toggle('open');
        trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    // Pills toggle their tier; never allow an empty selection.
    pills.forEach(function (pill) {
        pill.addEventListener('click', function () {
            pill.classList.toggle('active');
            if (!pills.some(function (p) { return p.classList.contains('active'); })) {
                pill.classList.add('active');
            }
            pill.setAttribute(
                'aria-pressed',
                pill.classList.contains('active') ? 'true' : 'false'
            );
            apply(true);
        });
    });

    // On load, apply any ?depth= parameter so a shared link opens filtered.
    var raw = new URL(window.location.href).searchParams.get(PARAM);
    if (raw) {
        var wanted = raw.split(',').map(function (s) {
            return s.trim().toLowerCase();
        }).filter(Boolean);
        pills.forEach(function (p) {
            var on = wanted.indexOf(p.getAttribute('data-tier')) !== -1;
            p.classList.toggle('active', on);
            p.setAttribute('aria-pressed', on ? 'true' : 'false');
        });
        if (!pills.some(function (p) { return p.classList.contains('active'); })) {
            pills.forEach(function (p) {
                p.classList.add('active');
                p.setAttribute('aria-pressed', 'true');
            });
        }
    }

    apply(false);
});
