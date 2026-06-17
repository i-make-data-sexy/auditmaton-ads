/* intake.js
   Behavior for the single-page manual intake modal.

   Two independent features:

   1. Side toggle — the "demand" / "supply" radio pair shows the matching
      platform block and hides the other. When the side changes, checkboxes
      belonging to the hidden block are unchecked so the form only submits
      slugs for the chosen side.

   2. Site-type Other field — choosing "Other" from the site-type select
      reveals a suggestion text input. */

document.addEventListener("DOMContentLoaded", function () {

    /* ================================================
         Site-type Other field
       ================================================ */

    var siteTypeSelect = document.getElementById("intake-site-type");
    var otherWrap = document.getElementById("intake-other-wrap");
    var otherInput = document.getElementById("intake-site-type-other");

    if (siteTypeSelect && otherWrap) {

        /**
         * Shows the suggestion field when 'Other' is selected; hides it
         * otherwise. Focuses the field when it becomes visible.
         */
        function syncOtherField() {
            var isOther = siteTypeSelect.value === "other";
            otherWrap.hidden = !isOther;
            if (isOther && otherInput) {
                otherInput.focus();
            }
        }

        siteTypeSelect.addEventListener("change", syncOtherField);

        /* Sync once on load so a restored 'Other' selection shows its field */
        syncOtherField();
    }


    /* ================================================
         Demand / Supply side toggle
       ================================================ */

    var sideRadios = document.querySelectorAll("input[name='side']");
    var demandBlock = document.getElementById("intake-platforms-demand");
    var supplyBlock = document.getElementById("intake-platforms-supply");

    if (!sideRadios.length || !demandBlock || !supplyBlock) {
        return;
    }

    /**
     * Shows the platform block that matches the currently selected side;
     * hides the other. Unchecks all checkboxes in the hidden block so
     * only the active side's platforms are submitted.
     *
     * @param {string} side - "demand" or "supply"
     */
    function syncPlatformBlock(side) {
        var showDemand = side === "demand";

        demandBlock.classList.toggle("is-hidden", !showDemand);
        supplyBlock.classList.toggle("is-hidden", showDemand);

        /* Uncheck every box in the block that's being hidden */
        var hiddenBlock = showDemand ? supplyBlock : demandBlock;
        hiddenBlock.querySelectorAll("input[type='checkbox']").forEach(function (cb) {
            cb.checked = false;
        });
    }

    sideRadios.forEach(function (radio) {
        radio.addEventListener("change", function () {
            syncPlatformBlock(this.value);
        });
    });

    /* Sync on page load using whichever radio is pre-checked */
    var checked = document.querySelector("input[name='side']:checked");
    syncPlatformBlock(checked ? checked.value : "demand");
});
