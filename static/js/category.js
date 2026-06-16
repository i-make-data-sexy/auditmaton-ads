/* category.js
   Handles subcategory switching on the category browser page (Level 2).
   Toggles active panels and buttons, updates the URL permalink via
   history.pushState for bookmarkability without page reload.
   Also handles check status persistence via localStorage: done/skip
   cards collapse to a thin bar, and hover reveals status change options. */


/* ========================================================================
   Section 1: Subcategory Switching
   ======================================================================== */

$(document).ready(function() {

    /* Handle subcategory button clicks */
    $(".subcategory-btn").on("click", function(e) {
        e.preventDefault();

        var slug = $(this).data("subcategory");
        var href = $(this).attr("href");

        var name = $(this).find(".subcategory-btn-name").text();

        /* Update active button */
        $(".subcategory-btn").removeClass("active");
        $(this).addClass("active");

        /* Update active panel */
        $(".subcategory-content").removeClass("active");
        $(".subcategory-content[data-subcategory='" + slug + "']").addClass("active");

        /* Reset to Overview tab for the newly selected subcategory */
        var newPanel = $(".subcategory-content[data-subcategory='" + slug + "']");
        newPanel.find(".subcat-tab").removeClass("active");
        newPanel.find(".subcat-tab-panel").removeClass("active");
        newPanel.find(".subcat-tab[data-tab^='overview-']").addClass("active");
        newPanel.find("[id^='panel-overview-']").addClass("active");

        /* Update subcategory title */
        $("#subcategory-title").text(name);

        /* Update URL without page reload — preserve the current query
           string so the worth-it filter survives subcategory switches
           and remains in any URL the user shares. The tinted trigger
           + "Showing X of Y" tooltip make the active filter obvious,
           so there's no risk of a user forgetting it's on. */
        history.pushState(
            {subcategory: slug, tab: "overview", name: name},
            "",
            href + window.location.search
        );
    });
});


/* ========================================================================
   Section 2: Subcategory Tab Switching (Overview / Audit Checks)
   ======================================================================== */

/**
 * Returns the tab slug ("overview" or "audit-checks") for a given tab button.
 */
function getTabSlug(tabButton) {
    var dataTab = tabButton.data("tab");
    if (dataTab && dataTab.indexOf("checks-") === 0) {
        return "audit-checks";
    }
    return "overview";
}

/**
 * Builds the permalink URL for the current subcategory and tab.
 * Handles APPLICATION_ROOT prefix (e.g., /tools/auditmaton/site-audit/dashboard/category/subcat/tab/).
 */
function buildTabPermalink(subcategorySlug, tabSlug) {
    var path = window.location.pathname;
    var parts = path.split("/").filter(Boolean);

    /* Find the "dashboard" segment to anchor our path construction */
    var dashboardIndex = parts.indexOf("dashboard");
    if (dashboardIndex === -1) {
        return path;
    }

    /* Keep everything up to "dashboard" + platform + category, then append subcat + tab */
    var baseParts = parts.slice(0, dashboardIndex + 3);
    var permalink = "/" + baseParts.join("/") + "/" + subcategorySlug + "/" + tabSlug + "/";

    /* Preserve any active query string (worth-it filter) so subcategory
       + tab switches don't strip the filter from the URL. */
    return permalink + window.location.search;
}

$(document).on("click", ".subcat-tab", function() {
    var tab = $(this);
    var tabBar = tab.closest(".subcat-tab-bar");
    var container = tabBar.closest(".subcategory-content");

    /* Deactivate all tabs and panels in this subcategory */
    tabBar.find(".subcat-tab").removeClass("active");
    container.find(".subcat-tab-panel").removeClass("active");

    /* Activate clicked tab and matching panel */
    tab.addClass("active");
    var panelId = "panel-" + tab.data("tab");
    container.find("#" + panelId).addClass("active");

    /* Update URL to reflect the active tab */
    var subcatSlug = container.data("subcategory");
    var tabSlug = getTabSlug(tab);
    var name = $("#subcategory-title").text();
    var permalink = buildTabPermalink(subcatSlug, tabSlug);
    history.pushState({subcategory: subcatSlug, tab: tabSlug, name: name}, "", permalink);
});


/* ========================================================================
   Section 3: Browser Back/Forward Support (was Section 2)
   ======================================================================== */

/* Handle browser back/forward navigation */
window.addEventListener("popstate", function(e) {

    /* Resync the worth-it pills to whatever the URL now claims, so
       the rail's filtered state matches the address bar after a
       back/forward hop. Skip save: this is navigation, not a user
       choice, so don't overwrite their persisted preference. */
    var urlValues = readWorthItFilterFromUrl();
    if (urlValues !== null && $(".worth-it-pill").length) {
        applyValuesToWorthItPills(urlValues);
        applyWorthItFilter({ skipSave: true });
    }

    if (e.state && e.state.subcategory) {
        var slug = e.state.subcategory;
        var tabSlug = e.state.tab || "overview";

        /* Update active button */
        $(".subcategory-btn").removeClass("active");
        $(".subcategory-btn[data-subcategory='" + slug + "']").addClass("active");

        /* Update active panel */
        $(".subcategory-content").removeClass("active");
        var panel = $(".subcategory-content[data-subcategory='" + slug + "']");
        panel.addClass("active");

        /* Restore the correct tab */
        panel.find(".subcat-tab").removeClass("active");
        panel.find(".subcat-tab-panel").removeClass("active");

        if (tabSlug === "audit-checks") {
            panel.find(".subcat-tab[data-tab^='checks-']").addClass("active");
            panel.find("[id^='panel-checks-']").addClass("active");
        } else {
            panel.find(".subcat-tab[data-tab^='overview-']").addClass("active");
            panel.find("[id^='panel-overview-']").addClass("active");
        }

        /* Update subcategory title */
        if (e.state.name) {
            $("#subcategory-title").text(e.state.name);
        }
    }
});


/* ========================================================================
   Section 4: Check Status (localStorage Persistence)
   ======================================================================== */

/**
 * Reads all check statuses from localStorage.
 * Returns an object keyed by category, each containing check ID to status mappings.
 */
function getCheckStatuses() {
    var raw = localStorage.getItem("audit_check_status");
    if (!raw) {
        return {};
    }

    try {
        return JSON.parse(raw);
    } catch (e) {
        return {};
    }
}

/**
 * Saves the full check status object to localStorage.
 */
function saveCheckStatuses(statuses) {
    localStorage.setItem("audit_check_status", JSON.stringify(statuses));
}

/**
 * Applies a status to a check card (adds/removes CSS classes, updates labels).
 * Handles the visual collapse for done/skip and expansion for todo.
 */
function applyCardStatus(card, status) {

    /* Remove any existing status classes */
    card.removeClass("status-done status-skip status-in_progress");

    if (status === "in_progress") {

        /* In-progress: blue border, card stays full size */
        card.addClass("status-in_progress");

    } else if (status === "done" || status === "skip") {

        /* Add the appropriate collapsed class */
        card.addClass("status-" + status);

        /* Set the collapsed label text */
        var labelText = status === "done" ? "DONE" : "SKIPPED";
        card.find(".check-collapsed-label").text(labelText);

        /* Hide the button matching the current status, show the other two */
        card.find(".check-collapsed-btns .status-btn").show();
        card.find(".check-collapsed-btns .status-btn[data-status='" + status + "']").hide();
    }
}

/**
 * Restores saved check states on page load.
 * Reads localStorage and collapses cards that were marked done or skip.
 */
function restoreCheckStates() {
    var statuses = getCheckStatuses();

    $(".check-card").each(function() {
        var card = $(this);
        var checkId = card.data("check-id");
        var category = card.data("category");

        if (statuses[category] && statuses[category][checkId]) {
            var savedStatus = statuses[category][checkId];

            /* Only apply non-default statuses */
            if (savedStatus === "done" || savedStatus === "skip" || savedStatus === "in_progress") {
                applyCardStatus(card, savedStatus);
            }
        }
    });

    /* Reorder cards after restoring states */
    reorderCards();
}


/**
 * Reorders check cards within each container by status.
 * Order: in-progress first, then todo (not started), then done, then skipped last.
 * Handles two layout modes: tabbed (panel-checks-*) and standard
 * (subcategory-content).
 */
function reorderCards() {
    var statusOrder = {
        "in_progress": 0,
        "todo": 1,
        "done": 2,
        "skip": 3
    };

    /* Helper: sort and re-append cards within a container */
    function sortContainer(container) {
        var cards = container.find(".check-card").toArray();

        cards.sort(function(a, b) {
            var aStatus = getCardStatus($(a));
            var bStatus = getCardStatus($(b));
            return statusOrder[aStatus] - statusOrder[bStatus];
        });

        $.each(cards, function(i, card) {
            container.append(card);
        });
    }

    /* Standard / tabbed mode: cards inside subcategory panels */
    $(".subcategory-content").each(function() {
        var subcatContent = $(this);

        /* Cards may be inside a tab panel or directly in the subcategory-content */
        var checksPanel = subcatContent.find("[id^='panel-checks-']");
        var container = checksPanel.length ? checksPanel : subcatContent;

        sortContainer(container);
    });
}


/**
 * Returns the current status of a check card based on its CSS classes.
 */
function getCardStatus(card) {
    if (card.hasClass("status-done")) {
        return "done";
    }
    if (card.hasClass("status-skip")) {
        return "skip";
    }
    if (card.hasClass("status-in_progress")) {
        return "in_progress";
    }
    return "todo";
}

$(document).ready(function() {

    /* Restore saved check states */
    restoreCheckStates();

    /* Handle status button clicks */
    $(document).on("click", ".status-btn", function(e) {
        e.stopPropagation();
        var btn = $(this);
        var card = btn.closest(".check-card");
        var checkId = card.data("check-id");
        var category = card.data("category");
        var status = btn.data("status");

        /* Apply the visual state change */
        applyCardStatus(card, status);

        /* Save to localStorage */
        var statuses = getCheckStatuses();
        if (!statuses[category]) {
            statuses[category] = {};
        }
        statuses[category][checkId] = status;
        saveCheckStatuses(statuses);

        /* Reorder cards after status change */
        reorderCards();
    });

    /* Mark check as in-progress when 'Get Started' is clicked */
    $(document).on("click", ".check-link", function() {
        var card = $(this).closest(".check-card");
        var checkId = card.data("check-id");
        var category = card.data("category");

        /* Only mark as in-progress if currently todo (not started) */
        var currentStatus = getCardStatus(card);
        if (currentStatus === "todo") {
            applyCardStatus(card, "in_progress");

            /* Save to localStorage */
            var statuses = getCheckStatuses();
            if (!statuses[category]) {
                statuses[category] = {};
            }
            statuses[category][checkId] = "in_progress";
            saveCheckStatuses(statuses);
        }
    });
});


/* ========================================================================
   Section 5: Subcategory Skip (Right-Click Context Menu)
   ======================================================================== */

/* Track which subcategory button was right-clicked */
var contextTarget = null;

/**
 * Reads skipped subcategory slugs from localStorage.
 * Returns an object keyed by category, each containing an array of slugs.
 */
function getSkippedSubcats() {
    var raw = localStorage.getItem("audit_subcat_skip");
    if (!raw) {
        return {};
    }

    try {
        return JSON.parse(raw);
    } catch (e) {
        return {};
    }
}

/**
 * Saves the full skipped subcategories object to localStorage.
 */
function saveSkippedSubcats(skipped) {
    localStorage.setItem("audit_subcat_skip", JSON.stringify(skipped));
}

/**
 * Returns the current category key from the page URL.
 * Extracts it from the path: /dashboard/<platform>/<category>/...
 */
function getCategoryKey() {
    var path = window.location.pathname;
    var parts = path.split("/").filter(Boolean);

    /* Path contains ["dashboard", "<platform>", "<category>", ...] (possibly with an APPLICATION_ROOT prefix) */
    var dashboardIndex = parts.indexOf("dashboard");
    if (dashboardIndex !== -1 && parts.length > dashboardIndex + 2) {
        return parts[dashboardIndex + 2];
    }
    return null;
}

/**
 * Applies or removes the skipped class on a subcategory button.
 */
function applySubcatSkip(btn, isSkipped) {
    if (isSkipped) {
        btn.addClass("skipped");
    } else {
        btn.removeClass("skipped");
    }
}

/**
 * Reorders subcategory buttons in the rail: unskipped first (original order),
 * then skipped at the bottom (original order preserved within skipped group).
 */
function reorderSubcats() {
    var rail = $(".category-rail");
    var buttons = rail.find(".subcategory-btn").toArray();

    /* Sort helper: compare by original server-rendered index */
    function byOriginalIndex(a, b) {
        return parseInt($(a).attr("data-original-index"), 10)
             - parseInt($(b).attr("data-original-index"), 10);
    }

    /* Separate into unskipped and skipped, then sort each by original position */
    var unskipped = buttons.filter(function(btn) {
        return !$(btn).hasClass("skipped");
    }).sort(byOriginalIndex);

    var skipped = buttons.filter(function(btn) {
        return $(btn).hasClass("skipped");
    }).sort(byOriginalIndex);

    /* Re-append: unskipped first, then skipped */
    $.each(unskipped, function(i, btn) {
        rail.append(btn);
    });
    $.each(skipped, function(i, btn) {
        rail.append(btn);
    });
}

/**
 * Stamps each subcategory button with its original DOM index (data-original-index)
 * so reorderSubcats can restore unskipped items to their server-rendered position.
 * Must be called once before any reordering occurs.
 */
function stampOriginalOrder() {
    $(".category-rail .subcategory-btn").each(function(i) {
        $(this).attr("data-original-index", i);
    });
}

/**
 * Restores skipped subcategory states on page load from localStorage.
 */
function restoreSubcatSkips() {

    /* Capture server-rendered order before any reordering */
    stampOriginalOrder();

    var categoryKey = getCategoryKey();
    if (!categoryKey) {
        return;
    }

    var skipped = getSkippedSubcats();
    var slugs = skipped[categoryKey] || [];

    if (slugs.length === 0) {
        return;
    }

    $(".subcategory-btn").each(function() {
        var btn = $(this);
        var slug = btn.data("subcategory");

        if (slugs.indexOf(slug) !== -1) {
            applySubcatSkip(btn, true);
        }
    });

    reorderSubcats();
}


$(document).ready(function() {

    /* Restore skipped subcategory states */
    restoreSubcatSkips();

    var menu = $("#subcat-context-menu");
    var skipBtn = $("#subcat-skip-btn");

    /* Show context menu on right-click of subcategory buttons */
    $(document).on("contextmenu", ".subcategory-btn", function(e) {
        e.preventDefault();
        contextTarget = $(this);

        /* Set button text based on current skip state */
        var isSkipped = contextTarget.hasClass("skipped");
        skipBtn.text(isSkipped ? "Unskip" : "Skip");

        /* Position menu at cursor */
        menu.css({
            top: e.clientY + "px",
            left: e.clientX + "px"
        });
        menu.addClass("visible");
    });

    /* Handle skip/unskip button click */
    skipBtn.on("click", function() {
        if (!contextTarget) {
            return;
        }

        var categoryKey = getCategoryKey();
        var slug = contextTarget.data("subcategory");
        var isSkipped = contextTarget.hasClass("skipped");

        /* Toggle the skip state */
        applySubcatSkip(contextTarget, !isSkipped);

        /* Update localStorage */
        var skipped = getSkippedSubcats();
        if (!skipped[categoryKey]) {
            skipped[categoryKey] = [];
        }

        if (isSkipped) {

            /* Remove from skipped list */
            skipped[categoryKey] = skipped[categoryKey].filter(function(s) {
                return s !== slug;
            });
        } else {

            /* Add to skipped list */
            if (skipped[categoryKey].indexOf(slug) === -1) {
                skipped[categoryKey].push(slug);
            }
        }

        saveSkippedSubcats(skipped);

        /* Reorder the rail */
        reorderSubcats();

        /* Hide the menu */
        menu.removeClass("visible");
        contextTarget = null;
    });

    /* Hide context menu on click anywhere else */
    $(document).on("click", function() {
        menu.removeClass("visible");
        contextTarget = null;
    });

    /* Hide context menu on Escape key */
    $(document).on("keydown", function(e) {
        if (e.key === "Escape") {
            menu.removeClass("visible");
            contextTarget = null;
        }
    });
});


// ========================================================================
//   Worth-it Filter (multi-select pills above the subcategory rail)
// ========================================================================

// Canonical worth-it pill values (matches data-worth-it on the rail
// buttons + pills). URL representations are the lowercase form.
var WORTH_IT_PILL_VALUES = ["Yes", "No", "Depends"];


function readWorthItFilterFromUrl() {
    /**
     * Parses the ?worth-it=... query parameter (comma-joined, case-
     * insensitive) into the canonical Title-case pill values. Returns
     * null when the param is absent so callers can fall back to saved
     * preferences. Returns [] when the param is present but empty.
     *
     * Returns:
     *     Array<string>|null: canonical pill values, or null if the
     *     param is absent from the URL.
     */

    var params = new URLSearchParams(window.location.search);
    if (!params.has("worth-it")) {
        return null;
    }
    var raw = params.get("worth-it") || "";
    if (!raw) {
        return [];
    }
    var requested = raw.split(",").map(function(v) {
        return v.trim().toLowerCase();
    });
    var matched = [];
    for (var i = 0; i < WORTH_IT_PILL_VALUES.length; i++) {
        var canonical = WORTH_IT_PILL_VALUES[i];
        if (requested.indexOf(canonical.toLowerCase()) !== -1) {
            matched.push(canonical);
        }
    }
    return matched;
}


function updateUrlForWorthItFilter(activeValues, totalPills) {
    /**
     * Reflects the current pill selection in the URL via replaceState
     * so filter toggles don't pollute history but the address bar
     * still shows a shareable URL. Strips the param entirely when all
     * pills are active — that's the canonical no-filter state, so the
     * URL stays clean for the default view.
     *
     * Args:
     *     activeValues (Array<string>): canonical Title-case worth-it
     *         values whose pills are currently active.
     *     totalPills (number): total pill count, used to detect the
     *         all-active "default" state that should produce a clean URL.
     */

    // URLSearchParams.set would percent-encode the comma as %2C, which
    // junks up an otherwise clean shareable URL. Comma is a valid
    // sub-delim in the query component per RFC 3986, so we drop the
    // worth-it key out of URLSearchParams and re-append it as a raw
    // string with a literal comma between values. Any OTHER query
    // params still go through URLSearchParams.toString() so their
    // encoding rules stay correct.
    var url = new URL(window.location.href);
    url.searchParams.delete("worth-it");
    var baseSearch = url.searchParams.toString();

    var addition = "";
    if (activeValues.length !== totalPills) {
        var lowered = activeValues.map(function(v) { return v.toLowerCase(); });
        addition = "worth-it=" + lowered.join(",");
    }

    var combinedSearch = [baseSearch, addition].filter(Boolean).join("&");
    var newUrl = url.pathname + (combinedSearch ? "?" + combinedSearch : "") + url.hash;
    history.replaceState(history.state, "", newUrl);
}


function applyValuesToWorthItPills(activeValues) {
    /**
     * Sets each pill's active/aria-pressed state to match the supplied
     * canonical value list. Used both when restoring from URL and when
     * reconciling with the server's stored value.
     *
     * Args:
     *     activeValues (Array<string>): canonical Title-case worth-it
     *         values that should be marked active.
     */

    $(".worth-it-pill").each(function() {
        var $pill = $(this);
        var value = $pill.attr("data-worth-it");
        var nowActive = activeValues.indexOf(value) !== -1;
        $pill.toggleClass("active", nowActive);
        $pill.attr("aria-pressed", nowActive ? "true" : "false");
    });
}


function activateSubcategory(slug) {
    /**
     * Switches the rail's active button + the visible content panel to
     * the given subcategory slug, and pushes the new URL onto the
     * history stack so back/forward still works. Mirrors the existing
     * popstate handler's logic so both code paths stay in sync.
     *
     * Args:
     *     slug (str): The subcategory slug to activate (matches
     *         data-subcategory on the rail button and content panel).
     */

    var $btn = $(".subcategory-btn[data-subcategory='" + slug + "']");
    if (!$btn.length) {
        return;
    }

    $(".subcategory-btn").removeClass("active");
    $btn.addClass("active");

    $(".subcategory-content").removeClass("active");
    var $panel = $(".subcategory-content[data-subcategory='" + slug + "']");
    $panel.addClass("active");

    // Reset to the Overview tab on switch
    $panel.find(".subcat-tab").removeClass("active");
    $panel.find(".subcat-tab-panel").removeClass("active");
    $panel.find(".subcat-tab[data-tab^='overview-']").addClass("active");
    $panel.find("[id^='panel-overview-']").addClass("active");

    // Update the visible H2 title
    var name = $btn.find(".subcategory-btn-name").text();
    $("#subcategory-title").text(name);

    // Update URL without reloading. buildTabPermalink already appends
    // window.location.search so the worth-it filter stays in the URL
    // when the active subcat changes via auto-promotion.
    var permalink = buildTabPermalink(slug, "overview");
    history.pushState({subcategory: slug, tab: "overview", name: name}, "", permalink);
}


function getCurrentCategoryKey() {
    /**
     * Extracts the current category key from the URL so per-category
     * filter preferences are scoped correctly. URL shape is
     * /dashboard/<platform>/<category>/<subcat>/<tab>/ (with optional
     * APPLICATION_ROOT prefix).
     *
     * Returns:
     *     str: Category key (e.g., "container-structure") or "" if not found.
     */

    var parts = window.location.pathname.split("/").filter(Boolean);
    var idx = parts.indexOf("dashboard");
    return (idx !== -1 && parts[idx + 2]) ? parts[idx + 2] : "";
}


function getStoredWorthItFilter(categoryKey) {
    /**
     * Reads the persisted active-pill set from the localStorage cache.
     * The server-side store at /api/preferences/<key>/ is the source
     * of truth, but we also mirror to localStorage so the rail can
     * paint instantly on page load while the server fetch happens
     * async. Returns null if nothing cached or value is malformed.
     */

    if (!categoryKey) {
        return null;
    }
    try {
        var raw = localStorage.getItem("worth_it_filter::" + categoryKey);
        if (!raw) {
            return null;
        }
        var parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed : null;
    } catch (e) {
        return null;
    }
}


function saveWorthItFilter(categoryKey, activeValues) {
    /**
     * Persists the active-pill set both to localStorage (instant cache)
     * and to the server (cross-device source of truth) via PUT
     * /api/preferences/<key>/. Server failures are silent — the local
     * cache means the next page load is still correct on this device.
     */

    if (!categoryKey) {
        return;
    }
    try {
        localStorage.setItem(
            "worth_it_filter::" + categoryKey,
            JSON.stringify(activeValues)
        );
    } catch (e) {
        // Quota exceeded or storage disabled — silently degrade
    }

    var csrfMeta = document.querySelector('meta[name="csrf-token"]');
    var csrfValue = csrfMeta ? csrfMeta.getAttribute("content") : "";

    fetch(window.APP_ROOT + "/api/preferences/worth_it_filter::" + encodeURIComponent(categoryKey) + "/", {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfValue,
            "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ value: activeValues }),
    }).catch(function() {
        // Server unreachable — local cache covers this device's next load
    });
}


function fetchWorthItFilterFromServer(categoryKey) {
    /**
     * GETs the persisted active-pill set from the server. If the value
     * differs from what's currently applied (which the local cache
     * would have already painted), update the pills + storage and
     * re-run the filter. Treat errors as "stick with cache."
     *
     * Returns a Promise that resolves when the server fetch completes.
     */

    if (!categoryKey) {
        return Promise.resolve();
    }

    return fetch(window.APP_ROOT + "/api/preferences/worth_it_filter::" + encodeURIComponent(categoryKey) + "/", {
        headers: { "X-Requested-With": "XMLHttpRequest" },
    })
    .then(function(response) {
        if (!response.ok) { return null; }
        return response.json();
    })
    .then(function(data) {
        if (!data || !Array.isArray(data.value)) {
            return;
        }

        // If the server's stored value differs from the local cache,
        // sync the UI to match the server. Skip on identical sets to
        // avoid an unnecessary re-render.
        var cached = getStoredWorthItFilter(categoryKey) || [];
        var serverSet = data.value.slice().sort().join("|");
        var cachedSet = cached.slice().sort().join("|");
        if (serverSet === cachedSet) {
            return;
        }

        $(".worth-it-pill").each(function() {
            var $pill = $(this);
            var value = $pill.attr("data-worth-it");
            var nowActive = data.value.indexOf(value) !== -1;
            $pill.toggleClass("active", nowActive);
            $pill.attr("aria-pressed", nowActive ? "true" : "false");
        });

        // Run the filter. saveWorthItFilter will write back the now-
        // synced value to localStorage and re-PUT it to the server,
        // which is a no-op on the server side.
        applyWorthItFilter();
    })
    .catch(function() { /* ignore server errors */ });
}


// Fixed render order so the trigger icons stay in the same sequence as
// the pills below: Yes (check), No (xmark), Depends (scale).
var WORTH_IT_ICON_ORDER = [
    { value: "Yes",     iconClass: "fa-thumbs-up",      colorClass: "worth-it-trigger-icon-yes" },
    { value: "No",      iconClass: "fa-ban",            colorClass: "worth-it-trigger-icon-no" },
    { value: "Depends", iconClass: "fa-scale-balanced", colorClass: "worth-it-trigger-icon-depends" }
];


function renderWorthItTriggerIcons(activeValues, totalPills) {
    /**
     * Renders an icon for each currently-active pill into the trigger
     * button. Stays empty when nothing is filtered (all pills active or
     * none active) so the trigger reads cleanly in the default state.
     *
     * Args:
     *     activeValues (Array<string>): worth_it values whose pills are
     *         currently selected.
     *     totalPills (number): how many pills exist in the panel,
     *         used to detect the "all active" no-filter state.
     */

    var $slot = $(".worth-it-filter-trigger-icons");
    if (!$slot.length) {
        return;
    }

    // No icons in the default (all-active) state — keeps the trigger
    // visually quiet until the user actually narrows the filter.
    if (activeValues.length === totalPills) {
        $slot.empty();
        return;
    }

    var html = "";
    for (var i = 0; i < WORTH_IT_ICON_ORDER.length; i++) {
        var spec = WORTH_IT_ICON_ORDER[i];
        if (activeValues.indexOf(spec.value) !== -1) {
            html += '<i class="fa-solid ' + spec.iconClass +
                    ' worth-it-trigger-icon ' + spec.colorClass + '"></i>';
        }
    }
    $slot.html(html);
}


function updateWorthItTriggerState(activeValues, totalPills) {
    /**
     * Reflects the active-filter state on the trigger button itself:
     *   - Adds .filtered when at least one pill is deselected, which
     *     paints the trigger in brand-blue tones so the user sees the
     *     filter at a glance without opening the pill panel.
     *   - Sets data-tooltip to "Showing X of Y subcategories" so a
     *     hover spells out exactly how many subcats the filter is
     *     hiding. Cleared in the default all-active state so the
     *     trigger doesn't grow a tooltip the user doesn't need.
     *
     * Must be called AFTER the .filtered-out class is toggled on the
     * rail buttons — the count is read from the DOM, not the active
     * pill set, so it correctly reflects subcats that have no
     * worth_it value (those are always filtered out when filtered).
     *
     * Args:
     *     activeValues (Array<string>): canonical Title-case worth-it
     *         values whose pills are currently active.
     *     totalPills (number): total pill count, used to detect the
     *         default all-active state.
     */

    var $trigger = $("#worth-it-filter-trigger");
    if (!$trigger.length) {
        return;
    }

    var isFiltered = activeValues.length < totalPills;
    $trigger.toggleClass("filtered", isFiltered);

    if (isFiltered) {
        var $allBtns = $(".subcategory-btn");
        var visible = $allBtns.filter(":not(.filtered-out)").length;
        var total = $allBtns.length;
        $trigger.attr(
            "data-tooltip",
            "Showing " + visible + " of " + total + " subcategories"
        );
    } else {
        $trigger.removeAttr("data-tooltip");
    }
}


function applyWorthItFilter(opts) {
    /**
     * Reads the current state of the worth-it filter pills, computes which
     * subcategory rail buttons should be visible, persists the active
     * set to localStorage + server (unless suppressed), reflects the
     * selection in the URL for sharing, and toggles .filtered-out on
     * rail buttons. If the currently-active subcat gets filtered out,
     * promote the first visible one so the right panel shows something
     * the rail still surfaces.
     *
     * Args:
     *     opts (object|undefined): optional flags.
     *         skipSave (bool): when true, don't write to localStorage
     *             or the server. Used during initial URL-driven load
     *             so a shared link doesn't overwrite the recipient's
     *             saved preferences just by being opened.
     */

    opts = opts || {};

    var $pills = $(".worth-it-pill");
    if (!$pills.length) {
        return;
    }

    var activeValues = $pills.filter(".active")
        .map(function() { return $(this).attr("data-worth-it"); })
        .get();

    if (!opts.skipSave) {
        saveWorthItFilter(getCurrentCategoryKey(), activeValues);
    }
    renderWorthItTriggerIcons(activeValues, $pills.length);
    updateUrlForWorthItFilter(activeValues, $pills.length);

    $(".subcategory-btn").each(function() {
        var $btn = $(this);
        var value = $btn.attr("data-worth-it") || "";
        var matches = activeValues.indexOf(value) !== -1;
        $btn.toggleClass("filtered-out", !matches);
    });

    // Refresh the trigger's tinted/tooltip state. Must run after the
    // .filtered-out toggling above so the "X of Y" count reflects what
    // the user actually sees in the rail.
    updateWorthItTriggerState(activeValues, $pills.length);

    // If the active subcat was just hidden, jump to the first visible
    // one so the rail and the panel stay aligned.
    var $activeBtn = $(".subcategory-btn.active");
    if ($activeBtn.length && $activeBtn.hasClass("filtered-out")) {
        var $firstVisible = $(".subcategory-btn:not(.filtered-out)").first();
        if ($firstVisible.length) {
            activateSubcategory($firstVisible.attr("data-subcategory"));
        }
    }
}


function restoreWorthItFilter() {
    /**
     * Loads the persisted active-pill set for the current category and
     * applies it to the pill UI before the first applyWorthItFilter
     * runs. If nothing is stored, leaves the default (all active) in
     * place. Save is suppressed during restore so we don't overwrite
     * the persisted value with the same one on every reload.
     */

    var stored = getStoredWorthItFilter(getCurrentCategoryKey());
    if (!stored) {
        return;
    }
    applyValuesToWorthItPills(stored);
}


$(document).ready(function() {

    // Click the trigger to expand/collapse the pill panel
    $("#worth-it-filter-trigger").on("click", function(e) {
        e.stopPropagation();
        var $filter = $("#worth-it-filter");
        var nowOpen = !$filter.hasClass("open");
        $filter.toggleClass("open", nowOpen);
        $(this).attr("aria-expanded", nowOpen ? "true" : "false");
    });

    // Click outside the filter panel to collapse it
    $(document).on("click", function(e) {
        var $filter = $("#worth-it-filter");
        if (!$filter.length || !$filter.hasClass("open")) {
            return;
        }
        if (!$(e.target).closest("#worth-it-filter").length) {
            $filter.removeClass("open");
            $("#worth-it-filter-trigger").attr("aria-expanded", "false");
        }
    });

    // Toggle each pill's active state on click, then re-apply the filter
    $(".worth-it-pill").on("click", function(e) {
        e.stopPropagation();
        var $pill = $(this);
        var nowActive = !$pill.hasClass("active");
        $pill.toggleClass("active", nowActive);
        $pill.attr("aria-pressed", nowActive ? "true" : "false");
        applyWorthItFilter();
    });

    // Precedence on initial load:
    //   1. ?worth-it=... in the URL wins (so shared links land the
    //      recipient on the sender's view without clobbering their own
    //      saved preferences — skipSave keeps localStorage/server clean).
    //   2. Otherwise restore from local cache for an instant paint,
    //      then reconcile with the server in the background.
    var urlValues = readWorthItFilterFromUrl();
    if (urlValues !== null) {
        applyValuesToWorthItPills(urlValues);
        applyWorthItFilter({ skipSave: true });
    } else {
        restoreWorthItFilter();
        applyWorthItFilter();
        fetchWorthItFilterFromServer(getCurrentCategoryKey());
    }
});
