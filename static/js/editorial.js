/* editorial.js
   Editorial overlay functionality for the canvas view. Handles the
   "Propose Edit" and "Comment" popover actions, edit proposal modal,
   inline comment cards, override status indicators, and comment
   highlight rendering. Works alongside canvas.js. */


// ========================================================================
//   Constants
// ========================================================================

var EDITORIAL_USER_ROLE = document.body.getAttribute("data-user-role") || "";

// Quill instance for the edit proposal modal (initialized in bindEditProposalModal)
var proposalQuill = null;


// ========================================================================
//   Document Ready
// ========================================================================

$(document).ready(function() {

    // Only initialize editorial features for users with editorial roles
    if (EDITORIAL_USER_ROLE === "editor" || EDITORIAL_USER_ROLE === "owner" || EDITORIAL_USER_ROLE === "contributor") {

        // Bind the edit proposal modal
        bindEditProposalModal();

        // Bind the comment input card
        bindCommentInput();

        // Load override indicators for the current check
        loadOverrideIndicators();

        // Load existing comments for the current check
        loadComments();
    }
});


// ========================================================================
//   Edit Proposal Flow
// ========================================================================

function handleProposeEdit() {
    /**
     * Handles the "Propose Edit" popover action. Finds the nearest
     * data-content-path ancestor of the selected text, extracts the
     * check_id and field_path, and opens the edit proposal modal
     * pre-populated with the original text.
     */

    var popover = $("#selection-popover");
    var selectedText = popover.data("selected-text") || "";

    // Get the selection range to find the content path
    var selection = window.getSelection();
    if (!selection.rangeCount) {
        return;
    }

    var range = selection.getRangeAt(0);
    var container = range.commonAncestorContainer;

    // Walk up to find nearest element node
    var el = container.nodeType === 3 ? container.parentElement : container;

    // Find the nearest ancestor with data-content-path
    var contentEl = $(el).closest("[data-content-path]");
    if (!contentEl.length) {
        showEditorialToast("Could not identify the content field. Please select text within a content block.", "error");
        return;
    }

    var contentPath = contentEl.attr("data-content-path");
    var parts = contentPath.split("::");
    var checkId = parts[0] || "";
    var fieldPath = parts[1] || "";

    // Use the user's selected text as the original text to edit
    var originalText = selectedText;

    // For link elements, get the href instead
    if (fieldPath.endsWith(".source_url") || fieldPath.endsWith(".update_link")) {
        var linkEl = contentEl.is("a") ? contentEl : contentEl.find("a").first();
        originalText = linkEl.attr("href") || "";

        // Show URL input mode
        $("#edit-url-field").show();
        $("#edit-text-field").hide();
        $("#edit-url-input").val(originalText);
    } else {

        // Show text edit mode with Quill editor
        $("#edit-url-field").hide();
        $("#edit-text-field").show();
        if (proposalQuill) {
            proposalQuill.setText(originalText);
        }
    }

    // Populate modal fields
    $("#edit-check-id").val(checkId);
    $("#edit-field-path").val(fieldPath);
    $("#edit-original-text-value").val(originalText);
    $("#edit-original-text-display").text(originalText);

    // Hide the selection popover and show the modal
    hidePopover();
    window.getSelection().removeAllRanges();
    $("#edit-proposal-modal-overlay").addClass("visible");
}


function bindEditProposalModal() {
    /**
     * Binds event handlers for the edit proposal modal: close buttons,
     * overlay click, Escape key, and form submission via AJAX. Also
     * initializes the Quill rich text editor for proposed text.
     */

    // Initialize Quill editor for the proposed text field
    if (document.getElementById("edit-proposed-quill")) {
        proposalQuill = new Quill("#edit-proposed-quill", {
            theme: "snow",
            placeholder: "Enter the corrected text",
            modules: {
                toolbar: [
                    ["bold", "italic", "underline"],
                    [{ "list": "ordered" }, { "list": "bullet" }],
                    ["link"],
                    ["clean"],
                ],
            },
        });
    }

    // Close via X button
    $("#close-edit-proposal-modal").on("click", function() {
        closeEditProposalModal();
    });

    // Close via Cancel button
    $("#cancel-edit-proposal").on("click", function() {
        closeEditProposalModal();
    });

    // Close via overlay click — but only when both mousedown AND mouseup
    // happen on the overlay itself. This prevents the modal from closing
    // when the user starts a text selection inside an input/Quill editor
    // and the drag ends on the dim background (browser fires `click` on
    // the common ancestor, which would otherwise be the overlay).
    var overlayDismissArmed = false;
    $("#edit-proposal-modal-overlay").on("mousedown", function(e) {
        overlayDismissArmed = $(e.target).is("#edit-proposal-modal-overlay");
    });
    $("#edit-proposal-modal-overlay").on("mouseup", function(e) {
        if (overlayDismissArmed && $(e.target).is("#edit-proposal-modal-overlay")) {
            closeEditProposalModal();
        }
        overlayDismissArmed = false;
    });

    // Close via Escape key
    $(document).on("keydown.editProposal", function(e) {
        if (e.key === "Escape" && $("#edit-proposal-modal-overlay").hasClass("visible")) {
            closeEditProposalModal();
        }
    });

    // Form submission
    $("#edit-proposal-form").on("submit", function(e) {
        e.preventDefault();
        submitEditProposal();
    });
}


function closeEditProposalModal() {
    /**
     * Closes the edit proposal modal and resets the form.
     */

    $("#edit-proposal-modal-overlay").removeClass("visible");
    $("#edit-proposal-form")[0].reset();
    $("#edit-original-text-display").text("");

    // Clear the Quill editor
    if (proposalQuill) {
        proposalQuill.setText("");
    }
}


function submitEditProposal() {
    /**
     * Submits the edit proposal to the server via AJAX.
     * Reads the check_id, field_path, original_text, and proposed_text
     * from the modal form and POSTs to /api/propose-edit/.
     */

    var checkId = $("#edit-check-id").val();
    var fieldPath = $("#edit-field-path").val();
    var originalText = $("#edit-original-text-value").val();

    // Get proposed text from the appropriate input
    var proposedText;
    if ($("#edit-url-field").is(":visible")) {
        proposedText = $("#edit-url-input").val().trim();
    } else if (proposalQuill) {

        // Get HTML from Quill, but use plain text if no formatting was applied
        var quillHtml = proposalQuill.root.innerHTML.trim();
        var quillText = proposalQuill.getText().trim();

        // If the editor only contains plain text (single <p> with no formatting),
        // send as plain text to avoid unnecessary HTML wrapping
        proposedText = quillHtml === "<p>" + quillText + "</p>" ? quillText : quillHtml;
    } else {
        proposedText = "";
    }

    if (!proposedText) {
        showEditorialToast("Please enter the proposed text.", "error");
        return;
    }

    if (proposedText === originalText) {
        showEditorialToast("The proposed text is identical to the original.", "error");
        return;
    }

    // Get CSRF token
    var csrfMeta = document.querySelector('meta[name="csrf-token"]');
    var csrfValue = csrfMeta ? csrfMeta.getAttribute("content") : "";

    // Pull category/subcategory off the canvas root so the server can write
    // the edit directly to the source JSON file (owner only)
    var canvasRoot = document.getElementById("panel-canvas");
    var categoryKey = canvasRoot ? canvasRoot.getAttribute("data-category-key") : "";
    var subcategorySlug = canvasRoot ? canvasRoot.getAttribute("data-subcategory-slug") : "";

    var payload = {
        check_id: checkId,
        field_path: fieldPath,
        original_text: originalText,
        proposed_text: proposedText,
        source_url: window.location.href,
        category_key: categoryKey,
        subcategory_slug: subcategorySlug,
    };

    fetch(window.APP_ROOT + "/api/propose-edit/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfValue,
            "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify(payload),
    })
    .then(function(response) {
        return response.json().then(function(data) {
            return { ok: response.ok, data: data };
        });
    })
    .then(function(result) {
        if (result.ok) {
            closeEditProposalModal();
            showEditorialToast(
    EDITORIAL_USER_ROLE === "owner" ? "Edit submitted to your To Do tab." : "Edit submitted.",
    "success"
);
            addOverrideIndicator(checkId + "::" + fieldPath, "pending", result.data.override_id);
        } else {
            showEditorialToast(result.data.error || "Failed to submit proposal.", "error");
        }
    })
    .catch(function() {
        showEditorialToast("Network error. Please try again.", "error");
    });
}


// ========================================================================
//   Format as Code Flow
// ========================================================================

function handleFormatAsCode() {
    /**
     * Handles the "Format as code" popover action. Wraps the current
     * selection in <code> tags both in the DOM (for instant feedback)
     * and in the source JSON file (via /api/format-as-code/).
     *
     * Refuses if the selection spans multiple element nodes (e.g.,
     * straddles existing inline tags), since reproducing such a
     * selection inside the source JSON is not straightforward.
     */

    var popover = $("#selection-popover");
    var selectedText = popover.data("selected-text") || "";

    var selection = window.getSelection();
    if (!selection.rangeCount) {
        return;
    }
    var range = selection.getRangeAt(0).cloneRange();

    // Refuse trivial selections
    if (!selectedText.trim()) {
        showEditorialToast("Select some text first.", "error");
        return;
    }

    // Walk up to the editable content block to read check_id and field_path
    var container = range.commonAncestorContainer;
    var el = container.nodeType === 3 ? container.parentElement : container;
    var contentEl = $(el).closest("[data-content-path]");
    if (!contentEl.length) {
        showEditorialToast("Could not identify the content field. Please select text within a content block.", "error");
        return;
    }

    var contentPath = contentEl.attr("data-content-path");
    var parts = contentPath.split("::");
    var checkId = parts[0] || "";
    var fieldPath = parts[1] || "";

    // Refuse selections that already sit inside a <code> element
    if ($(el).closest("code").length) {
        showEditorialToast("Selection is already formatted as code.", "error");
        return;
    }

    // The backend resolves the source file from the scope embedded in
    // checkId — either a real check_id (walked across the JSON tree) or
    // a `__subcat__/<cat>/<sub>` synthetic prefix (parsed directly).
    // No client-side category/subcategory lookup needed.

    // Get CSRF token
    var csrfMeta = document.querySelector('meta[name="csrf-token"]');
    var csrfValue = csrfMeta ? csrfMeta.getAttribute("content") : "";

    var payload = {
        check_id: checkId,
        field_path: fieldPath,
        selected_text: selectedText,
        source_url: window.location.href,
    };

    // Hide popover immediately for a snappy feel
    hidePopover();

    fetch(window.APP_ROOT + "/api/format-as-code/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfValue,
            "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify(payload),
    })
    .then(function(response) {
        return response.json().then(function(data) {
            return { ok: response.ok, data: data };
        });
    })
    .then(function(result) {
        if (!result.ok) {
            showEditorialToast(result.data.error || "Failed to format as code.", "error");
            return;
        }

        // Wrap the saved range in a <code> element in the DOM for instant
        // visual feedback. The wrap is only persisted to the source JSON
        // when the owner approves the edit from /admin/editorial/, so on
        // page reload the wrap will revert until then. surroundContents
        // throws if the range straddles elements; fall back to
        // extractContents + insertNode in that case.
        var codeEl = document.createElement("code");
        try {
            range.surroundContents(codeEl);
        } catch (err) {
            var frag = range.extractContents();
            codeEl.appendChild(frag);
            range.insertNode(codeEl);
        }

        // Drop the selection so the popover doesn't immediately reappear
        window.getSelection().removeAllRanges();

        showEditorialToast(
    EDITORIAL_USER_ROLE === "owner" ? "Edit submitted to your To Do tab." : "Edit submitted.",
    "success"
);
        addOverrideIndicator(checkId + "::" + fieldPath, "pending", result.data.override_id);
    })
    .catch(function() {
        showEditorialToast("Network error. Please try again.", "error");
    });
}


// ========================================================================
//   Comment Flow
// ========================================================================

function handleComment() {
    /**
     * Handles the "Comment" popover action. Captures the text selection
     * anchor data and opens an inline comment input card near the selection.
     */

    var popover = $("#selection-popover");
    var selectedText = popover.data("selected-text") || "";

    // Get the selection range
    var selection = window.getSelection();
    if (!selection.rangeCount) {
        return;
    }

    var range = selection.getRangeAt(0);
    var container = range.commonAncestorContainer;
    var el = container.nodeType === 3 ? container.parentElement : container;

    // Find the nearest content path ancestor
    var contentEl = $(el).closest("[data-content-path]");
    if (!contentEl.length) {
        showEditorialToast("Could not identify the content field. Please select text within a content block.", "error");
        return;
    }

    var contentPath = contentEl.attr("data-content-path");

    // Get the full text of the content element for offset calculation
    var fullText = contentEl.text();
    var startOffset = fullText.indexOf(selectedText);
    var endOffset = startOffset >= 0 ? startOffset + selectedText.length : -1;

    // Capture prefix/suffix context (~30 chars)
    var prefix = startOffset > 0 ? fullText.substring(Math.max(0, startOffset - 30), startOffset) : "";
    var suffix = endOffset >= 0 ? fullText.substring(endOffset, Math.min(fullText.length, endOffset + 30)) : "";

    // Store anchor data for submission
    var commentInput = $("#comment-input-wrapper");
    commentInput.data("content-path", contentPath);
    commentInput.data("anchor-exact", selectedText);
    commentInput.data("anchor-prefix", prefix);
    commentInput.data("anchor-suffix", suffix);
    commentInput.data("anchor-start-offset", startOffset);
    commentInput.data("anchor-end-offset", endOffset);

    // Position the comment input near the selection
    var rect = range.getBoundingClientRect();
    var scrollTop = window.pageYOffset || document.documentElement.scrollTop;

    commentInput.css({
        top: (rect.bottom + scrollTop + 8) + "px",
        left: Math.max(8, rect.left - 50) + "px",
    });

    // Hide the popover and show the comment input
    hidePopover();
    window.getSelection().removeAllRanges();
    commentInput.addClass("visible").show();
    $("#comment-input-textarea").val("").focus();
}


function bindCommentInput() {
    /**
     * Binds event handlers for the inline comment input card.
     */

    // Cancel button
    $("#comment-input-cancel").on("click", function() {
        hideCommentInput();
    });

    // Submit button
    $("#comment-input-submit").on("click", function() {
        submitComment();
    });

    // Close when clicking outside
    $(document).on("mousedown.commentInput", function(e) {
        if (!$(e.target).closest("#comment-input-wrapper").length && $("#comment-input-wrapper").hasClass("visible")) {
            hideCommentInput();
        }
    });

    // Ctrl+Enter to submit
    $("#comment-input-textarea").on("keydown", function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            submitComment();
        }
    });
}


function hideCommentInput() {
    /**
     * Hides the inline comment input card and clears its contents.
     */

    $("#comment-input-wrapper").removeClass("visible").hide();
    $("#comment-input-textarea").val("");
}


function submitComment() {
    /**
     * Submits the comment to the server via AJAX. Reads anchor data
     * from the comment input's jQuery data attributes and POSTs
     * to /api/comments/.
     */

    var commentInput = $("#comment-input-wrapper");
    var commentText = $("#comment-input-textarea").val().trim();

    if (!commentText) {
        showEditorialToast("Please enter a comment.", "error");
        return;
    }

    var contentPath = commentInput.data("content-path");
    var parts = contentPath.split("::");
    var checkId = parts[0] || "";

    // Get audit_id from the canvas panel data attribute
    var auditId = $("#panel-canvas").data("audit-id") || "";

    // Get CSRF token
    var csrfMeta = document.querySelector('meta[name="csrf-token"]');
    var csrfValue = csrfMeta ? csrfMeta.getAttribute("content") : "";

    var payload = {
        audit_id: auditId,
        check_id: checkId,
        content_path: contentPath,
        anchor_exact: commentInput.data("anchor-exact"),
        anchor_prefix: commentInput.data("anchor-prefix"),
        anchor_suffix: commentInput.data("anchor-suffix"),
        anchor_start_offset: commentInput.data("anchor-start-offset"),
        anchor_end_offset: commentInput.data("anchor-end-offset"),
        comment_text: commentText,
        source_url: window.location.href,
    };

    fetch(window.APP_ROOT + "/api/comments/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfValue,
            "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify(payload),
    })
    .then(function(response) {
        return response.json().then(function(data) {
            return { ok: response.ok, data: data };
        });
    })
    .then(function(result) {
        if (result.ok) {
            hideCommentInput();
            showEditorialToast("Comment posted.", "success");
        } else {
            showEditorialToast(result.data.error || "Failed to post comment.", "error");
        }
    })
    .catch(function() {
        showEditorialToast("Network error. Please try again.", "error");
    });
}


// ========================================================================
//   Override Indicators
// ========================================================================

function loadOverrideIndicators() {
    /**
     * Fetches approved and pending overrides for the current check
     * and adds visual indicator dots to the corresponding content blocks.
     */

    // Extract check_id from the first data-content-path attribute
    var firstPath = $("[data-content-path]").first().attr("data-content-path");
    if (!firstPath) {
        return;
    }

    var checkId = firstPath.split("::")[0];
    if (!checkId) {
        return;
    }

    fetch(window.APP_ROOT + "/api/overrides/" + encodeURIComponent(checkId) + "/", {
        headers: {
            "X-Requested-With": "XMLHttpRequest",
        },
    })
    .then(function(response) {
        if (!response.ok) {
            return [];
        }
        return response.json();
    })
    .then(function(overrides) {
        overrides.forEach(function(override) {
            if (override.status === "pending" || override.status === "approved" || override.status === "applied") {
                addOverrideIndicator(
                    override.check_id + "::" + override.field_path,
                    override.status,
                    override.id
                );
            }
        });
    })
    .catch(function() {
        // Silently fail — indicators are non-critical
    });
}


function addOverrideIndicator(contentPath, status, overrideId) {
    /**
     * Adds a colored dot indicator to a content block showing its
     * override status (pending = orange, approved = green, applied = blue).
     *
     * The dot stores the override_id so a click on it can DELETE the
     * matching row via the editorial API. CSS escaping on the attribute
     * selector lets us match content paths that contain "/" (e.g.
     * subcategory-level synthetic paths like
     * "__subcat__/rich-results/organization::intro").
     *
     * Args:
     *     contentPath (str): The data-content-path value.
     *     status (str): "pending", "approved", or "applied".
     *     overrideId (str, optional): UUID of the override row, used
     *         when the dot is clicked to remove the edit.
     */

    if (!contentPath) {
        return;
    }

    // Escape any characters that have meaning inside a CSS attribute
    // selector value (slashes are fine quoted, but backslashes and
    // double quotes must be escaped to avoid a syntax error).
    var safePath = contentPath.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
    var el = $('[data-content-path="' + safePath + '"]');
    if (!el.length) {
        if (window.console && console.warn) {
            console.warn("[override-dot] no [data-content-path] matches", contentPath);
        }
        return;
    }

    // Remove any existing indicator
    el.find(".override-indicator").remove();

    // Add the new indicator dot. Promote relative positioning on the
    // host so the dot's absolute positioning anchors to it (some
    // editable-content elements may have lost their .editable-content
    // class).
    if (el.css("position") === "static") {
        el.css("position", "relative");
    }

    var titleByStatus = {
        "pending": "Edit pending review — click to remove",
        "approved": "Edit approved — click to remove",
        "applied": "Edit applied to source — click to remove",
    };
    var title = titleByStatus[status] || "Edit";
    var dot = $('<span class="override-indicator ' + status + '"></span>')
        .attr("title", title)
        .attr("data-override-id", overrideId || "");
    el.prepend(dot);

    if (window.console && console.info) {
        console.info("[override-dot] added", status, "on", contentPath, "id=" + (overrideId || "none"));
    }
}


// ========================================================================
//   Comment Highlights
// ========================================================================

function loadComments() {
    /**
     * Fetches existing comments for the current check and highlights
     * the anchored text in the rendered content.
     */

    // Extract check_id from the first content path
    var firstPath = $("[data-content-path]").first().attr("data-content-path");
    if (!firstPath) {
        return;
    }

    var checkId = firstPath.split("::")[0];
    var auditId = $("#panel-canvas").data("audit-id") || "";

    if (!checkId || !auditId) {
        return;
    }

    fetch(window.APP_ROOT + "/api/comments/" + encodeURIComponent(checkId) + "/?audit_id=" + encodeURIComponent(auditId), {
        headers: {
            "X-Requested-With": "XMLHttpRequest",
        },
    })
    .then(function(response) {
        if (!response.ok) {
            return [];
        }
        return response.json();
    })
    .then(function(comments) {
        comments.forEach(function(comment) {
            highlightCommentAnchor(comment);
        });
    })
    .catch(function() {
        // Silently fail — highlights are non-critical
    });
}


function highlightCommentAnchor(comment) {
    /**
     * Highlights the text that a comment is anchored to by wrapping
     * it in a <mark> element. Uses prefix/suffix context matching
     * with a character offset fallback.
     *
     * Args:
     *     comment (dict): Comment object with anchor data.
     */

    var contentEl = $('[data-content-path="' + comment.content_path + '"]');
    if (!contentEl.length) {
        return;
    }

    var exactText = comment.anchor.exact;
    if (!exactText) {
        return;
    }

    // Find the text in the DOM element
    var textContent = contentEl.text();
    var startIndex = -1;

    // Strategy 1: Find exact text with prefix/suffix context
    if (comment.anchor.prefix && comment.anchor.suffix) {
        var searchStr = comment.anchor.prefix + exactText + comment.anchor.suffix;
        var contextIndex = textContent.indexOf(searchStr);
        if (contextIndex >= 0) {
            startIndex = contextIndex + comment.anchor.prefix.length;
        }
    }

    // Strategy 2: Find exact text alone
    if (startIndex < 0) {
        startIndex = textContent.indexOf(exactText);
    }

    // Strategy 3: Fall back to character offset
    if (startIndex < 0 && comment.anchor.start_offset !== null) {
        startIndex = comment.anchor.start_offset;
    }

    if (startIndex < 0) {
        return;
    }

    // Walk the DOM tree to find the text node and wrap with <mark>
    var resolvedClass = comment.resolved ? " resolved" : "";
    wrapTextRange(contentEl[0], startIndex, startIndex + exactText.length, comment.id, resolvedClass);
}


function wrapTextRange(element, start, end, commentId, extraClass) {
    /**
     * Wraps a character range within an element's text content
     * with a <mark> highlight element.
     *
     * Args:
     *     element (HTMLElement): The container element.
     *     start (int): Start character offset.
     *     end (int): End character offset.
     *     commentId (str): UUID to set as data-comment-id.
     *     extraClass (str): Additional CSS classes for the mark.
     */

    var walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
    var currentOffset = 0;
    var node;
    var nodesToWrap = [];

    // Collect text nodes that fall within the range
    while ((node = walker.nextNode())) {
        var nodeLength = node.textContent.length;
        var nodeStart = currentOffset;
        var nodeEnd = currentOffset + nodeLength;

        // Check if this text node overlaps with our target range
        if (nodeEnd > start && nodeStart < end) {
            var wrapStart = Math.max(0, start - nodeStart);
            var wrapEnd = Math.min(nodeLength, end - nodeStart);
            nodesToWrap.push({ node: node, start: wrapStart, end: wrapEnd });
        }

        currentOffset += nodeLength;

        // Stop if we are past the end
        if (currentOffset >= end) {
            break;
        }
    }

    // Wrap the collected ranges with <mark> elements
    for (var i = nodesToWrap.length - 1; i >= 0; i--) {
        var info = nodesToWrap[i];
        var range = document.createRange();
        range.setStart(info.node, info.start);
        range.setEnd(info.node, info.end);

        var mark = document.createElement("mark");
        mark.className = "comment-highlight" + (extraClass || "");
        mark.setAttribute("data-comment-id", commentId);
        range.surroundContents(mark);
    }
}


// ========================================================================
//   Text Extraction Helpers
// ========================================================================

function getTextWithBreaks(element) {
    /**
     * Extracts text content from an element, preserving paragraph
     * and line breaks as newline characters. Block-level elements
     * (p, div, li) insert double newlines between them.
     *
     * Args:
     *     element (HTMLElement): The container element.
     *
     * Returns:
     *     str: Plain text with newlines preserving paragraph structure.
     */

    var text = "";
    var children = element.childNodes;

    for (var i = 0; i < children.length; i++) {
        var node = children[i];

        if (node.nodeType === 3) {

            // Text node
            text += node.textContent;
        } else if (node.nodeType === 1) {
            var tag = node.tagName.toLowerCase();

            if (tag === "br") {
                text += "\n";
            } else if (tag === "p" || tag === "div" || tag === "li" || tag === "h1" || tag === "h2" || tag === "h3" || tag === "h4" || tag === "h5" || tag === "h6") {

                // Add paragraph break before block elements
                if (text && !text.endsWith("\n")) {
                    text += "\n\n";
                }
                text += getTextWithBreaks(node);
            } else {
                text += getTextWithBreaks(node);
            }
        }
    }

    return text.trim();
}


// ========================================================================
//   Toast Notifications
// ========================================================================

function showEditorialToast(message, type) {
    /**
     * Shows a temporary toast notification at the bottom-right corner.
     *
     * Args:
     *     message (str): The message text.
     *     type (str): "success" or "error".
     */

    // Remove any existing toast
    $(".editorial-toast").remove();

    var toast = $('<div class="editorial-toast ' + type + '">' + message + '</div>');
    $("body").append(toast);

    // Trigger visibility animation
    setTimeout(function() {
        toast.addClass("visible");
    }, 10);

    // Auto-hide after 4 seconds
    setTimeout(function() {
        toast.removeClass("visible");

        // Remove from DOM after fade-out
        setTimeout(function() {
            toast.remove();
        }, 300);
    }, 4000);
}


// ========================================================================
//   Dashboard: Override Review
// ========================================================================

function reviewOverride(overrideId, status) {
    /**
     * Sends an approval or rejection for a content override proposal.
     * Used on the /admin/editorial/ dashboard page.
     *
     * Args:
     *     overrideId (str): UUID of the override to review.
     *     status (str): "approved" or "rejected".
     */

    // Get CSRF token
    var csrfMeta = document.querySelector('meta[name="csrf-token"]');
    var csrfValue = csrfMeta ? csrfMeta.getAttribute("content") : "";

    var note = "";
    if (status === "rejected") {
        note = prompt("Optional: Add a note explaining why this edit was rejected.");
        if (note === null) {
            return;
        }
    }

    fetch(window.APP_ROOT + "/api/overrides/" + overrideId + "/review/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfValue,
            "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({ status: status, note: note }),
    })
    .then(function(response) {
        return response.json().then(function(data) {
            return { ok: response.ok, data: data };
        });
    })
    .then(function(result) {
        if (result.ok) {

            // Remove the row from the table
            var row = document.querySelector('[data-override-id="' + overrideId + '"]');
            if (row) {
                row.style.transition = "opacity 0.3s ease";
                row.style.opacity = "0";
                setTimeout(function() {
                    row.remove();

                    // Show empty state if no more rows
                    if (!document.querySelector(".proposals-table tbody tr")) {
                        document.querySelector(".proposals-table").remove();
                        var empty = document.createElement("div");
                        empty.className = "dashboard-empty-state";
                        empty.innerHTML = '<i class="fa-solid fa-inbox"></i><p>No pending edit proposals.</p>';
                        document.querySelector(".editorial-dashboard").appendChild(empty);
                    }
                }, 300);
            }
        } else {
            alert(result.data.error || "Failed to review override.");
        }
    })
    .catch(function() {
        alert("Network error. Please try again.");
    });
}


// ========================================================================
//   Integration with canvas.js Popover
// ========================================================================

// These functions are called from canvas.js popover action handler.
// The canvas.js file dispatches to these based on the data-action attribute.

// Register editorial actions with the popover system
$(document).ready(function() {
    var popover = $("#selection-popover");

    // Listen for editorial action clicks on the popover
    popover.on("click", ".popover-editorial[data-action='propose-edit']", function(e) {
        e.stopPropagation();
        handleProposeEdit();
    });

    popover.on("click", ".popover-editorial[data-action='format-as-code']", function(e) {
        e.stopPropagation();
        handleFormatAsCode();
    });

    popover.on("click", ".popover-editorial[data-action='comment']", function(e) {
        e.stopPropagation();
        handleComment();
    });

    // Click an indicator dot to remove the underlying edit. Editors can
    // only delete their own pending edits; owners can delete anything.
    // The backend reverses any JSON write before dropping the row.
    $(document).on("click", ".override-indicator", function(e) {
        e.stopPropagation();
        e.preventDefault();
        handleDeleteOverride($(this));
    });
});


function handleDeleteOverride($dot) {
    /**
     * Deletes the override referenced by an indicator dot. Confirms
     * with the user, calls DELETE /api/overrides/<id>/, removes the
     * dot on success, and shows a toast suggesting a refresh so the
     * rendered content matches the deletion.
     *
     * Args:
     *     $dot (jQuery): The clicked .override-indicator element.
     */

    var overrideId = $dot.attr("data-override-id");
    if (!overrideId) {
        return;
    }

    if (!window.confirm("Remove this edit? This cannot be undone.")) {
        return;
    }

    var csrfMeta = document.querySelector('meta[name="csrf-token"]');
    var csrfValue = csrfMeta ? csrfMeta.getAttribute("content") : "";

    fetch(window.APP_ROOT + "/api/overrides/" + encodeURIComponent(overrideId) + "/", {
        method: "DELETE",
        headers: {
            "X-CSRFToken": csrfValue,
            "X-Requested-With": "XMLHttpRequest",
        },
    })
    .then(function(response) {
        return response.json().then(function(data) {
            return { ok: response.ok, data: data };
        });
    })
    .then(function(result) {
        if (result.ok) {
            $dot.remove();
            showEditorialToast("Edit removed. Refresh to see changes.", "success");
        } else {
            showEditorialToast(result.data.error || "Failed to remove edit.", "error");
        }
    })
    .catch(function() {
        showEditorialToast("Network error. Please try again.", "error");
    });
}
