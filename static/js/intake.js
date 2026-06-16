/* intake.js
   Behavior for the single-page manual intake modal. The only interactive
   piece is the site-type "Other" option: choosing it reveals a text field
   where the user can suggest a new site type. Everything else is a plain
   POST form. */

document.addEventListener("DOMContentLoaded", function () {

    var select = document.getElementById("intake-site-type");
    var otherWrap = document.getElementById("intake-other-wrap");
    var otherInput = document.getElementById("intake-site-type-other");

    if (!select || !otherWrap) {
        return;
    }

    /**
     * Shows the suggestion field when 'Other' is selected, hides it
     * otherwise. Focuses the field when it appears so the user can type
     * right away.
     */
    function syncOtherField() {
        var isOther = select.value === "other";
        otherWrap.hidden = !isOther;

        if (isOther && otherInput) {
            otherInput.focus();
        }
    }

    select.addEventListener("change", syncOtherField);

    /* Sync once on load so a restored 'Other' selection shows its field */
    syncOtherField();
});
