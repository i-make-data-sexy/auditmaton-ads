// pricing.js
// Handles add-on selection, running total calculation, CTA link building,
// and lightbox open/close for the dedicated pricing page.

document.addEventListener("DOMContentLoaded", function () {

    // ========================================================================
    //   Constants
    // ========================================================================

    // Base price in cents (always included)
    var BASE_PRICE = 29500;


    // ========================================================================
    //   DOM References
    // ========================================================================

    var addonCards = document.querySelectorAll(".pricing-addon-card");
    var totalAmount = document.getElementById("pricing-total-amount");
    var ctaHero = document.getElementById("pricing-cta-hero");
    var ctaBottom = document.getElementById("pricing-cta-bottom");
    var lightboxOverlays = document.querySelectorAll(".modal-overlay[data-product]");


    // ========================================================================
    //   Add-on Selection
    // ========================================================================

    addonCards.forEach(function (card) {

        // Click the "Add" / "Remove" button to toggle selection
        var selectBtn = card.querySelector(".pricing-addon-select");
        if (selectBtn) {
            selectBtn.addEventListener("click", function (e) {
                e.stopPropagation();
                toggleAddon(card);
            });
        }

        // Click the card itself to toggle selection
        card.addEventListener("click", function (e) {

            // Don't toggle if clicking "Learn More"
            if (e.target.closest(".pricing-addon-learn-more")) {
                return;
            }

            toggleAddon(card);
        });
    });


    /**
     * Toggles an add-on card's selected state and updates the UI.
     *
     * Args:
     *     card (Element): The add-on card element to toggle.
     */
    function toggleAddon(card) {
        var isSelected = card.classList.toggle("pricing-addon--selected");

        // Update button text
        var btn = card.querySelector(".pricing-addon-select");
        if (btn) {
            if (isSelected) {
                btn.innerHTML = '<i class="fa-solid fa-check"></i> Added';
            } else {
                btn.innerHTML = '<i class="fa-solid fa-plus"></i> Add';
            }
        }

        updateTotal();
        updateCtaLinks();
    }


    // ========================================================================
    //   Running Total
    // ========================================================================

    /**
     * Recalculates the total from base + selected add-ons and updates the display.
     */
    function updateTotal() {
        var total = BASE_PRICE;

        // Sum selected add-on prices
        document.querySelectorAll(".pricing-addon--selected").forEach(function (card) {
            var price = parseInt(card.getAttribute("data-price"), 10);
            if (!isNaN(price)) {
                total += price;
            }
        });

        // Format as dollars
        var dollars = Math.round(total / 100);

        if (totalAmount) {
            totalAmount.textContent = "$" + dollars + "/yr";
        }
    }


    // ========================================================================
    //   CTA Link Builder
    // ========================================================================

    /**
     * Updates CTA button hrefs with selected product slugs as query params.
     */
    function updateCtaLinks() {

        // Always include base
        var slugs = ["base"];

        // Add selected add-on slugs
        document.querySelectorAll(".pricing-addon--selected").forEach(function (card) {
            var slug = card.getAttribute("data-slug");
            if (slug) {
                slugs.push(slug);
            }
        });

        var href = "/register/?products=" + slugs.join(",");

        if (ctaHero) {
            ctaHero.setAttribute("href", href);
        }
        if (ctaBottom) {
            ctaBottom.setAttribute("href", href);
        }
    }


    // ========================================================================
    //   Lightbox — Open
    // ========================================================================

    document.querySelectorAll(".pricing-addon-learn-more").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            e.stopPropagation();
            var slug = btn.getAttribute("data-slug");
            var overlay = document.querySelector('.modal-overlay[data-product="' + slug + '"]');
            if (overlay) {
                overlay.classList.add("visible");
            }
        });
    });


    // ========================================================================
    //   Lightbox — Close
    // ========================================================================

    lightboxOverlays.forEach(function (overlay) {

        // Close button
        var closeBtn = overlay.querySelector(".modal-dialog-close");
        if (closeBtn) {
            closeBtn.addEventListener("click", function () {
                overlay.classList.remove("visible");
            });
        }

        // Backdrop click
        overlay.addEventListener("click", function (e) {
            if (e.target === overlay) {
                overlay.classList.remove("visible");
            }
        });
    });

    // Escape key closes any open lightbox
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") {
            lightboxOverlays.forEach(function (overlay) {
                overlay.classList.remove("visible");
            });
        }
    });
});
