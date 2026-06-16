/* bug-report.js
   Shared behavior for the bug report feature. Handles modal open/close,
   image paste interception on the textarea, file upload with drag-and-drop,
   client-side image resizing via Canvas API, and form submission to the
   Flask backend. Used on both canvas (Level 3) and category (Level 2) pages. */


// ========================================================================
//   Constants
// ========================================================================

var BUG_MAX_IMAGES = 3;                   // Maximum number of images allowed
var BUG_MAX_DIMENSION = 1920;             // Max width or height in pixels
var BUG_JPEG_QUALITY = 0.85;             // JPEG compression quality


// ========================================================================
//   State
// ========================================================================

// Array of { dataUrl: string, filename: string } objects
var bugImages = [];


// ========================================================================
//   Document Ready
// ========================================================================

$(document).ready(function() {
    bindBugReportModal();
    bindBugImagePaste();
    bindBugFileUpload();
    bindBugTooltip();
});


// ========================================================================
//   Viewport-Aware Tooltip
// ========================================================================

function bindBugTooltip() {
    /**
     * Creates a JS-positioned tooltip for the bug report trigger.
     * Calculates the trigger's distance from viewport edges and
     * places the tooltip so it never gets clipped. Falls back to
     * positioning above-left when the trigger is near the right edge.
     */

    // Bind to the class, not the id: the category page renders one bug
    // trigger per subcategory and only the first carries the id, so an
    // id selector would leave every other subcategory without a tooltip.
    var $trigger = $(".bug-report-trigger");
    if (!$trigger.length) return;

    // Create the tooltip element once and append to body
    var $tooltip = $("<div>", {
        "class": "bug-tooltip",
        text: "Report a bug"
    }).appendTo("body");

    var TOOLTIP_GAP = 8;

    $trigger.on("mouseenter", function() {
        var rect = this.getBoundingClientRect();
        var tooltipWidth = $tooltip.outerWidth();
        var tooltipHeight = $tooltip.outerHeight();
        var viewportWidth = window.innerWidth;

        // Default: position below the trigger, left-aligned
        var top = rect.bottom + TOOLTIP_GAP;
        var left = rect.left;

        // If tooltip overflows right edge, anchor to right side of trigger
        if (left + tooltipWidth > viewportWidth - TOOLTIP_GAP) {
            left = rect.right - tooltipWidth;
        }

        // If still overflows left, clamp to left edge
        if (left < TOOLTIP_GAP) {
            left = TOOLTIP_GAP;
        }

        // If tooltip overflows bottom, position above the trigger
        if (top + tooltipHeight > window.innerHeight - TOOLTIP_GAP) {
            top = rect.top - tooltipHeight - TOOLTIP_GAP;
        }

        $tooltip.css({ top: top + "px", left: left + "px" });
        $tooltip.addClass("visible");
    });

    $trigger.on("mouseleave", function() {
        $tooltip.removeClass("visible");
    });

    // Hide tooltip when modal opens
    $trigger.on("click", function() {
        $tooltip.removeClass("visible");
    });
}


// ========================================================================
//   Modal Open / Close / Submit
// ========================================================================

function bindBugReportModal() {
    /**
     * Binds all event handlers for the bug report modal: open trigger,
     * close (X, Cancel, overlay, Escape), and form submission.
     */

    var $overlay = $("#bug-report-modal-overlay");

    // Open via bug icon click. Bind to the class so every subcategory's
    // bug trigger opens the modal, not just the first (which carries the id).
    $(".bug-report-trigger").on("click", function() {
        $overlay.addClass("visible");
    });

    // Prevent clicks inside the dialog from closing the modal
    $overlay.find(".modal-dialog").on("click mousedown mouseup", function(e) {
        e.stopPropagation();
    });

    // Close via X button
    $("#close-bug-report-modal").on("click", function() {
        closeBugReportModal();
    });

    // Close via Cancel button
    $("#cancel-bug-report").on("click", function() {
        closeBugReportModal();
    });

    // Close via overlay click
    $overlay.on("click", function(e) {
        if ($(e.target).is("#bug-report-modal-overlay")) {
            closeBugReportModal();
        }
    });

    // Close on Escape key
    $(document).on("keydown", function(e) {
        if (e.key === "Escape" && $overlay.hasClass("visible")) {
            closeBugReportModal();
        }
    });

    // Form submission
    $("#bug-report-form").on("submit", function(e) {
        e.preventDefault();
        submitBugReport();
    });
}


function closeBugReportModal() {
    /**
     * Closes the bug report modal, resets the form, and clears images.
     */

    $("#bug-report-modal-overlay").removeClass("visible");
    $("#bug-report-form")[0].reset();
    bugImages = [];
    renderBugImagePreviews();
}


// ========================================================================
//   Form Submission
// ========================================================================

function submitBugReport() {
    /**
     * Validates required fields, builds the payload with base64 images,
     * and POSTs to /api/bug-report.
     */

    // Validate required fields
    var firstName = $("#bug-first-name").val().trim();
    var email = $("#bug-email").val().trim();
    var description = $("#bug-description").val().trim();

    if (!firstName || !email || !description) {
        return;
    }

    // Build payload
    var payload = {
        first_name: firstName,
        last_name: $("#bug-last-name").val().trim(),
        email: email,
        description: description,
        page_url: window.location.href,
        user_agent: navigator.userAgent,
        images: bugImages.map(function(img) {
            return {
                data_url: img.dataUrl,
                filename: img.filename
            };
        })
    };

    // Disable submit button
    var $submitBtn = $("#bug-report-form button[type='submit']");
    $submitBtn.prop("disabled", true).text("Submitting...");

    // POST to backend
    // CSRF token from meta tag in base.html
    var csrfToken = document.querySelector("meta[name='csrf-token']");
    var csrfValue = csrfToken ? csrfToken.getAttribute("content") : "";

    fetch(window.APP_ROOT + "/api/bug-report/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfValue
        },
        body: JSON.stringify(payload)
    })
    .then(function(response) {
        if (!response.ok) {
            throw new Error("Server returned " + response.status);
        }
        return response.json();
    })
    .then(function() {
        $submitBtn.text("Submitted!");
        setTimeout(function() {
            closeBugReportModal();
            $submitBtn.prop("disabled", false).text("Submit Bug Report");
        }, 800);
    })
    .catch(function() {
        $submitBtn.prop("disabled", false).text("Submit Bug Report");
        alert("Failed to submit bug report. Please try again.");
    });
}


// ========================================================================
//   Image Paste Interception
// ========================================================================

function bindBugImagePaste() {
    /**
     * Listens for paste events on the bug description textarea.
     * If the clipboard contains an image, intercepts it and adds
     * it to the image preview area instead of the textarea.
     * Plain text paste still works normally.
     */

    var textarea = document.getElementById("bug-description");
    if (!textarea) return;

    textarea.addEventListener("paste", function(e) {
        var clipboardData = e.clipboardData || e.originalEvent.clipboardData;
        if (!clipboardData || !clipboardData.items) return;

        for (var i = 0; i < clipboardData.items.length; i++) {
            if (clipboardData.items[i].type.indexOf("image") !== -1) {
                e.preventDefault();
                var file = clipboardData.items[i].getAsFile();
                processAndAddImage(file, "pasted-image.png");
                break;
            }
        }
    });
}


// ========================================================================
//   File Upload and Drag-and-Drop
// ========================================================================

function bindBugFileUpload() {
    /**
     * Binds the file input change event and drag-and-drop events
     * on the upload area.
     */

    // File input change
    $("#bug-image-input").on("change", function() {
        var files = this.files;
        for (var i = 0; i < files.length; i++) {
            processAndAddImage(files[i], files[i].name);
        }

        // Reset so the same file can be selected again
        this.value = "";
    });

    // Drag and drop
    var uploadArea = document.getElementById("bug-upload-area");
    if (!uploadArea) return;

    uploadArea.addEventListener("dragover", function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.add("drag-over");
    });

    uploadArea.addEventListener("dragleave", function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove("drag-over");
    });

    uploadArea.addEventListener("drop", function(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove("drag-over");

        var files = e.dataTransfer.files;
        for (var i = 0; i < files.length; i++) {
            if (files[i].type.indexOf("image") !== -1) {
                processAndAddImage(files[i], files[i].name);
            }
        }
    });
}


// ========================================================================
//   Image Processing (Canvas API Resize)
// ========================================================================

function processAndAddImage(file, filename) {
    /**
     * Reads an image file, resizes it if needed via the Canvas API,
     * and adds the result to the bugImages array and preview area.
     *
     * Args:
     *     file (File): The image file from paste, file input, or drag.
     *     filename (string): Display name for the image.
     */

    // Enforce max image count
    if (bugImages.length >= BUG_MAX_IMAGES) {
        alert("Maximum " + BUG_MAX_IMAGES + " images allowed.");
        return;
    }

    // Validate file type
    var validTypes = ["image/jpeg", "image/png", "image/gif", "image/webp"];
    if (validTypes.indexOf(file.type) === -1) {
        return;
    }

    var reader = new FileReader();

    reader.onload = function(e) {
        var img = new Image();

        img.onload = function() {
            resizeAndStore(img, file.type, filename);
        };

        img.src = e.target.result;
    };

    reader.readAsDataURL(file);
}


function resizeAndStore(img, mimeType, filename) {
    /**
     * Resizes an image using the Canvas API if it exceeds the max
     * dimension, converts to JPEG (unless PNG with transparency),
     * and stores the data URL in the bugImages array.
     *
     * Args:
     *     img (HTMLImageElement): The loaded image element.
     *     mimeType (string): Original MIME type of the image.
     *     filename (string): Display name for the image.
     */

    var width = img.naturalWidth;
    var height = img.naturalHeight;

    // Calculate new dimensions if resize is needed
    if (width > BUG_MAX_DIMENSION || height > BUG_MAX_DIMENSION) {
        if (width > height) {
            height = Math.round(height * (BUG_MAX_DIMENSION / width));
            width = BUG_MAX_DIMENSION;
        } else {
            width = Math.round(width * (BUG_MAX_DIMENSION / height));
            height = BUG_MAX_DIMENSION;
        }
    }

    // Draw to canvas
    var canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    var ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0, width, height);

    // Keep PNG if the original was PNG (to preserve transparency)
    var outputType = (mimeType === "image/png") ? "image/png" : "image/jpeg";
    var quality = (outputType === "image/jpeg") ? BUG_JPEG_QUALITY : undefined;

    var dataUrl = canvas.toDataURL(outputType, quality);

    // Store and render
    bugImages.push({
        dataUrl: dataUrl,
        filename: filename
    });
    renderBugImagePreviews();
}


// ========================================================================
//   Image Preview Rendering
// ========================================================================

function renderBugImagePreviews() {
    /**
     * Renders thumbnail previews in the preview area based on the
     * current bugImages array. Each thumbnail has a remove button.
     */

    var container = document.getElementById("bug-image-preview-area");
    if (!container) return;

    container.innerHTML = "";

    bugImages.forEach(function(imgData, index) {

        // Thumbnail wrapper
        var thumb = document.createElement("div");
        thumb.className = "bug-image-thumb";

        // Image element
        var imgEl = document.createElement("img");
        imgEl.src = imgData.dataUrl;
        imgEl.alt = imgData.filename;
        thumb.appendChild(imgEl);

        // Remove button
        var removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "bug-image-remove";
        removeBtn.innerHTML = "&times;";
        removeBtn.setAttribute("aria-label", "Remove image");
        removeBtn.addEventListener("click", function() {
            bugImages.splice(index, 1);
            renderBugImagePreviews();
        });
        thumb.appendChild(removeBtn);

        container.appendChild(thumb);
    });
}
