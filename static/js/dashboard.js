/* dashboard.js
   Handles dashboard-specific interactivity: spinner management, progress
   bar animations, category card click navigation, Bootstrap tooltips,
   URL parameter utilities, and live progress updates from localStorage. */


/* ========================================================================
   Section 1: Spinner
   ======================================================================== */

/**
 * Shows a spinner overlay inside the given element.
 * The element must contain a child with class "spinner-overlay".
 */
function showSpinner(elementId) {
    var overlay = document.getElementById(elementId);
    if (overlay) {
        overlay.classList.remove("hidden");
        overlay.style.opacity = "1";
    }
}

/**
 * Hides a spinner overlay with a fade-out transition.
 * Fades opacity over 300ms, then adds the hidden class.
 */
function hideSpinner(elementId) {
    var overlay = document.getElementById(elementId);
    if (overlay) {
        overlay.style.opacity = "0";
        setTimeout(function() {
            overlay.classList.add("hidden");
        }, 300);
    }
}


/* ========================================================================
   Section 2: Progress Bar Animation
   ======================================================================== */

$(document).ready(function() {

    /* Animate progress bars from 0 to their target width */
    $(".progress-fill").each(function() {
        var target = $(this).data("progress");
        $(this).css("width", target + "%");
    });
});


/* ========================================================================
   Section 3: Card Click Handlers
   ======================================================================== */

/* Navigate to category page when a kanban card is clicked */
$(document).on("click", ".kanban-card", function() {
    var categoryKey = $(this).data("category").replace(/_/g, "-");
    var platform = $(".kanban-board").data("platform") || "";
    window.location.href = window.APP_ROOT + "/dashboard/" + platform + "/" + categoryKey + "/";
});


/* ========================================================================
   Section 4: Tooltips
   ======================================================================== */

/* Initialize Bootstrap tooltips for locked category cards */
$(function () {
    $("[data-toggle=\"tooltip\"]").tooltip();
});


/* ========================================================================
   Section 5: URL Parameter Handling
   ======================================================================== */

/**
 * Parses URL query parameters into a key-value object.
 * Returns an object with parameter names as keys.
 */
function getUrlParams() {
    var params = {};
    var queryString = window.location.search.substring(1);
    if (!queryString) {
        return params;
    }

    var pairs = queryString.split("&");
    for (var i = 0; i < pairs.length; i++) {
        var pair = pairs[i].split("=");
        var key = decodeURIComponent(pair[0]);
        var value = pair.length > 1 ? decodeURIComponent(pair[1]) : "";
        params[key] = value;
    }
    return params;
}

/**
 * Updates URL query parameters without triggering a page reload.
 * Merges the provided params object with existing parameters.
 * Removes parameters set to null or empty string.
 */
function updateUrlParams(newParams) {
    var params = getUrlParams();

    /* Merge new params */
    for (var key in newParams) {
        if (newParams.hasOwnProperty(key)) {
            if (newParams[key] === null || newParams[key] === "") {
                delete params[key];
            } else {
                params[key] = newParams[key];
            }
        }
    }

    /* Build query string */
    var pairs = [];
    for (var k in params) {
        if (params.hasOwnProperty(k)) {
            pairs.push(encodeURIComponent(k) + "=" + encodeURIComponent(params[k]));
        }
    }

    var newUrl = window.location.pathname;
    if (pairs.length > 0) {
        newUrl += "?" + pairs.join("&");
    }

    window.history.replaceState({}, "", newUrl);
}


/* ========================================================================
   Section 6: Live Progress from localStorage
   ======================================================================== */

/**
 * Updates dashboard category cards with real completion data from localStorage.
 * Reads the audit_check_status object, counts completed checks (done or skip)
 * per category, and updates the progress bars and text.
 */
function updateDashboardProgress() {
    var raw = localStorage.getItem("audit_check_status");
    if (!raw) {
        return;
    }

    var statuses;
    try {
        statuses = JSON.parse(raw);
    } catch (e) {
        return;
    }

    $(".kanban-card").each(function() {
        var card = $(this);
        var categoryKey = card.data("category");
        var total = parseInt(card.data("total"), 10);

        if (!categoryKey || !total) {
            return;
        }

        /* Skip categories with no localStorage data to preserve server values */
        var categoryStatuses = statuses[categoryKey];
        if (!categoryStatuses) {
            return;
        }

        /* Count completed checks (done or skip) */
        var completed = 0;
        if (categoryStatuses) {
            for (var checkId in categoryStatuses) {
                if (categoryStatuses.hasOwnProperty(checkId)) {
                    var status = categoryStatuses[checkId];
                    if (status === "done" || status === "skip") {
                        completed++;
                    }
                }
            }
        }

        /* Calculate percentage */
        var percentage = Math.round((completed / total) * 100);

        /* Update progress bar */
        var progressFill = card.find(".progress-fill");
        progressFill.data("progress", percentage);
        progressFill.css("width", percentage + "%");

        /* Update progress bar color class */
        progressFill.removeClass("progress-fill-not_started progress-fill-in_progress progress-fill-complete");
        if (completed === 0) {
            progressFill.addClass("progress-fill-not_started");
        } else if (completed >= total) {
            progressFill.addClass("progress-fill-complete");
        } else {
            progressFill.addClass("progress-fill-in_progress");
        }

        /* Update progress text */
        var progressText = card.find("[data-progress-text]");
        if (progressText.length) {
            var isMuted = progressText.data("muted") === "true";
            var prefix = isMuted ? "Deprioritized &middot; " : "";

            if (completed >= total) {
                progressText.html('<i class="fa-solid fa-check"></i> All ' + total + " complete");
            } else {
                progressText.html(prefix + completed + " of " + total + " complete");
            }
        }
    });
}

$(document).ready(function() {

    /* Apply localStorage progress after initial progress bar animation */
    updateDashboardProgress();
});


/* ========================================================================
   Section 7: Upload Modal
   ======================================================================== */

/**
 * Opens the crawl data upload modal.
 * Adds the "visible" class to the overlay to show it.
 */
function openUploadModal() {
    $("#upload-modal-overlay").addClass("visible");
}

/**
 * Closes the crawl data upload modal.
 * Removes the "visible" class from the overlay to hide it.
 */
function closeUploadModal() {
    $("#upload-modal-overlay").removeClass("visible");
}

$(document).ready(function() {

    /* Open modal when refresh icon is clicked */
    $("#open-upload-modal").on("click", function() {
        openUploadModal();
    });

    /* Close modal via the X button */
    $("#close-upload-modal").on("click", function() {
        closeUploadModal();
    });

    /* Close modal when clicking the overlay background */
    $("#upload-modal-overlay").on("click", function(e) {
        if (e.target === this) {
            closeUploadModal();
        }
    });

    /* Close modal with Escape key */
    $(document).on("keydown", function(e) {
        if (e.key === "Escape") {
            closeUploadModal();
        }
    });
});
