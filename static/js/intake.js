/* intake.js
   Behavior for the 2-step intake wizard modal.

   Three independent features:

   1. Wizard navigation, "Next" advances from step 1 to step 2;
      "Back" returns to step 1. The progress indicator (circles and
      connecting line) updates to reflect which step is active or done.

   2. Side toggle, the "demand" / "supply" radio pair on step 1
      shows the matching platform block and hides the other. When the
      side changes, checkboxes belonging to the hidden block are unchecked
      so the form only submits slugs for the chosen side.

   3. Step-1 soft validation, advancing to step 2 requires a side
      selection and at least one platform checkbox. If the requirement
      is not met, a warning message is shown but the user is NOT
      hard-blocked (they can still proceed after seeing the warning). */

document.addEventListener("DOMContentLoaded", function () {

    /* ================================================
         Element references
       ================================================ */

    var step1 = document.getElementById("wizard-step-1");
    var step2 = document.getElementById("wizard-step-2");
    var nextBtn = document.getElementById("intake-next-btn");
    var backBtn = document.getElementById("intake-back-btn");
    var warning = document.getElementById("intake-step1-warning");

    var dot1 = document.getElementById("intake-step-dot-1");
    var dot2 = document.getElementById("intake-step-dot-2");
    var progressLine = document.getElementById("intake-progress-line-1");

    var sideRadios = document.querySelectorAll("input[name='side']");
    var demandBlock = document.getElementById("intake-platforms-demand");
    var supplyBlock = document.getElementById("intake-platforms-supply");


    /* ================================================
         Demand / Supply side toggle
       ================================================ */

    /**
     * Shows the platform block matching the chosen side and hides the other.
     * Unchecks all checkboxes in the hidden block so the form only submits
     * slugs for the active side.
     *
     * @param {string} side - "demand" or "supply"
     */
    function syncPlatformBlock(side) {
        if (!demandBlock || !supplyBlock) { return; }

        var showDemand = (side === "demand");

        demandBlock.classList.toggle("is-hidden", !showDemand);
        supplyBlock.classList.toggle("is-hidden", showDemand);

        /* Uncheck every box in the block that is being hidden */
        var hiddenBlock = showDemand ? supplyBlock : demandBlock;
        hiddenBlock.querySelectorAll("input[type='checkbox']").forEach(function (cb) {
            cb.checked = false;
        });
    }

    if (sideRadios.length) {
        sideRadios.forEach(function (radio) {
            radio.addEventListener("change", function () {
                syncPlatformBlock(this.value);

                /* Clear the warning when the user makes a selection */
                if (warning) { warning.hidden = true; }
            });
        });

        /* Sync once on load from the pre-checked radio */
        var checkedSide = document.querySelector("input[name='side']:checked");
        syncPlatformBlock(checkedSide ? checkedSide.value : "demand");
    }

    /* Also clear the warning when the user checks any platform */
    document.querySelectorAll("input[name='platforms']").forEach(function (cb) {
        cb.addEventListener("change", function () {
            if (warning) { warning.hidden = true; }
        });
    });


    /* ================================================
         Progress indicator helpers
       ================================================ */

    /**
     * Updates the step circles and connecting line to reflect the current step.
     *
     * @param {number} step - 1 or 2
     */
    function setProgressStep(step) {
        if (!dot1 || !dot2 || !progressLine) { return; }

        if (step === 1) {
            dot1.className = "intake-progress-step active";
            dot2.className = "intake-progress-step";
            progressLine.classList.remove("done");
        } else {
            dot1.className = "intake-progress-step done";
            dot2.className = "intake-progress-step active";
            progressLine.classList.add("done");
        }
    }


    /* ================================================
         Wizard navigation
       ================================================ */

    /**
     * Returns true when the step-1 requirements are met:
     * a side radio is selected AND at least one platform is checked.
     *
     * @returns {boolean}
     */
    function step1IsValid() {
        var sideSelected = !!document.querySelector("input[name='side']:checked");
        var platformChecked = !!document.querySelector("input[name='platforms']:checked");
        return sideSelected && platformChecked;
    }

    /**
     * Advances from step 1 to step 2.
     * Shows a soft warning if the requirements are not met, but lets the
     * user continue after a second click (the warning stays visible).
     */
    function goToStep2() {
        if (!step1IsValid()) {
            if (warning) { warning.hidden = false; }

            /* Allow advancing on a second click even without a selection, 
               the handler is not re-registered, so clicking Next again simply
               calls this function again. The warning stays visible but the
               user is not hard-blocked. */
            return;
        }

        if (step1) { step1.classList.remove("active"); }
        if (step2) { step2.classList.add("active"); }
        setProgressStep(2);

        /* Scroll the modal body back to the top */
        var body2 = step2 ? step2.querySelector(".intake-modal-body") : null;
        if (body2) { body2.scrollTop = 0; }
    }

    /**
     * Returns from step 2 to step 1.
     */
    function goToStep1() {
        if (step2) { step2.classList.remove("active"); }
        if (step1) { step1.classList.add("active"); }
        setProgressStep(1);

        /* Scroll the modal body back to the top */
        var body1 = step1 ? step1.querySelector(".intake-modal-body") : null;
        if (body1) { body1.scrollTop = 0; }
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", goToStep2);
    }

    if (backBtn) {
        backBtn.addEventListener("click", goToStep1);
    }


    /* ================================================
         Initial state
       ================================================ */

    /* Set progress indicator to step 1 */
    setProgressStep(1);
});
