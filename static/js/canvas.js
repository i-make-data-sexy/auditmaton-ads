/* canvas.js
   Page-specific behavior for the canvas view (Level 3). Handles
   top-level tab switching (Guide / Canvas), -ate step navigation,
   tool tab switching, site type overlay tabs, Quill editor
   initialization, Add to Canvas button actions, and Kindle-style
   contextual text selection (Look up, Rephrase, Report). */


// ========================================================================
//   Quill Editor Instance
// ========================================================================

var quill = null;


// ========================================================================
//   Document Ready
// ========================================================================

$(document).ready(function() {

    // Selection popover is shared by canvas and overview pages — bind it
    // first and unconditionally so it works wherever [data-content-path]
    // elements exist
    bindTextSelection();

    // The remaining initializers are canvas-page specific. Skip them on
    // pages that don't host the canvas editor (e.g., overview pages).
    if (!document.getElementById("canvas-editor")) {
        return;
    }

    // Initialize the Quill rich text editor
    initQuillEditor();

    // Bind top-level tab switching (Guide / Canvas)
    bindTabSwitching();

    // Bind -ate step pill navigation
    bindStepNavigation();

    // Bind investigate tool checkbox picker
    bindToolCheckboxes();

    // Bind Add to Canvas buttons
    bindAddToCanvas();

    // Bind Report as Inaccurate modal
    bindReportModal();

    // Bind post-rephrase modals
    bindRephraseModals();

    // Bind update feedback modal
    bindFeedbackModal();

    // Bind heading styles customization modal
    bindStylesCustomizeModal();

    // Bind custom spacing modal
    bindSpacingModal();
});


// ========================================================================
//   Quill Editor Initialization
// ========================================================================

function registerStyleAttributors() {
    /**
     * Registers Style-based Parchment attributors for font-size,
     * line-height, and paragraph spacing so Quill preserves these
     * styles in the Delta format.
     */

    var Parchment = Quill.import("parchment");

    // Font size: preserves inline font-size (e.g., heading sizes)
    var SizeStyle = new Parchment.Attributor.Style("size", "font-size", {
        scope: Parchment.Scope.INLINE
    });
    Quill.register(SizeStyle, true);

    // Line height: preserves inline line-height
    var LineHeightStyle = new Parchment.Attributor.Style("lineHeight", "line-height", {
        scope: Parchment.Scope.BLOCK
    });
    Quill.register(LineHeightStyle, true);

    // Paragraph spacing before (margin-top)
    var MarginBeforeStyle = new Parchment.Attributor.Style("marginBefore", "margin-top", {
        scope: Parchment.Scope.BLOCK
    });
    Quill.register(MarginBeforeStyle, true);

    // Paragraph spacing after (margin-bottom)
    var MarginAfterStyle = new Parchment.Attributor.Style("marginAfter", "margin-bottom", {
        scope: Parchment.Scope.BLOCK
    });
    Quill.register(MarginAfterStyle, true);
}


// All available fonts, listed alphabetically by display name
var FONT_WHITELIST = [
    "arial",
    "arial-black",
    "baskerville",
    "book-antiqua",
    "brush-script-mt",
    "calibri",
    "cambria",
    "candara",
    "century-gothic",
    "comic-sans-ms",
    "consolas",
    "constantia",
    "copperplate",
    "corbel",
    "courier-new",
    "didot",
    "franklin-gothic",
    "futura",
    "garamond",
    "geneva",
    "georgia",
    "gill-sans",
    "goudy-old-style",
    "helvetica",
    "helvetica-neue",
    "impact",
    "lucida-bright",
    "lucida-console",
    "lucida-grande",
    "lucida-sans",
    "menlo",
    "monaco",
    "optima",
    "palatino",
    "perpetua",
    "rockwell",
    "segoe-ui",
    "tahoma",
    "times-new-roman",
    "trebuchet-ms",
    "verdana"
];


// Mapping of font slugs to human-readable display names
var FONT_DISPLAY_NAMES = {
    "arial": "Arial",
    "arial-black": "Arial Black",
    "baskerville": "Baskerville",
    "book-antiqua": "Book Antiqua",
    "brush-script-mt": "Brush Script MT",
    "calibri": "Calibri",
    "cambria": "Cambria",
    "candara": "Candara",
    "century-gothic": "Century Gothic",
    "comic-sans-ms": "Comic Sans MS",
    "consolas": "Consolas",
    "constantia": "Constantia",
    "copperplate": "Copperplate",
    "corbel": "Corbel",
    "courier-new": "Courier New",
    "didot": "Didot",
    "franklin-gothic": "Franklin Gothic",
    "futura": "Futura",
    "garamond": "Garamond",
    "geneva": "Geneva",
    "georgia": "Georgia",
    "gill-sans": "Gill Sans",
    "goudy-old-style": "Goudy Old Style",
    "helvetica": "Helvetica",
    "helvetica-neue": "Helvetica Neue",
    "impact": "Impact",
    "lucida-bright": "Lucida Bright",
    "lucida-console": "Lucida Console",
    "lucida-grande": "Lucida Grande",
    "lucida-sans": "Lucida Sans",
    "menlo": "Menlo",
    "monaco": "Monaco",
    "optima": "Optima",
    "palatino": "Palatino",
    "perpetua": "Perpetua",
    "rockwell": "Rockwell",
    "segoe-ui": "Segoe UI",
    "tahoma": "Tahoma",
    "times-new-roman": "Times New Roman",
    "trebuchet-ms": "Trebuchet MS",
    "verdana": "Verdana"
};

// Mapping of font slugs to CSS font-family values
var FONT_FAMILIES = {
    "arial": "Arial, sans-serif",
    "arial-black": "\"Arial Black\", sans-serif",
    "baskerville": "Baskerville, \"Baskerville Old Face\", serif",
    "book-antiqua": "\"Book Antiqua\", Palatino, serif",
    "brush-script-mt": "\"Brush Script MT\", cursive",
    "calibri": "Calibri, sans-serif",
    "cambria": "Cambria, serif",
    "candara": "Candara, sans-serif",
    "century-gothic": "\"Century Gothic\", sans-serif",
    "comic-sans-ms": "\"Comic Sans MS\", cursive",
    "consolas": "Consolas, monospace",
    "constantia": "Constantia, serif",
    "copperplate": "Copperplate, \"Copperplate Gothic Light\", serif",
    "corbel": "Corbel, sans-serif",
    "courier-new": "\"Courier New\", Courier, monospace",
    "didot": "Didot, \"Bodoni MT\", serif",
    "franklin-gothic": "\"Franklin Gothic Medium\", sans-serif",
    "futura": "Futura, sans-serif",
    "garamond": "Garamond, serif",
    "geneva": "Geneva, sans-serif",
    "georgia": "Georgia, serif",
    "gill-sans": "\"Gill Sans\", sans-serif",
    "goudy-old-style": "\"Goudy Old Style\", serif",
    "helvetica": "Helvetica, sans-serif",
    "helvetica-neue": "\"Helvetica Neue\", Helvetica, sans-serif",
    "impact": "Impact, sans-serif",
    "lucida-bright": "\"Lucida Bright\", serif",
    "lucida-console": "\"Lucida Console\", monospace",
    "lucida-grande": "\"Lucida Grande\", sans-serif",
    "lucida-sans": "\"Lucida Sans\", sans-serif",
    "menlo": "Menlo, monospace",
    "monaco": "Monaco, monospace",
    "optima": "Optima, sans-serif",
    "palatino": "Palatino, \"Palatino Linotype\", serif",
    "perpetua": "Perpetua, serif",
    "rockwell": "Rockwell, serif",
    "segoe-ui": "\"Segoe UI\", sans-serif",
    "tahoma": "Tahoma, sans-serif",
    "times-new-roman": "\"Times New Roman\", Times, serif",
    "trebuchet-ms": "\"Trebuchet MS\", sans-serif",
    "verdana": "Verdana, sans-serif"
};


function registerFontWhitelist() {
    /**
     * Registers a comprehensive font whitelist with Quill so the font
     * picker dropdown offers a wide selection of system fonts. Updates
     * both the class attributor and the format to ensure consistency.
     */

    // Update the class attributor whitelist
    var FontClass = Quill.import("attributors/class/font");
    FontClass.whitelist = FONT_WHITELIST;
    Quill.register(FontClass, true);

    // Also update the format-level whitelist
    var FontFormat = Quill.import("formats/font");
    FontFormat.whitelist = FONT_WHITELIST;
    Quill.register(FontFormat, true);
}


// ========================================================================
//   Quill Editor — Recent Fonts (localStorage)
// ========================================================================

function getRecentFonts() {
    /**
     * Returns the list of recently used font slugs from localStorage.
     *
     * Returns:
     *     Array: Up to 5 font slug strings, most recent first.
     */

    var stored = localStorage.getItem("canvas_recent_fonts");
    return stored ? JSON.parse(stored) : [];
}


function saveRecentFont(fontSlug) {
    /**
     * Saves a font slug to the recent fonts list in localStorage.
     * Keeps only the 5 most recent, with the newest first.
     *
     * Args:
     *     fontSlug (string): The font identifier (e.g., 'arial').
     */

    var recents = getRecentFonts();

    // Remove if already in the list so it moves to front
    recents = recents.filter(function(f) { return f !== fontSlug; });

    // Add to front
    recents.unshift(fontSlug);

    // Keep only 5
    recents = recents.slice(0, 5);
    localStorage.setItem("canvas_recent_fonts", JSON.stringify(recents));
}


function setupRecentFonts() {
    /**
     * Reorders the font picker dropdown to show recently used fonts
     * at the top, separated by a visual divider from the full
     * alphabetical list. Also binds click listeners to track future
     * font selections.
     */

    var picker = document.querySelector("#canvas-editor-wrapper .ql-font .ql-picker-options");
    if (!picker) return;

    // Move recent fonts to the top of the dropdown
    var recents = getRecentFonts();
    var movedCount = 0;

    // Iterate in reverse so the most recent ends up first
    for (var i = recents.length - 1; i >= 0; i--) {
        var item = picker.querySelector(".ql-picker-item[data-value=\"" + recents[i] + "\"]");
        if (item) {
            picker.insertBefore(item, picker.firstChild);
            movedCount++;
        }
    }

    // Add a separator between recent and alphabetical fonts
    if (movedCount > 0) {
        var separator = document.createElement("span");
        separator.className = "ql-picker-separator";
        var allItems = picker.querySelectorAll(".ql-picker-item");
        if (allItems[movedCount]) {
            picker.insertBefore(separator, allItems[movedCount]);
        }
    }

    // Track font selections for future recent fonts
    picker.querySelectorAll(".ql-picker-item").forEach(function(item) {
        item.addEventListener("mousedown", function() {
            var value = this.getAttribute("data-value");
            if (value) {
                saveRecentFont(value);
            }
        });
    });
}


// ========================================================================
//   Heading Styles Customization
// ========================================================================

function getDefaultHeadingStyles() {
    /**
     * Returns the default heading style settings for H1-H6.
     *
     * Returns:
     *     Object: Keys are heading levels (1-6), values contain font, size, color.
     */

    return {
        "1": { font: "", size: 42, color: "#333333", marginAfter: 15 },
        "2": { font: "", size: 34, color: "#0273BE", marginAfter: 15 },
        "3": { font: "", size: 30, color: "#FFC04D", marginAfter: 12 },
        "4": { font: "", size: 26, color: "#8BB42D", marginAfter: 12 },
        "5": { font: "", size: 22, color: "#888888", marginAfter: 12 },
        "6": { font: "", size: 20, color: "#333333", marginAfter: 12 }
    };
}


function loadHeadingStyles() {
    /**
     * Reads heading styles from localStorage, falling back to defaults
     * if nothing is saved.
     *
     * Returns:
     *     Object: Heading styles keyed by level (1-6).
     */

    var stored = localStorage.getItem("canvas_heading_styles");
    if (stored) {
        return JSON.parse(stored);
    }
    return getDefaultHeadingStyles();
}


function populateFontSelects() {
    /**
     * Populates all font select dropdowns in the styles modal with
     * Default, Serif, Sans-serif, Monospace, and all FONT_WHITELIST fonts.
     */

    var selects = document.querySelectorAll("#styles-customize-modal-overlay .styles-font-select");

    selects.forEach(function(select) {

        // Clear existing options
        select.innerHTML = "";

        // Default option
        var defaultOpt = document.createElement("option");
        defaultOpt.value = "";
        defaultOpt.textContent = "Default";
        select.appendChild(defaultOpt);

        // Generic font families
        var generics = [
            { value: "serif", label: "Serif" },
            { value: "sans-serif", label: "Sans-serif" },
            { value: "monospace", label: "Monospace" }
        ];

        generics.forEach(function(g) {
            var opt = document.createElement("option");
            opt.value = g.value;
            opt.textContent = g.label;
            select.appendChild(opt);
        });

        // Visual separator (disabled option)
        var sep = document.createElement("option");
        sep.disabled = true;
        sep.textContent = "──────────";
        select.appendChild(sep);

        // All FONT_WHITELIST fonts
        FONT_WHITELIST.forEach(function(slug) {
            var opt = document.createElement("option");
            opt.value = slug;
            opt.textContent = FONT_DISPLAY_NAMES[slug] || slug;
            select.appendChild(opt);
        });
    });
}


function populateStylesModal(styles) {
    /**
     * Fills the modal inputs with values from the given styles object.
     *
     * Args:
     *     styles (Object): Heading styles keyed by level (1-6).
     */

    for (var level = 1; level <= 6; level++) {
        var row = document.querySelector(".styles-grid-row[data-level='" + level + "']");
        if (!row) continue;

        var style = styles[level.toString()] || getDefaultHeadingStyles()[level.toString()];
        row.querySelector(".styles-font-select").value = style.font || "";
        row.querySelector(".styles-size-input").value = style.size;
        row.querySelector(".styles-color-input").value = style.color;
    }
}


function saveHeadingStyles() {
    /**
     * Reads the current modal inputs, saves to localStorage, and
     * re-injects the heading CSS.
     */

    var styles = {};

    for (var level = 1; level <= 6; level++) {
        var row = document.querySelector(".styles-grid-row[data-level='" + level + "']");
        if (!row) continue;

        styles[level.toString()] = {
            font: row.querySelector(".styles-font-select").value,
            size: parseInt(row.querySelector(".styles-size-input").value, 10) || 16,
            color: row.querySelector(".styles-color-input").value
        };
    }

    localStorage.setItem("canvas_heading_styles", JSON.stringify(styles));
    injectHeadingCSS(styles);
}


function resetHeadingStylesToDefaults() {
    /**
     * Clears localStorage heading styles, repopulates the modal with
     * defaults, and re-injects the default CSS.
     */

    localStorage.removeItem("canvas_heading_styles");
    var defaults = getDefaultHeadingStyles();
    populateStylesModal(defaults);
    injectHeadingCSS(defaults);
}


function injectHeadingCSS(styles) {
    /**
     * Creates or replaces a <style> tag with custom heading CSS rules
     * scoped to the Quill editor.
     *
     * Args:
     *     styles (Object): Heading styles keyed by level (1-6).
     */

    var styleId = "canvas-heading-custom-styles";
    var existing = document.getElementById(styleId);
    if (existing) {
        existing.parentNode.removeChild(existing);
    }

    var css = "";
    for (var level = 1; level <= 6; level++) {
        var s = styles[level.toString()];
        if (!s) continue;

        var selector = "#canvas-editor .ql-editor h" + level;
        var rules = [];

        if (s.color) {
            rules.push("color: " + s.color + " !important");
        }

        if (s.size) {
            rules.push("font-size: " + s.size + "px !important");
        }

        if (s.font) {

            // Look up the CSS font-family for this slug
            var fontFamily = FONT_FAMILIES[s.font] || s.font;
            rules.push("font-family: " + fontFamily + " !important");
        }

        if (s.marginAfter != null) {
            rules.push("margin-bottom: " + s.marginAfter + "pt !important");
        }

        if (rules.length > 0) {
            css += selector + " { " + rules.join("; ") + "; }\n";
        }
    }

    var tag = document.createElement("style");
    tag.id = styleId;
    tag.textContent = css;
    document.head.appendChild(tag);
}


function positionStylesCustomizeButton() {
    /**
     * Moves the gear button from its hidden location in the document
     * into the Quill toolbar, right next to the Styles (header) dropdown.
     */

    var btn = document.getElementById("styles-customize-btn");
    if (!btn) return;

    // Find the header picker's parent .ql-formats group
    var headerPicker = document.querySelector("#canvas-editor-wrapper .ql-toolbar .ql-header");
    if (!headerPicker) return;

    var formatsGroup = headerPicker.closest(".ql-formats");
    if (!formatsGroup) return;

    // Show the button and append it to the same group
    btn.style.display = "";
    formatsGroup.appendChild(btn);
}


function positionFontSizeInput() {
    /**
     * Moves the custom font size input from its hidden location into the
     * Quill toolbar, in the same .ql-formats group as the Fonts dropdown.
     */

    var widget = document.getElementById("custom-font-size");
    if (!widget) return;

    // Find the font picker's parent .ql-formats group
    var fontPicker = document.querySelector("#canvas-editor-wrapper .ql-toolbar .ql-font");
    if (!fontPicker) return;

    var formatsGroup = fontPicker.closest(".ql-formats");
    if (!formatsGroup) return;

    // Show the widget and append it to the same group
    widget.style.display = "";
    formatsGroup.appendChild(widget);
}


function bindFontSizeInput() {
    /**
     * Binds event handlers for the custom font size input: typing a value
     * and pressing Enter applies it, the dropdown shows presets, and Quill
     * selection-change keeps the display in sync.
     */

    var input = document.querySelector("#custom-font-size .font-size-value");
    var toggle = document.querySelector("#custom-font-size .font-size-toggle");
    var presets = document.querySelector("#custom-font-size .font-size-presets");
    if (!input || !toggle || !presets) return;

    // Apply typed size on Enter
    input.addEventListener("keydown", function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            var val = parseInt(input.value, 10);
            if (val && val > 0) {
                quill.format("size", val + "px");
            } else {

                // Empty or invalid clears the size
                quill.format("size", false);
            }
            quill.focus();
        }
    });

    // Select all text on focus for easy overtyping
    input.addEventListener("focus", function() {
        input.select();
    });

    // Toggle preset dropdown
    toggle.addEventListener("click", function(e) {
        e.stopPropagation();
        presets.classList.toggle("visible");
    });

    // Apply preset size on click
    presets.addEventListener("click", function(e) {
        var option = e.target.closest(".font-size-option");
        if (!option) return;

        var size = option.getAttribute("data-size");
        quill.format("size", size + "px");
        input.value = size;
        presets.classList.remove("visible");
        quill.focus();
    });

    // Close presets when clicking outside
    document.addEventListener("mousedown", function(e) {
        if (!e.target.closest("#custom-font-size")) {
            presets.classList.remove("visible");
        }
    });

    // Sync input display when cursor moves or selection changes
    quill.on("selection-change", function(range) {
        if (!range) return;

        var format = quill.getFormat(range);
        if (format.size) {

            // Strip "px" suffix for display
            input.value = parseInt(format.size, 10) || "";
        } else {
            input.value = "";
        }
    });
}


function loadAndApplyHeadingStyles() {
    /**
     * Reads saved heading styles from localStorage and injects the CSS.
     * Called on page load so styles apply immediately.
     */

    var styles = loadHeadingStyles();
    injectHeadingCSS(styles);
}


// ========================================================================
//   Custom Spacing Modal
// ========================================================================

function positionSpacingButton() {
    /**
     * Moves the custom spacing button from its hidden location into the
     * Quill toolbar, in the same .ql-formats group as the line height picker.
     */

    var btn = document.getElementById("spacing-btn");
    if (!btn) return;

    // Find the line height picker's parent .ql-formats group
    var lineHeightPicker = document.querySelector("#canvas-editor-wrapper .ql-toolbar .ql-lineHeight");
    if (!lineHeightPicker) return;

    var formatsGroup = lineHeightPicker.closest(".ql-formats");
    if (!formatsGroup) return;

    // Show the button and append it to the same group
    btn.style.display = "";
    formatsGroup.appendChild(btn);
}


function bindSpacingModal() {
    /**
     * Binds all event handlers for the custom spacing modal: open, close,
     * apply formatting, and pre-populate from current block format.
     */

    var overlay = $("#spacing-modal-overlay");

    // Open modal when spacing button is clicked
    $(document).on("click", "#spacing-btn", function() {

        // Pre-populate from current block format
        var format = quill.getFormat();

        // Line spacing: strip any unit, show raw number
        var lineVal = format.lineHeight ? parseFloat(format.lineHeight) : "";
        $("#spacing-line").val(lineVal || "");

        // Before/after: parse pt value
        var beforeVal = format.marginBefore ? parseFloat(format.marginBefore) : "";
        var afterVal = format.marginAfter ? parseFloat(format.marginAfter) : "";
        $("#spacing-before").val(beforeVal || "");
        $("#spacing-after").val(afterVal || "");

        overlay.addClass("visible");
    });

    // Close via X button
    $("#close-spacing-modal").on("click", function() {
        overlay.removeClass("visible");
    });

    // Close via Cancel button
    $("#cancel-spacing").on("click", function() {
        overlay.removeClass("visible");
    });

    // Close via overlay click
    overlay.on("click", function(e) {
        if ($(e.target).is("#spacing-modal-overlay")) {
            overlay.removeClass("visible");
        }
    });

    // Close on Escape key
    $(document).on("keydown", function(e) {
        if (e.key === "Escape") {
            if (overlay.hasClass("visible")) {
                overlay.removeClass("visible");
            }
        }
    });

    // Apply button
    $("#apply-spacing").on("click", function() {
        var lineVal = $("#spacing-line").val();
        var beforeVal = $("#spacing-before").val();
        var afterVal = $("#spacing-after").val();

        // Apply line spacing (unitless multiplier)
        if (lineVal && parseFloat(lineVal) > 0) {
            quill.format("lineHeight", lineVal);
        } else {
            quill.format("lineHeight", false);
        }

        // Apply paragraph spacing before (pts)
        if (beforeVal && parseFloat(beforeVal) > 0) {
            quill.format("marginBefore", beforeVal + "pt");
        } else {
            quill.format("marginBefore", false);
        }

        // Apply paragraph spacing after (pts)
        if (afterVal && parseFloat(afterVal) > 0) {
            quill.format("marginAfter", afterVal + "pt");
        } else {
            quill.format("marginAfter", false);
        }

        overlay.removeClass("visible");
        quill.focus();
    });
}


// ========================================================================
//   Heading Styles Customization Modal
// ========================================================================

function bindStylesCustomizeModal() {
    /**
     * Binds all event handlers for the heading styles customization
     * modal: open, close, save, and reset to defaults.
     */

    // Populate font select dropdowns
    populateFontSelects();

    // Open modal when gear button is clicked
    $(document).on("click", "#styles-customize-btn", function() {
        var styles = loadHeadingStyles();
        populateStylesModal(styles);
        $("#styles-customize-modal-overlay").addClass("visible");
    });

    // Close via X button
    $("#close-styles-customize-modal").on("click", function() {
        $("#styles-customize-modal-overlay").removeClass("visible");
    });

    // Close via overlay click
    $("#styles-customize-modal-overlay").on("click", function(e) {
        if ($(e.target).is("#styles-customize-modal-overlay")) {
            $(this).removeClass("visible");
        }
    });

    // Close on Escape key
    $(document).on("keydown", function(e) {
        if (e.key === "Escape") {
            if ($("#styles-customize-modal-overlay").hasClass("visible")) {
                $("#styles-customize-modal-overlay").removeClass("visible");
            }
        }
    });

    // Save button
    $("#save-styles").on("click", function() {
        saveHeadingStyles();
        $("#styles-customize-modal-overlay").removeClass("visible");
    });

    // Reset to Defaults button
    $("#reset-styles-defaults").on("click", function() {
        resetHeadingStylesToDefaults();
    });
}


function initQuillEditor() {
    /**
     * Initializes the Quill rich text editor with a toolbar matching
     * the user's requested formatting options: font picker, color picker,
     * headings, font size, lists, and paragraph alignment.
     */

    // Register style attributors so Quill preserves inline formatting
    registerStyleAttributors();

    // Register font whitelist for the font picker
    registerFontWhitelist();

    var toolbarOptions = [
        [{ "header": [1, 2, 3, 4, 5, 6, false] }],
        [{ "font": FONT_WHITELIST }],
        ["bold", "italic", "underline", "strike"],
        [{ "color": [] }, { "background": [] }],
        ["clean", "link"],
        [{ "list": "ordered" }, { "list": "bullet" }],
        [{ "align": [] }],
        [{ "indent": "-1" }, { "indent": "+1" }],
        [{ "lineHeight": ["1", "1.15", "1.5", "1.75", "2", "2.5", "3", false] }]
    ];

    quill = new Quill("#canvas-editor", {
        theme: "snow",
        placeholder: "Your audit document starts here. Use the Guide tab to review each step, then click \"Add to Canvas\" to build your report.",
        modules: {
            toolbar: toolbarOptions
        }
    });

    // Override font picker default label text via inline style
    var fontPickerStyle = document.createElement("style");
    fontPickerStyle.textContent = "#canvas-editor-wrapper .ql-snow .ql-picker.ql-font > .ql-picker-label::before { content: \"Fonts\" !important; }";
    document.head.appendChild(fontPickerStyle);

    // Load saved content and auto-save on changes
    initCanvasPersistence();

    // Surface recently used fonts at the top of the font picker
    setupRecentFonts();

    // Position the gear button next to the Styles dropdown
    positionStylesCustomizeButton();

    // Position the custom font size input next to the Fonts dropdown
    positionFontSizeInput();

    // Sync font size display when cursor moves
    bindFontSizeInput();

    // Apply saved heading styles from localStorage
    loadAndApplyHeadingStyles();

    // Position the custom spacing button next to the line height picker
    positionSpacingButton();
}


// ========================================================================
//   Quill Editor — Content Persistence (localStorage)
// ========================================================================

function getCanvasStorageKey() {
    /**
     * Returns the localStorage key for the canvas content. Uses a single
     * global key so content persists across all checks (additive canvas).
     *
     * Returns:
     *     string: The storage key "canvas_content".
     */

    return "canvas_content";
}


function initCanvasPersistence() {
    /**
     * Loads any previously saved canvas content from localStorage and
     * auto-saves editor changes on a 500ms debounce.
     */

    var storageKey = getCanvasStorageKey();

    // Load saved content if it exists
    var saved = localStorage.getItem(storageKey);
    if (saved) {
        var delta = JSON.parse(saved);
        quill.setContents(delta);
    }

    // Auto-save on every text change (debounced to 500ms)
    var saveTimer;
    quill.on("text-change", function() {
        clearTimeout(saveTimer);
        saveTimer = setTimeout(function() {
            var contents = quill.getContents();
            localStorage.setItem(storageKey, JSON.stringify(contents));

            // Clear hierarchy tracking when canvas is emptied
            if (quill.getLength() <= 1) {
                localStorage.removeItem("canvas_last_hierarchy");
            }
        }, 500);
    });
}


// ========================================================================
//   Top-Level Tab Switching (Guide / Canvas)
// ========================================================================

function bindTabSwitching() {
    /**
     * Binds click handlers to the Guide and Canvas tab buttons.
     * Updates the URL path segment for permalink support so
     * refreshing the page preserves the active tab.
     */

    $(".canvas-tab").on("click", function() {
        var targetTab = $(this).data("tab");
        switchToTab(targetTab);
    });
}


function switchToTab(targetTab) {
    /**
     * Activates the specified tab (guide or canvas) and updates the
     * URL path for permalink support.
     *
     * Args:
     *     targetTab (string): "guide" or "canvas"
     */

    // Update active tab button
    $(".canvas-tab").removeClass("active");
    $(".canvas-tab[data-tab='" + targetTab + "']").addClass("active");

    // Show the target panel, hide others
    $(".tab-panel").removeClass("active");
    $("#panel-" + targetTab).addClass("active");

    // Update URL path to reflect the active tab
    var pathParts = window.location.pathname.replace(/\/$/, "").split("/");
    var validSteps = ["educate", "investigate", "generate", "canvas"];

    // Determine the new last segment
    var newSegment;
    if (targetTab === "canvas") {
        newSegment = "canvas";
    } else {

        // Switching to Guide: use the currently active -ate step pill
        var activeStep = $(".ate-step-pill.active").data("step");
        newSegment = activeStep || "educate";
    }

    // Replace the last segment if it's a known step, otherwise append
    if (validSteps.indexOf(pathParts[pathParts.length - 1]) !== -1) {
        pathParts[pathParts.length - 1] = newSegment;
    } else {
        pathParts.push(newSegment);
    }

    var newPath = pathParts.join("/") + "/";
    history.replaceState(null, null, newPath);
}


// ========================================================================
//   -ate Step Navigation
// ========================================================================

function bindStepNavigation() {
    /**
     * Binds click handlers to the -ate step pills (Educate, Investigate,
     * Generate). Shows the content panel for the selected step, hides
     * the rest, and updates the URL path for permalink support.
     */

    $(".ate-step-pill").on("click", function() {
        var targetStep = $(this).data("step");

        // Update active pill
        $(".ate-step-pill").removeClass("active");
        $(this).addClass("active");

        // Show target step panel, hide others
        $(".ate-step-panel").removeClass("active");
        $("#step-" + targetStep).addClass("active");

        // Update URL path to reflect the active step
        var pathParts = window.location.pathname.replace(/\/$/, "").split("/");
        var validSteps = ["educate", "investigate", "generate"];

        // Replace the last segment if it's a step, otherwise append
        if (validSteps.indexOf(pathParts[pathParts.length - 1]) !== -1) {
            pathParts[pathParts.length - 1] = targetStep;
        } else {
            pathParts.push(targetStep);
        }

        var newPath = pathParts.join("/") + "/";
        history.replaceState(null, null, newPath);
    });
}


// ========================================================================
//   Investigate Tool Checkboxes
// ========================================================================

function bindToolCheckboxes() {
    /**
     * Binds change handlers to the investigate tool checkboxes.
     * Shows or hides each tool's step panel based on its checked state.
     * Multiple tools can be visible at once.
     */

    $(".tool-checkbox").on("change", function() {
        var toolKey = $(this).val();
        var isChecked = $(this).is(":checked");
        var toolSection = $(this).closest(".tool-section");
        var panel = toolSection.find(".tool-panel[data-tool='" + toolKey + "']");

        if (isChecked) {
            panel.addClass("active");
        } else {
            panel.removeClass("active");
        }

        /* Sync the 'Show All' checkbox with individual checkbox states */
        syncShowAllCheckbox(toolSection);
    });

    /* 'Show All' checkbox: checks/unchecks every tool checkbox */
    $(".tool-checkbox-all").on("change", function() {
        var isChecked = $(this).is(":checked");
        var toolSection = $(this).closest(".tool-section");

        toolSection.find(".tool-checkbox").each(function() {
            $(this).prop("checked", isChecked);
            var toolKey = $(this).val();
            var panel = toolSection.find(".tool-panel[data-tool='" + toolKey + "']");

            if (isChecked) {
                panel.addClass("active");
            } else {
                panel.removeClass("active");
            }
        });
    });

    /* Sync 'Show All' on initial load so the first click toggles correctly
       when the template pre-checks every tool (the free-tools-on-by-default
       state can leave Show All visually unchecked otherwise). */
    $(".tool-section").each(function() {
        syncShowAllCheckbox($(this));
    });
}


/**
 * Syncs the 'Show All' checkbox state with the individual tool checkboxes.
 * Checked when all tools are checked, unchecked otherwise.
 */
function syncShowAllCheckbox(toolSection) {
    var allCheckboxes = toolSection.find(".tool-checkbox");
    var allChecked = allCheckboxes.length > 0 && allCheckboxes.filter(":checked").length === allCheckboxes.length;
    toolSection.find(".tool-checkbox-all").prop("checked", allChecked);
}


// ========================================================================
//   Add to Canvas
// ========================================================================

function bindAddToCanvas() {
    /**
     * Binds click handlers to the "Add to Canvas" buttons in each -ate
     * step section. Extracts the content from the current step, bumps
     * heading levels down by 2, adds hierarchy headers as needed, and
     * inserts the result into the Quill editor.
     */

    $(".add-to-canvas-btn").on("click", function() {
        var section = $(this).data("section");
        var content = extractSectionContent(section);

        if (content) {

            // Build the full HTML, adding a section heading for tabs that
            // don't have their own headings in the content
            var heading = getSectionHeading(section);
            var fullHtml = heading ? "<h2>" + heading + "</h2>" + content : content;

            // Insert with hierarchy headers and heading-level bumping
            insertWithHierarchy(fullHtml);
        }
    });
}


function getSectionHeading(section) {
    /**
     * Returns a display heading for the given -ate section.
     *
     * Args:
     *     section (string): Section identifier (educate, investigate, etc.)
     *
     * Returns:
     *     string: Human-readable heading for the section.
     */

    var headings = {
        "educate": "Background"
    };

    return headings[section] || null;
}


function extractSectionContent(section) {
    /**
     * Extracts HTML content from the specified -ate section panel,
     * preserving headings, lists, bold, and other formatting. Captures
     * computed styles (color, font-size, line-height) as inline styles
     * so Quill can preserve them during paste.
     *
     * Args:
     *     section (string): Section identifier (educate, investigate, etc.)
     *
     * Returns:
     *     string: HTML content with inline styles, ready for Quill insertion.
     */

    var html = "";

    if (section === "educate") {

        // Capture the base explanation with computed styles baked in
        var contentEl = document.getElementById("educate-content");
        if (contentEl) {
            html += captureStyledHTML(contentEl);
        }

    } else if (section === "generate") {

        // Capture the entire Generate panel content with computed styles.
        // Clone the panel, remove the footer button, and capture everything.
        var generatePanel = document.querySelector("#step-generate .ate-panel-inner");
        if (generatePanel) {
            var clone = generatePanel.cloneNode(true);

            // Remove the Add to Canvas footer from the clone
            var footer = clone.querySelector(".ate-footer");
            if (footer) {
                footer.parentNode.removeChild(footer);
            }

            // Remove HTML comment nodes from the clone
            var walker = document.createTreeWalker(clone, NodeFilter.SHOW_COMMENT);
            var comments = [];
            while (walker.nextNode()) {
                comments.push(walker.currentNode);
            }
            comments.forEach(function(c) { c.parentNode.removeChild(c); });

            // Inject computed styles from the live DOM
            var originals = generatePanel.querySelectorAll("*");
            var clones = clone.querySelectorAll("*");
            for (var i = 0; i < originals.length && i < clones.length; i++) {
                injectComputedStyles(originals[i], clones[i]);
            }

            // Convert the inline impact-gauge SVG to a data-URI <img>. Quill
            // strips inline <svg> on paste (keeping only its text), but embeds
            // <img> data-URIs natively, so this is what carries the impact
            // bars into the canvas and the exported deliverable. Done after
            // the computed-style loop so the node swap doesn't misalign the
            // original/clone index pairing above.
            inlineSvgToImage(clone);

            html += clone.innerHTML;
        }

    }

    return html.trim();
}


function inlineSvgToImage(rootEl) {
    /**
     * Replaces inline impact-gauge <svg> nodes with <img> elements whose src
     * is a data-URI of the serialized SVG. Quill's sanitizer drops inline
     * <svg> on dangerouslyPasteHTML (keeping only the title text), but it
     * embeds <img> data-URIs natively. Converting here is what lets the
     * impact bars survive into the canvas and the Word/PDF export.
     *
     * Args:
     *     rootEl (Element): Container whose descendant gauge SVGs are converted.
     *
     * Returns:
     *     void
     */

    var svgs = rootEl.querySelectorAll("svg.impact-gauge");
    var serializer = new XMLSerializer();

    for (var i = 0; i < svgs.length; i++) {
        var svg = svgs[i];

        // The serialized SVG keeps its own width/height, so the data-URI
        // image renders at the gauge's natural 28x20 even if Quill drops
        // the <img> sizing attributes
        var alt = svg.getAttribute("aria-label") || "Impact gauge";
        var svgStr = serializer.serializeToString(svg);
        var src = "data:image/svg+xml," + encodeURIComponent(svgStr);

        var img = document.createElement("img");
        img.setAttribute("src", src);
        img.setAttribute("alt", alt);

        svg.parentNode.replaceChild(img, svg);
    }
}


// ========================================================================
//   Canvas Hierarchy Headers
// ========================================================================

function bumpHeadingLevels(html, levels) {
    /**
     * Shifts all heading tags (H1-H6) down by the specified number of levels.
     * Processes from H6 downward to avoid double-replacement. Caps at H6.
     *
     * Args:
     *     html (string): HTML string containing heading tags.
     *     levels (int): Number of levels to bump down (e.g., 2 means H2→H4).
     *
     * Returns:
     *     string: HTML with heading levels shifted.
     */

    // Process from H6 down to H1 to avoid double-replacement
    for (var i = 6; i >= 1; i--) {
        var newLevel = Math.min(i + levels, 6);
        var openTag = new RegExp("<h" + i + "(\\s|>)", "gi");
        var closeTag = new RegExp("</h" + i + ">", "gi");
        html = html.replace(openTag, "<h" + newLevel + "$1");
        html = html.replace(closeTag, "</h" + newLevel + ">");
    }

    return html;
}


function isCanvasEmpty() {
    /**
     * Returns true if the Quill editor has no real content.
     * Quill always has at least 1 character (a trailing newline).
     *
     * Returns:
     *     boolean: True if the canvas is empty.
     */

    return !quill || quill.getLength() <= 1;
}


function getPageHierarchy() {
    /**
     * Reads the current page's category, subcategory, and check title
     * from data attributes on the canvas panel.
     *
     * Returns:
     *     Object: { category, subcategory, check }
     */

    var panel = $("#panel-canvas");
    return {
        category: panel.data("category") || "",
        subcategory: panel.data("subcategory") || "",
        check: panel.data("check-title") || ""
    };
}


function getLastInsertedHierarchy() {
    /**
     * Reads the last-inserted hierarchy from localStorage.
     *
     * Returns:
     *     Object|null: { category, subcategory, check } or null if none stored.
     */

    var stored = localStorage.getItem("canvas_last_hierarchy");
    return stored ? JSON.parse(stored) : null;
}


function saveLastInsertedHierarchy(hierarchy) {
    /**
     * Saves the current hierarchy to localStorage so subsequent insertions
     * can determine which headers to add.
     *
     * Args:
     *     hierarchy (Object): { category, subcategory, check }
     */

    localStorage.setItem("canvas_last_hierarchy", JSON.stringify(hierarchy));
}


function buildHierarchyHTML(current, last) {
    /**
     * Compares the current page hierarchy with the last-inserted hierarchy
     * and returns the HTML for any new header levels needed.
     *
     * Args:
     *     current (Object): { category, subcategory, check } from the page.
     *     last (Object|null): { category, subcategory, check } from localStorage.
     *
     * Returns:
     *     string: HTML string with H1/H2/H3 headers as needed, or empty string.
     */

    var html = "";

    // First insertion (canvas was empty, no prior hierarchy)
    if (!last) {
        html += "<h1>" + current.category + "</h1>";
        html += "<h2>" + current.subcategory + "</h2>";
        html += "<h3>" + current.check + "</h3>";
        return html;
    }

    // Category changed: full hierarchy
    if (current.category !== last.category) {
        html += "<h1>" + current.category + "</h1>";
        html += "<h2>" + current.subcategory + "</h2>";
        html += "<h3>" + current.check + "</h3>";
        return html;
    }

    // Same category, subcategory changed
    if (current.subcategory !== last.subcategory) {
        html += "<h2>" + current.subcategory + "</h2>";
        html += "<h3>" + current.check + "</h3>";
        return html;
    }

    // Same category + subcategory, check changed
    if (current.check !== last.check) {
        html += "<h3>" + current.check + "</h3>";
        return html;
    }

    // Everything matches (same check, adding more content)
    return "";
}


function insertWithHierarchy(contentHtml) {
    /**
     * Inserts content into the Quill editor with hierarchy headers and
     * heading-level bumping. Shared by both the Add to Canvas button
     * and the selection popover.
     *
     * Args:
     *     contentHtml (string): Raw HTML content to insert.
     */

    if (!contentHtml || !quill) {
        return;
    }

    // Bump all headings in the content down 2 levels (H2→H4, H3→H5, etc.)
    var bumpedHtml = bumpHeadingLevels(contentHtml, 2);

    // Build hierarchy prefix based on what's changed since last insertion
    var current = getPageHierarchy();
    var last = isCanvasEmpty() ? null : getLastInsertedHierarchy();
    var hierarchyHtml = buildHierarchyHTML(current, last);

    // Combine hierarchy headers + bumped content
    var fullHtml = hierarchyHtml + bumpedHtml;

    // Get the current editor length
    var currentLength = quill.getLength();

    // Add a blank line separator if there is existing content
    if (currentLength > 1) {
        quill.insertText(currentLength - 1, "\n");
        currentLength = quill.getLength();
    }

    // Insert as HTML to preserve headings, lists, and formatting
    quill.clipboard.dangerouslyPasteHTML(currentLength - 1, fullHtml);

    // Clean up empty heading blocks that Quill creates when the separator
    // newline inherits a heading format from adjacent content
    $("#canvas-editor .ql-editor").children("h1, h2, h3, h4, h5, h6").each(function() {
        var text = $(this).text().trim();
        if (!text) {
            $(this).remove();
        }
    });

    // Save current hierarchy for next insertion
    saveLastInsertedHierarchy(current);

    // Switch to the Canvas tab to show the result
    switchToTab("canvas");

    // Scroll to the top of the editor
    $("html, body").animate({
        scrollTop: $("#panel-canvas").offset().top - 100
    }, 300);
}


// ========================================================================
//   Styled HTML Capture for Canvas Insertion
// ========================================================================

function captureStyledHTML(sourceEl) {
    /**
     * Clones a DOM element and bakes computed styles (color, font-size,
     * font-weight, line-height) into inline styles on each child element.
     * Returns the clone's innerHTML so Quill can preserve the visual
     * formatting during dangerouslyPasteHTML().
     *
     * Args:
     *     sourceEl (Element): The live DOM element to capture from.
     *
     * Returns:
     *     string: HTML string with inline styles.
     */

    var clone = sourceEl.cloneNode(true);

    // Walk both trees in parallel to read computed styles from the
    // originals and inject them into the clones
    var originals = sourceEl.querySelectorAll("*");
    var clones = clone.querySelectorAll("*");

    for (var i = 0; i < originals.length; i++) {
        injectComputedStyles(originals[i], clones[i]);
    }

    return clone.innerHTML;
}


function captureStyledElement(sourceEl) {
    /**
     * Captures a single element (including its children) as an HTML string
     * with computed styles baked in as inline styles.
     *
     * Args:
     *     sourceEl (Element): The live DOM element to capture.
     *
     * Returns:
     *     string: The element's outerHTML with inline styles.
     */

    var clone = sourceEl.cloneNode(true);

    // Apply styles to the root clone element
    injectComputedStyles(sourceEl, clone);

    // Walk children
    var originals = sourceEl.querySelectorAll("*");
    var clones = clone.querySelectorAll("*");

    for (var i = 0; i < originals.length; i++) {
        injectComputedStyles(originals[i], clones[i]);
    }

    return clone.outerHTML;
}


function injectComputedStyles(sourceEl, targetEl) {
    /**
     * Reads computed styles from a live DOM element and applies key
     * formatting properties as inline styles on a cloned element.
     * Only injects properties that Quill can preserve: color,
     * font-size (for headings), and font-weight.
     *
     * Args:
     *     sourceEl (Element): The original element in the live DOM.
     *     targetEl (Element): The cloned element to receive inline styles.
     */

    // Skip text nodes and non-element nodes
    if (sourceEl.nodeType !== 1) return;

    var computed = window.getComputedStyle(sourceEl);
    var tag = sourceEl.tagName.toLowerCase();

    // Color (skip default body text color)
    var color = computed.color;
    if (color && color !== "rgb(51, 51, 51)" && color !== "rgb(0, 0, 0)") {
        targetEl.style.color = color;
    }

    // Font size for headings (Quill defaults are too small)
    if (/^h[1-6]$/.test(tag)) {
        targetEl.style.fontSize = computed.fontSize;
    }

    // Line height (preserve spacing)
    var lineHeight = computed.lineHeight;
    if (lineHeight && lineHeight !== "normal") {
        targetEl.style.lineHeight = lineHeight;
    }
}


function captureSelectionHTML(range) {
    /**
     * Converts a browser Selection Range into an HTML string with computed
     * styles baked in as inline styles. Walks the common ancestor container,
     * finds elements that overlap the selection, reads their computed styles,
     * and injects them into a cloned fragment.
     *
     * Args:
     *     range (Range): The browser selection range.
     *
     * Returns:
     *     string: HTML string with inline styles for Quill insertion.
     */

    var fragment = range.cloneContents();
    var tempDiv = document.createElement("div");
    tempDiv.appendChild(fragment);

    // The cloned fragment has the DOM structure but no computed styles.
    // Walk the original container's elements to find matching originals.
    var container = range.commonAncestorContainer;

    // If the container is a text node, use its parent
    if (container.nodeType === 3) {
        container = container.parentElement;
    }

    // Get all elements in the original container
    var liveElements = container.querySelectorAll("*");
    var cloneElements = tempDiv.querySelectorAll("*");

    // Build a map of live elements by their text content + tag for matching
    cloneElements.forEach(function(cloneEl) {
        var tag = cloneEl.tagName.toLowerCase();

        // Find the matching live element by tag + trimmed text content
        for (var i = 0; i < liveElements.length; i++) {
            var liveEl = liveElements[i];
            if (liveEl.tagName.toLowerCase() === tag &&
                liveEl.textContent.trim() === cloneEl.textContent.trim() &&
                !liveEl._matched) {
                injectComputedStyles(liveEl, cloneEl);
                liveEl._matched = true;
                break;
            }
        }
    });

    // Clean up the matching flags
    for (var i = 0; i < liveElements.length; i++) {
        delete liveElements[i]._matched;
    }

    return tempDiv.innerHTML;
}


// ========================================================================
//   Contextual Text Selection — Kindle-Style Popover
// ========================================================================

function bindTextSelection() {
    /**
     * Listens for text selection (mouseup) within the Guide and Canvas
     * tab panels. When the user selects text, a floating popover appears
     * near the selection with contextual actions (Look up, Rephrase,
     * Report as inaccurate). Design only; no backend logic.
     */

    var popover = $("#selection-popover");
    var submenu = $("#rephrase-submenu");

    // Show the popover when text is selected inside content areas
    $(document).on("mouseup", function(e) {

        // Ignore mouseup events inside modals
        if ($(e.target).closest(".modal-overlay").length) {
            return;
        }

        // Small delay to let the browser finalize the selection
        setTimeout(function() {
            var selection = window.getSelection();
            var selectedText = selection.toString().trim();

            // Only show if there is actual selected text
            if (!selectedText) {
                hidePopover();
                return;
            }

            var range = selection.getRangeAt(0);
            var container = range.commonAncestorContainer;

            // Walk up to find the nearest element node
            var el = container.nodeType === 3 ? container.parentElement : container;

            // Determine which page context the selection is in:
            //   - guide: inside the canvas page's Guide panel
            //   - canvas: inside the canvas page's Canvas editor
            //   - overview: inside an editable element on the category page
            var inGuide = $(el).closest("#panel-guide").length > 0;
            var inCanvas = $(el).closest("#panel-canvas").length > 0;
            var inEditable = $(el).closest("[data-content-path]").length > 0;

            // Selection must land inside an editable region on a recognized
            // page; otherwise hide the popover and bail.
            if (!inGuide && !inCanvas && !inEditable) {
                hidePopover();
                return;
            }

            var context;
            if (inCanvas) {
                context = "canvas";
            } else if (inGuide) {
                context = "guide";
            } else {
                context = "overview";
            }

            popover.data("context", context);
            popover.data("selected-text", selectedText);

            // Store the selected HTML with computed styles baked in.
            // Walk the selected range's DOM nodes, read their computed
            // styles from the live document, and inject as inline styles
            // so Quill preserves the visual formatting.
            var styledHtml = captureSelectionHTML(range);
            popover.data("selected-html", styledHtml);

            // Show/hide popover buttons based on which context we're in.
            // Add-to-canvas and Rephrase only apply when the canvas editor
            // is present on the page; Report is only meaningful on Guide
            // and overview contexts.
            var canvasOnly = popover.find(
                "[data-action='add-to-canvas'], [data-action='rephrase']"
            );
            var reportBtn = popover.find("[data-action='report']");

            if (context === "canvas") {
                reportBtn.hide();
                canvasOnly.show();
            } else if (context === "overview") {

                // Overview pages have no canvas editor — hide the canvas
                // and rephrase actions, keep Report as inaccurate visible
                canvasOnly.hide();
                reportBtn.show();
            } else {
                reportBtn.show();
                canvasOnly.show();
            }

            // Show "Update Heading X" when selection is inside a heading on canvas
            var updateBtn = $("#popover-update-heading");
            var updateDivider = $("#popover-update-heading-divider");

            if (context === "canvas") {
                var headingEl = $(el).closest("h1, h2, h3, h4, h5, h6", "#canvas-editor .ql-editor");
                if (headingEl.length) {
                    var level = parseInt(headingEl.prop("tagName").substring(1), 10);
                    updateBtn.find("span").text("Update Heading " + level);
                    updateBtn.data("heading-level", level);
                    updateBtn.show();
                    updateDivider.show();
                } else {
                    updateBtn.hide();
                    updateDivider.hide();
                }
            } else {
                updateBtn.hide();
                updateDivider.hide();
            }

            // Position the popover above the selection
            positionPopover(range);
        }, 10);
    });

    // Hide popover when clicking outside of it (but not inside modals)
    $(document).on("mousedown", function(e) {
        if (!$(e.target).closest(".selection-popover, .rephrase-submenu, .modal-overlay").length) {
            hidePopover();
        }
    });

    // Handle popover action clicks
    popover.on("click", ".popover-action", function(e) {
        e.stopPropagation();
        var action = $(this).data("action");

        if (action === "lookup") {
            handleLookup();
        } else if (action === "rephrase") {
            toggleRephraseSubmenu();
        } else if (action === "add-to-canvas") {
            handleAddSelectionToCanvas();
        } else if (action === "report") {
            handleReport();
        } else if (action === "update-heading") {
            handleUpdateHeading();
        }
    });

    // Handle rephrase submenu option clicks
    submenu.on("click", ".submenu-option", function(e) {
        e.stopPropagation();
        var rephraseType = $(this).data("rephrase");
        handleRephrase(rephraseType);
    });

    // ====================================================================
    //   Group hover (User / Editorial) — show/hide submenus
    // ====================================================================
    // Hovering a group trigger opens its submenu; moving the mouse to a
    // sibling group switches submenus. A short delay before hiding gives
    // the user time to move into the submenu without it collapsing under
    // them. Pure CSS :hover doesn't cut it because we want one submenu
    // open at a time and need to allow movement across the gap from
    // trigger to submenu.

    var submenuHideTimer = null;

    popover.on("mouseenter", ".popover-group", function() {
        clearTimeout(submenuHideTimer);
        var $group = $(this);
        $group.siblings(".popover-group").removeClass("submenu-open");
        $group.addClass("submenu-open");
    });

    popover.on("mouseleave", ".popover-group", function() {
        var $group = $(this);
        submenuHideTimer = setTimeout(function() {
            $group.removeClass("submenu-open");
        }, 250);
    });
}


function positionPopover(range) {
    /**
     * Positions the selection popover above the selected text range.
     * Centers the popover horizontally on the selection, then clamps it
     * to the bounds of the panel/column that contains the selection so
     * the popover never overflows out of its content container.
     *
     * Args:
     *     range (Range): The DOM Range object for the current selection.
     */

    var popover = $("#selection-popover");
    var rect = range.getBoundingClientRect();
    var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    var scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

    // Use the popover's actual rendered width (visible buttons vary by
    // page context). Make it visible first so outerWidth() reads true.
    popover.css({ visibility: "hidden" }).addClass("visible");
    var popoverWidth = popover.outerWidth() || 380;
    popover.css({ visibility: "" });

    // Find the panel/column that bounds where the popover may render.
    // Falls back to the viewport when no recognized container is found.
    var container = range.commonAncestorContainer;
    var el = container.nodeType === 3 ? container.parentElement : container;
    var $container = $(el).closest(".subcat-tab-panel, .category-panel, #panel-canvas, #panel-guide");

    var minLeft, maxLeft;
    var padding = 8;
    if ($container.length) {
        var crect = $container[0].getBoundingClientRect();
        minLeft = crect.left + scrollLeft + padding;
        maxLeft = crect.right + scrollLeft - popoverWidth - padding;
    } else {
        minLeft = scrollLeft + padding;
        maxLeft = scrollLeft + $(window).width() - popoverWidth - padding;
    }

    // Calculate position: center above the selection
    var top = rect.top + scrollTop - 52;
    var left = rect.left + scrollLeft + (rect.width / 2) - (popoverWidth / 2);

    // Clamp inside container (or viewport fallback). If the popover is
    // wider than the container, pin to its left edge so the right edge
    // is the only side that can spill.
    if (maxLeft < minLeft) {
        left = minLeft;
    } else if (left < minLeft) {
        left = minLeft;
    } else if (left > maxLeft) {
        left = maxLeft;
    }

    popover.css({
        top: top + "px",
        left: left + "px"
    });

    popover.addClass("visible");
}


function hidePopover() {
    /**
     * Hides the selection popover, the rephrase sub-submenu, and any
     * open User/Editorial group submenus.
     */

    $("#selection-popover").removeClass("visible");
    $("#rephrase-submenu").removeClass("visible");
    $(".popover-group").removeClass("submenu-open");
}


function toggleRephraseSubmenu() {
    /**
     * Shows or hides the rephrase submenu positioned to the right of
     * the Rephrase button in the popover. If the submenu would overflow
     * the viewport, it is positioned to the left instead.
     */

    var popover = $("#selection-popover");
    var submenu = $("#rephrase-submenu");
    var rephraseBtn = popover.find("[data-action='rephrase']");

    // Toggle visibility
    if (submenu.hasClass("visible")) {
        submenu.removeClass("visible");
        return;
    }

    // Position the submenu next to the popover
    var popoverOffset = popover.offset();
    var popoverWidth = popover.outerWidth();
    var submenuWidth = 240;
    var viewportWidth = $(window).width();

    // Default: position to the right of the popover
    var top = popoverOffset.top;
    var left = popoverOffset.left + popoverWidth + 4;

    // If it overflows right, position to the left
    if (left + submenuWidth > viewportWidth - 8) {
        left = popoverOffset.left - submenuWidth - 4;
    }

    submenu.css({
        top: top + "px",
        left: left + "px"
    });

    submenu.addClass("visible");
}


// ========================================================================
//   Contextual Actions — Look Up, Rephrase, Report
// ========================================================================

function handleUpdateHeading() {
    /**
     * Captures the current heading's formatting (font, size, color) and
     * saves it as the style for that heading level. All headings of the
     * same level update instantly via injectHeadingCSS().
     */

    var btn = $("#popover-update-heading");
    var level = btn.data("heading-level");
    if (!level) return;

    // Read current format from Quill
    var format = quill.getFormat();

    // Load existing heading styles
    var styles = loadHeadingStyles();
    var levelKey = level.toString();
    if (!styles[levelKey]) {
        styles[levelKey] = getDefaultHeadingStyles()[levelKey];
    }

    // Capture font (slug), size (px integer), color
    if (format.font) {
        styles[levelKey].font = format.font;
    }

    if (format.size) {
        styles[levelKey].size = parseInt(format.size, 10);
    }

    if (format.color) {
        styles[levelKey].color = format.color;
    }

    // Capture paragraph spacing (after)
    if (format.marginAfter) {
        styles[levelKey].marginAfter = parseFloat(format.marginAfter);
    }

    // Persist and apply
    localStorage.setItem("canvas_heading_styles", JSON.stringify(styles));
    injectHeadingCSS(styles);

    hidePopover();
}


function handleLookup() {
    /**
     * Handles the 'Look up' action. Currently design only.
     * In the future, this will send the selected text to an AI endpoint
     * and display a definition/explanation tooltip.
     */

    // Placeholder: functionality will be connected to backend later
    hidePopover();
}


function handleAddSelectionToCanvas() {
    /**
     * Inserts the selected text into the Quill editor on the Canvas tab.
     * Bumps heading levels down by 2 and adds hierarchy headers as needed.
     */

    var popover = $("#selection-popover");
    var selectedHtml = popover.data("selected-html");
    hidePopover();

    // Insert with hierarchy headers and heading-level bumping
    insertWithHierarchy(selectedHtml);
}


function handleRephrase(rephraseType) {
    /**
     * Handles a rephrase action (simplify, detail, analogy, regale).
     * Shows the appropriate post-rephrase modal based on which tab
     * (Guide or Canvas) the selection was made in.
     *
     * Args:
     *     rephraseType (string): The rephrase style selected
     *         (simplify, detail, analogy, regale).
     */

    var context = $("#selection-popover").data("context");
    hidePopover();

    // Show the appropriate post-rephrase modal
    if (context === "guide") {
        $("#rephrase-guide-modal-overlay").addClass("visible");
    } else {
        $("#rephrase-canvas-modal-overlay").addClass("visible");
    }
}


function handleReport() {
    /**
     * Opens the 'Report as inaccurate' modal with the selected text
     * context preserved for the form submission. Captures the highlighted
     * text and active -ate step so the report includes full context.
     */

    // Capture the selected text before the popover hides and selection clears
    var popover = $("#selection-popover");
    var selectedText = popover.data("selected-text") || "";

    // Capture the active -ate step label (e.g., "Educate", "Investigate")
    var activeStep = $(".ate-step-pill.active").text().trim();

    hidePopover();

    // Clear the browser selection so the mouseup timeout callback
    // (which fires ~10ms later) doesn't re-show the popover
    window.getSelection().removeAllRanges();

    // Store context in the modal's hidden fields
    $("#report-selected-text").val(selectedText);
    $("#report-active-step").val(activeStep);

    $("#report-modal-overlay").addClass("visible");
}


// ========================================================================
//   Report as Inaccurate Modal
// ========================================================================

function bindReportModal() {
    /**
     * Binds open/close handlers for the Report as Inaccurate modal,
     * including form submission via POST to /api/report-inaccuracy.
     */

    // Prevent clicks inside any modal dialog from bubbling to the overlay
    $(".modal-dialog").on("click mousedown mouseup", function(e) {
        e.stopPropagation();
    });

    // Close via X button
    $("#close-report-modal").on("click", function() {
        closeReportModal();
    });

    // Close via Cancel button
    $("#cancel-report").on("click", function() {
        closeReportModal();
    });

    // Close via overlay click
    $("#report-modal-overlay").on("click", function(e) {
        if ($(e.target).is("#report-modal-overlay")) {
            closeReportModal();
        }
    });

    // Form submission via POST to Flask backend
    $("#report-form").on("submit", function(e) {
        e.preventDefault();

        // Validate required fields
        var firstName = $("#report-first-name").val().trim();
        var description = $("#report-description").val().trim();
        if (!firstName || !description) {
            return;
        }

        // Gather form and context data
        var lastName = $("#report-last-name").val().trim();
        var reference = $("#report-reference").val().trim();
        var selectedText = $("#report-selected-text").val();
        var activeStep = $("#report-active-step").val();

        // Pull check context from the breadcrumb
        var checkTitle = $(".breadcrumb-current").text().trim();
        var breadcrumbLinks = $(".category-breadcrumb a");
        var category = breadcrumbLinks.eq(2).text().trim();
        var subcategory = breadcrumbLinks.eq(3).text().trim();

        // Build the payload
        var payload = {
            first_name: firstName,
            last_name: lastName,
            description: description,
            reference: reference,
            selected_text: selectedText,
            active_step: activeStep,
            category: category,
            subcategory: subcategory,
            check_title: checkTitle,
            page_url: window.location.href
        };

        // Disable the submit button while sending
        var submitBtn = $("#report-form button[type='submit']");
        submitBtn.prop("disabled", true).text("Submitting...");

        // POST to the backend
        // CSRF token from meta tag in base.html
        var csrfToken = document.querySelector("meta[name='csrf-token']");
        var csrfValue = csrfToken ? csrfToken.getAttribute("content") : "";

        fetch(window.APP_ROOT + "/api/report-inaccuracy/", {
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

            // Show brief success feedback before closing
            submitBtn.text("Submitted!");
            setTimeout(function() {
                closeReportModal();
                submitBtn.prop("disabled", false).text("Submit Report");
            }, 800);
        })
        .catch(function() {
            submitBtn.prop("disabled", false).text("Submit Report");
            alert("Failed to submit report. Please try again.");
        });
    });

    // Close on Escape key
    $(document).on("keydown", function(e) {
        if (e.key === "Escape") {
            if ($("#report-modal-overlay").hasClass("visible")) {
                closeReportModal();
            }
        }
    });
}


function closeReportModal() {
    /**
     * Closes the report modal and resets the form fields.
     */

    $("#report-modal-overlay").removeClass("visible");
    $("#report-form")[0].reset();
}


// ========================================================================
//   Post-Rephrase Modals (Guide + Canvas)
// ========================================================================

function bindRephraseModals() {
    /**
     * Binds open/close handlers and option clicks for the post-rephrase
     * modals. The Guide modal has three options (Revert, Remember for
     * this audit, Remember for all audits). The Canvas modal has only
     * Revert.
     */

    // Close via X buttons
    $("#close-rephrase-guide-modal").on("click", function() {
        $("#rephrase-guide-modal-overlay").removeClass("visible");
    });

    $("#close-rephrase-canvas-modal").on("click", function() {
        $("#rephrase-canvas-modal-overlay").removeClass("visible");
    });

    // Close via overlay click
    $("#rephrase-guide-modal-overlay, #rephrase-canvas-modal-overlay").on("click", function(e) {
        if ($(e.target).hasClass("modal-overlay")) {
            $(this).removeClass("visible");
        }
    });

    // Handle option button clicks (design only)
    $(".rephrase-option-btn").on("click", function() {
        var action = $(this).data("remember");
        var overlay = $(this).closest(".modal-overlay");

        // Placeholder: action would be handled by backend
        // action === "revert"  — undo the rephrase
        // action === "audit"   — persist for current audit only
        // action === "all"     — persist across all audits

        overlay.removeClass("visible");
    });

    // Close on Escape key
    $(document).on("keydown", function(e) {
        if (e.key === "Escape") {
            $("#rephrase-guide-modal-overlay").removeClass("visible");
            $("#rephrase-canvas-modal-overlay").removeClass("visible");
        }
    });
}


// ========================================================================
//   Update Feedback Modal
// ========================================================================

function bindFeedbackModal() {
    /**
     * Binds open/close handlers for the update feedback modal.
     * Opens when a user clicks "let us know" on an unconfirmed update.
     * Sends feedback to feedback@annielytics.com (design only, no backend).
     */

    // Open feedback modal when "let us know" link is clicked
    $(document).on("click", ".feedback-link", function(e) {
        e.preventDefault();
        var updateTitle = $(this).data("update-title");

        // Set the modal title dynamically
        $("#feedback-modal-title").text("Feedback on " + updateTitle);

        // Show the modal
        $("#feedback-modal-overlay").addClass("visible");
    });

    // Close via X button
    $("#close-feedback-modal").on("click", function() {
        closeFeedbackModal();
    });

    // Close via Cancel button
    $("#cancel-feedback").on("click", function() {
        closeFeedbackModal();
    });

    // Close via overlay click
    $("#feedback-modal-overlay").on("click", function(e) {
        if ($(e.target).is("#feedback-modal-overlay")) {
            closeFeedbackModal();
        }
    });

    // Form submission (design only)
    $("#feedback-form").on("submit", function(e) {
        e.preventDefault();

        // Placeholder: form data would be sent to feedback@annielytics.com
        closeFeedbackModal();
    });

    // Close on Escape key
    $(document).on("keydown", function(e) {
        if (e.key === "Escape") {
            if ($("#feedback-modal-overlay").hasClass("visible")) {
                closeFeedbackModal();
            }
        }
    });
}


function closeFeedbackModal() {
    /**
     * Closes the feedback modal and resets the form fields.
     */

    $("#feedback-modal-overlay").removeClass("visible");
    $("#feedback-form")[0].reset();
}
