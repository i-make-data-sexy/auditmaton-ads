/* task_polling.js
   Reusable background task status polling. Polls the task-status endpoint
   at a configurable interval and fires callbacks on completion or failure.
   Used by intake.js for crawl file processing, and will be reused for
   chart generation and PDF export tasks. */


/* ========================================================================
   Task Polling
   ======================================================================== */

/**
 * Polls a background task until it reaches a terminal state.
 *
 * Args:
 *     taskId (string): The Huey task ID returned by the server.
 *     options (object): Configuration with the following keys:
 *         - url (string): Base URL for the status endpoint. The task ID
 *           is appended automatically.
 *         - interval (number): Polling interval in milliseconds (default: 2000).
 *         - onComplete (function): Called with the response when status is "complete".
 *         - onFailed (function): Called with the response when status is "failed".
 *         - onProgress (function): Called with the response on each poll while
 *           status is "processing" or "queued" (optional).
 *         - onError (function): Called if the AJAX request itself fails (optional).
 *         - maxAttempts (number): Maximum poll attempts before giving up (default: 150,
 *           which is 5 minutes at 2-second intervals).
 */
function pollTaskStatus(taskId, options) {

    var url = options.url || (window.APP_ROOT + "/intake/task-status/" + taskId + "/");
    var interval = options.interval || 2000;
    var maxAttempts = options.maxAttempts || 150;
    var attempts = 0;
    var timerId = null;

    function poll() {
        attempts++;

        $.ajax({
            url: url,
            method: "GET",
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            },
            success: function(response) {

                /* Terminal states */
                if (response.status === "complete") {
                    if (options.onComplete) {
                        options.onComplete(response);
                    }
                    return;
                }

                if (response.status === "failed") {
                    if (options.onFailed) {
                        options.onFailed(response);
                    }
                    return;
                }

                /* Still in progress */
                if (options.onProgress) {
                    options.onProgress(response);
                }

                /* Check attempt limit */
                if (attempts >= maxAttempts) {
                    if (options.onFailed) {
                        options.onFailed({
                            status: "failed",
                            error: "Processing timed out. Please try again."
                        });
                    }
                    return;
                }

                /* Schedule next poll */
                timerId = setTimeout(poll, interval);
            },
            error: function(xhr) {

                /* Network or server errors */
                if (options.onError) {
                    options.onError(xhr);
                } else if (options.onFailed) {
                    options.onFailed({
                        status: "failed",
                        error: "Could not check task status. Please try again."
                    });
                }
            }
        });
    }

    /* Start polling */
    poll();

    /* Return a handle to cancel polling if needed */
    return {
        cancel: function() {
            if (timerId) {
                clearTimeout(timerId);
                timerId = null;
            }
        }
    };
}
