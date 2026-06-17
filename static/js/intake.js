/* intake.js
   Behavior for the 2-step intake wizard modal (Auditmaton: Ads).

   1. Wizard navigation: "Next" advances panel 1 to panel 2, "Back" returns.
      The progress indicator fills (active blue, completed green) and the
      footer swaps the Next button for the green "Start Audit" submit.
   2. Side toggle: the demand/supply radio shows the matching platform block
      and clears any checkboxes in the hidden block so only the chosen side's
      platforms submit.
   Everything lives in one form; only the final submit posts. */

document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("intake-form");
    if (!form) return;

    // ====================================================================
    //   Wizard navigation
    // ====================================================================
    var panels = [
        document.getElementById("intake-panel-1"),
        document.getElementById("intake-panel-2"),
    ];
    var steps = Array.prototype.slice.call(
        document.querySelectorAll(".intake-progress-step")
    );
    var lines = Array.prototype.slice.call(
        document.querySelectorAll(".intake-progress-line")
    );
    var backBtn = document.getElementById("intake-back");
    var nextBtn = document.getElementById("intake-next");
    var submitBtn = document.getElementById("intake-submit");
    var modal = document.getElementById("intake-modal");
    var last = panels.length - 1;
    var current = 0;

    // Render the wizard at the given panel index.
    function show(idx) {
        panels.forEach(function (p, i) {
            if (p) p.classList.toggle("active", i === idx);
        });
        steps.forEach(function (s, i) {
            s.classList.toggle("active", i === idx);
            s.classList.toggle("done", i < idx);
        });
        lines.forEach(function (l, i) {
            l.classList.toggle("done", i < idx);
        });

        // Footer: hide Back on the first panel; swap Next for Start Audit on
        // the last panel.
        backBtn.classList.toggle("hidden", idx === 0);
        nextBtn.classList.toggle("intake-hidden", idx === last);
        submitBtn.classList.toggle("intake-hidden", idx !== last);

        current = idx;
        if (modal) modal.scrollTop = 0;
    }

    nextBtn.addEventListener("click", function () {
        if (current < last) show(current + 1);
    });
    backBtn.addEventListener("click", function () {
        if (current > 0) show(current - 1);
    });

    // ====================================================================
    //   Demand / Supply side toggle
    // ====================================================================
    var blocks = Array.prototype.slice.call(
        document.querySelectorAll(".intake-platform-block")
    );

    // Show only the chosen side's platform block; clear checkboxes in the
    // hidden block so a hidden selection never submits.
    function syncSide() {
        var checked = form.querySelector('input[name="side"]:checked');
        var side = checked ? checked.value : "demand";
        blocks.forEach(function (b) {
            var match = b.getAttribute("data-side") === side;
            b.classList.toggle("is-hidden", !match);
            if (!match) {
                Array.prototype.slice
                    .call(b.querySelectorAll('input[name="platforms"]:checked'))
                    .forEach(function (cb) {
                        cb.checked = false;
                    });
            }
        });
    }

    Array.prototype.slice
        .call(form.querySelectorAll('input[name="side"]'))
        .forEach(function (r) {
            r.addEventListener("change", syncSide);
        });

    syncSide();
    show(0);
});
