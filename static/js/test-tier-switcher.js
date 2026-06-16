/* test-tier-switcher.js
   Admin-only "Test as tier" switcher in the footer menu. Posts the selected
   tier to /admin/test-tier/, then reloads so the new effective tier takes
   effect across the whole page (nav state, body attribute, future feature
   gates). Only loaded for real admins (the include is gated in base.html). */

(function () {
    "use strict";

    // Reads the CSRF token from the meta tag (same pattern as auth.js)
    function getCsrfToken() {
        var meta = document.querySelector("meta[name='csrf-token']");
        return meta ? meta.getAttribute("content") : "";
    }

    document.addEventListener("DOMContentLoaded", function () {
        var select = document.getElementById("test-tier-select");
        if (!select) {
            return;
        }

        // Remember the starting value so we can restore it if the POST fails
        var lastTier = select.value;

        select.addEventListener("change", function () {
            var tier = select.value;
            select.disabled = true;

            fetch(window.APP_ROOT + "/admin/test-tier/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify({ tier: tier }),
            })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error("Tier switch failed (HTTP " + response.status + ")");
                    }
                    return response.json();
                })
                .then(function () {
                    // Reload so every tier-gated element re-renders for the
                    // new effective tier
                    window.location.reload();
                })
                .catch(function (err) {
                    // Restore the previous selection and re-enable on failure
                    console.error(err);
                    select.value = lastTier;
                    select.disabled = false;
                });
        });
    });
})();
