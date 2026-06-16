/* auth.js
   Client-side authentication logic for Auditmaton for Site Audits. Uses the Firebase JS SDK
   for credential management (registration, login, password reset) and sends
   verified ID tokens to the Flask backend for session creation. Includes
   browser fingerprinting for the 2-device limit enforcement and Authorize.net
   Accept.js integration for PCI-compliant payment processing. */


/* ========================================================================
   Browser Fingerprinting
   ======================================================================== */

/**
 * Generates a simple browser fingerprint hash.
 *
 * Combines screen resolution, timezone, language, platform, and
 * hardware concurrency into a SHA-256 hash. Canvas was deliberately
 * excluded because Chrome (and other browsers) periodically update
 * their text rasterization, which would shift the canvas data URL
 * even by a single pixel and produce a brand-new hash. That caused
 * legitimate users to get registered as new devices on every browser
 * auto-update, eating into their 2-device slot.
 *
 * @returns {Promise<string>} SHA-256 hex hash of the fingerprint.
 */
async function generateFingerprint() {
    "use strict";

    var components = [
        screen.width + "x" + screen.height,
        screen.colorDepth,
        Intl.DateTimeFormat().resolvedOptions().timeZone,
        navigator.language,
        navigator.platform,
        navigator.hardwareConcurrency || "unknown",
        new Date().getTimezoneOffset()
    ];

    var raw = components.join("|");

    // SHA-256 hash using the Web Crypto API
    var encoder = new TextEncoder();
    var data = encoder.encode(raw);
    var hashBuffer = await crypto.subtle.digest("SHA-256", data);
    var hashArray = Array.from(new Uint8Array(hashBuffer));
    var hashHex = hashArray.map(function(b) { return b.toString(16).padStart(2, "0"); }).join("");

    return hashHex;
}


/* ========================================================================
   CSRF Token Helper
   ======================================================================== */

/**
 * Retrieves the CSRF token from the meta tag in the page head.
 *
 * @returns {string} The CSRF token value.
 */
function getCsrfToken() {
    "use strict";

    var meta = document.querySelector("meta[name='csrf-token']");
    return meta ? meta.getAttribute("content") : "";
}


/* ========================================================================
   UI Helpers
   ======================================================================== */

/**
 * Shows an error message below the form.
 *
 * @param {string} message - The error message to display.
 */
function showAuthError(message) {
    "use strict";

    var errorEl = document.getElementById("auth-error");
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.add("visible");
    }

    // Hide any success message
    var successEl = document.getElementById("auth-success");
    if (successEl) {
        successEl.classList.remove("visible");
    }
}

/**
 * Shows a success message below the form.
 *
 * @param {string} message - The success message to display.
 */
function showAuthSuccess(message) {
    "use strict";

    var successEl = document.getElementById("auth-success");
    if (successEl) {
        successEl.textContent = message;
        successEl.classList.add("visible");
    }

    // Hide any error message
    var errorEl = document.getElementById("auth-error");
    if (errorEl) {
        errorEl.classList.remove("visible");
    }
}

/**
 * Clears all error and success messages.
 */
function clearAuthMessages() {
    "use strict";

    var errorEl = document.getElementById("auth-error");
    var successEl = document.getElementById("auth-success");
    if (errorEl) errorEl.classList.remove("visible");
    if (successEl) successEl.classList.remove("visible");
}

/**
 * Shows the device limit warning panel.
 *
 * @param {string} message - The warning message to display.
 */
function showDeviceWarning(message) {
    "use strict";

    var warningEl = document.getElementById("device-warning");
    if (warningEl) {
        warningEl.querySelector("p").textContent = message;
        warningEl.classList.add("visible");
    }
}

/**
 * Sets the submit button to a loading state.
 *
 * @param {HTMLElement} button - The submit button element.
 * @param {boolean} loading - Whether to show the loading state.
 */
function setButtonLoading(button, loading) {
    "use strict";

    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = "<span class='spinner'></span>Please wait...";
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || "Submit";
    }
}


/* ========================================================================
   Password Visibility Toggle
   ======================================================================== */

document.addEventListener("DOMContentLoaded", function() {
    "use strict";

    var toggleButtons = document.querySelectorAll(".auth-password-toggle");

    toggleButtons.forEach(function(btn) {
        btn.addEventListener("click", function() {
            var input = btn.parentElement.querySelector("input");
            var icon = btn.querySelector("i");

            if (input.type === "password") {
                input.type = "text";
                icon.classList.remove("fa-eye");
                icon.classList.add("fa-eye-slash");
            } else {
                input.type = "password";
                icon.classList.remove("fa-eye-slash");
                icon.classList.add("fa-eye");
            }
        });
    });
});


/* ========================================================================
   Registration: Shared State
   ======================================================================== */

// Stores the Accept.js opaque nonce after card tokenization (step 1)
// so it can be sent with the account creation in the final registration POST.
var _opaqueData = null;


/* ========================================================================
   Registration: Step Navigation
   ======================================================================== */

/**
 * Shows the payment step and hides the account step.
 */
function showPaymentStep() {
    "use strict";

    var accountStep = document.getElementById("register-step-account");
    var paymentStep = document.getElementById("register-step-payment");

    if (accountStep) accountStep.classList.add("auth-step-hidden");
    if (paymentStep) paymentStep.classList.remove("auth-step-hidden");
}

/**
 * Shows the account step and hides the payment step.
 */
function showAccountStep() {
    "use strict";

    var accountStep = document.getElementById("register-step-account");
    var paymentStep = document.getElementById("register-step-payment");

    if (paymentStep) paymentStep.classList.add("auth-step-hidden");
    if (accountStep) accountStep.classList.remove("auth-step-hidden");
}

// Back button handler (from account step back to payment step)
document.addEventListener("DOMContentLoaded", function() {
    "use strict";

    var backLink = document.getElementById("back-to-payment");
    if (backLink) {
        backLink.addEventListener("click", function(e) {
            e.preventDefault();
            clearAuthMessages();
            showPaymentStep();
        });
    }
});


/* ========================================================================
   Registration: Plan Selection & Running Total
   ======================================================================== */

document.addEventListener("DOMContentLoaded", function() {
    "use strict";

    var planCards = document.querySelectorAll(".plan-card");
    if (!planCards.length) return;

    /**
     * Recalculates and displays the running total based on selected products.
     */
    function updateTotal() {
        var total = 0;

        planCards.forEach(function(card) {
            var checkbox = card.querySelector(".plan-card__checkbox");
            if (checkbox.checked) {
                total += parseInt(card.dataset.price, 10);
            }
        });

        var totalEl = document.getElementById("plan-total-amount");
        if (totalEl) {
            totalEl.textContent = "$" + Math.round(total / 100);
        }
    }

    // Pre-select add-ons from ?products= query param (linked from pricing page)
    var urlParams = new URLSearchParams(window.location.search);
    var preselected = urlParams.get("products");
    if (preselected) {
        var slugs = preselected.split(",");
        planCards.forEach(function(card) {
            var slug = card.getAttribute("data-slug");
            var checkbox = card.querySelector(".plan-card__checkbox");

            // Skip base (always selected) and disabled checkboxes
            if (checkbox.disabled) return;

            if (slugs.indexOf(slug) !== -1) {
                checkbox.checked = true;
                card.classList.add("plan-card--selected");
            }
        });

        updateTotal();
    }

    // Toggle add-on selection on card click
    planCards.forEach(function(card) {
        card.addEventListener("click", function(e) {
            var checkbox = card.querySelector(".plan-card__checkbox");

            // Base product cannot be toggled
            if (checkbox.disabled) return;

            // Prevent double-toggle when clicking the checkbox directly
            if (e.target === checkbox) return;

            checkbox.checked = !checkbox.checked;
            card.classList.toggle("plan-card--selected", checkbox.checked);
            updateTotal();
        });

        // Handle direct checkbox changes
        var checkbox = card.querySelector(".plan-card__checkbox");
        checkbox.addEventListener("change", function() {
            card.classList.toggle("plan-card--selected", checkbox.checked);
            updateTotal();
        });
    });
});


/* ========================================================================
   Registration: Card Input Formatting
   ======================================================================== */

document.addEventListener("DOMContentLoaded", function() {
    "use strict";

    // Auto-format card number with spaces every 4 digits
    var cardInput = document.getElementById("card-number");
    if (cardInput) {
        cardInput.addEventListener("input", function() {
            var value = cardInput.value.replace(/\D/g, "");
            var formatted = value.replace(/(.{4})/g, "$1 ").trim();
            cardInput.value = formatted;
        });
    }

    // Auto-format expiry as MM/YY
    var expiryInput = document.getElementById("card-expiry");
    if (expiryInput) {
        expiryInput.addEventListener("input", function() {
            var value = expiryInput.value.replace(/\D/g, "");
            if (value.length >= 2) {
                value = value.substring(0, 2) + "/" + value.substring(2);
            }
            expiryInput.value = value;
        });
    }

    // CVV: digits only
    var cvvInput = document.getElementById("card-cvv");
    if (cvvInput) {
        cvvInput.addEventListener("input", function() {
            cvvInput.value = cvvInput.value.replace(/\D/g, "");
        });
    }
});


/* ========================================================================
   Registration: Accept.js Payment Tokenization
   ======================================================================== */

/**
 * Tokenizes card data via Authorize.net Accept.js.
 *
 * Returns a Promise that resolves with the opaque data (descriptor + value)
 * or rejects with an error message.
 *
 * @returns {Promise<{dataDescriptor: string, dataValue: string}>}
 */
function tokenizeCard() {
    "use strict";

    return new Promise(function(resolve, reject) {
        // Read card fields
        var cardNumber = document.getElementById("card-number").value.replace(/\s/g, "");
        var expiry = document.getElementById("card-expiry").value;
        var cvv = document.getElementById("card-cvv").value;

        if (!cardNumber || !expiry || !cvv) {
            reject("Please fill in all payment fields.");
            return;
        }

        // Parse expiry MM/YY
        var expiryParts = expiry.split("/");
        if (expiryParts.length !== 2) {
            reject("Please enter a valid expiration date (MM/YY).");
            return;
        }

        var month = expiryParts[0];
        var year = "20" + expiryParts[1];

        // Read Authorize.net credentials from meta tags
        var clientKey = document.querySelector("meta[name='anet-client-key']");
        var apiLoginId = document.querySelector("meta[name='anet-api-login-id']");

        if (!clientKey || !apiLoginId || !clientKey.content || !apiLoginId.content) {
            reject("Payment service is not configured.");
            return;
        }

        // Build the Accept.js secure data object
        var secureData = {
            authData: {
                clientKey: clientKey.content,
                apiLoginID: apiLoginId.content
            },
            cardData: {
                cardNumber: cardNumber,
                month: month,
                year: year,
                cardCode: cvv
            }
        };

        // Dispatch to Accept.js
        Accept.dispatchData(secureData, function(response) {
            if (response.messages.resultCode === "Error") {
                var errorMsg = response.messages.message[0].text;
                reject(errorMsg);
            } else {
                resolve({
                    dataDescriptor: response.opaqueData.dataDescriptor,
                    dataValue: response.opaqueData.dataValue
                });
            }
        });
    });
}


/**
 * Returns the list of selected product slugs from the plan cards.
 *
 * @returns {string[]} Array of product slugs (e.g., ["base", "viz"]).
 */
function getSelectedProducts() {
    "use strict";

    var selected = [];
    var checkboxes = document.querySelectorAll(".plan-card__checkbox:checked");
    checkboxes.forEach(function(cb) {
        selected.push(cb.value);
    });
    return selected;
}


/* ========================================================================
   Google Sign-In Handler
   ======================================================================== */

document.addEventListener("DOMContentLoaded", function() {
    "use strict";

    var googleBtn = document.getElementById("google-signin-btn");
    if (!googleBtn) return;

    // Detect if we are on the registration page (has plan cards)
    var isRegistrationPage = !!document.getElementById("register-step-payment");

    googleBtn.addEventListener("click", async function() {
        clearAuthMessages();
        googleBtn.disabled = true;
        var originalText = googleBtn.textContent;
        googleBtn.textContent = "Please wait...";

        try {
            // Open the Google sign-in popup
            var provider = new firebase.auth.GoogleAuthProvider();
            var result = await firebase.auth().signInWithPopup(provider);

            // Get the ID token from the signed-in user
            var idToken = await result.user.getIdToken();

            // Extract name from Google profile (if available)
            var displayName = result.user.displayName || "";
            var nameParts = displayName.split(" ");
            var firstName = nameParts[0] || "";
            var lastName = nameParts.slice(1).join(" ") || "";

            if (isRegistrationPage) {
                // Registration page: ensure payment nonce exists from step 1
                if (!_opaqueData) {
                    showAuthError("Payment information is missing. Please go back and enter your card details.");
                    googleBtn.disabled = false;
                    googleBtn.textContent = originalText;
                    return;
                }

                // Complete registration: payment nonce + Google account + POST
                var selectedProducts = getSelectedProducts();
                var fingerprint = await generateFingerprint();

                var regResponse = await fetch(window.APP_ROOT + "/register/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken()
                    },
                    body: JSON.stringify({
                        id_token: idToken,
                        first_name: firstName,
                        last_name: lastName,
                        fingerprint_hash: fingerprint,
                        opaque_data_descriptor: _opaqueData.dataDescriptor,
                        opaque_data_value: _opaqueData.dataValue,
                        selected_products: selectedProducts
                    })
                });

                var regData = await regResponse.json();

                if (regResponse.ok && regData.success) {
                    window.location.href = regData.redirect;
                } else {
                    showAuthError(regData.error || "Registration failed. Please try again.");
                    googleBtn.disabled = false;
                    googleBtn.textContent = originalText;
                }
                return;
            }

            // Login page: complete the login flow immediately
            var fingerprint = await generateFingerprint();

            var response = await fetch(window.APP_ROOT + "/login/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken()
                },
                body: JSON.stringify({
                    id_token: idToken,
                    fingerprint_hash: fingerprint,
                    first_name: firstName,
                    last_name: lastName
                })
            });

            var data = await response.json();

            if (response.ok && data.success) {
                window.location.href = data.redirect;
            } else if (data.error === "device_limit") {
                showDeviceWarning(data.message);
                googleBtn.disabled = false;
                googleBtn.textContent = originalText;
            } else {
                showAuthError(data.error || "Sign-in failed. Please try again.");
                googleBtn.disabled = false;
                googleBtn.textContent = originalText;
            }

        } catch (error) {
            // Log the full error for debugging
            console.error("Google Sign-In error:", error.code, error.message, error);

            var message = "Google sign-in failed. Please try again.";

            // User closed the popup — not an error worth showing
            if (error.code === "auth/popup-closed-by-user" ||
                error.code === "auth/cancelled-popup-request") {
                googleBtn.disabled = false;
                googleBtn.textContent = originalText;
                return;
            }

            if (error.code === "auth/account-exists-with-different-credential") {
                message = "An account already exists with this email using a different sign-in method.";
            } else if (error.code === "auth/unauthorized-domain") {
                message = "This domain is not authorized for sign-in. Please contact support.";
            } else if (error.code === "auth/popup-blocked") {
                message = "The sign-in popup was blocked. Please allow popups for this site and try again.";
            } else if (error.code === "auth/internal-error") {
                message = "Authentication service error. Please try again in a moment.";
            }

            showAuthError(message);
            googleBtn.disabled = false;
            googleBtn.textContent = originalText;
        }
    });
});


/* ========================================================================
   Login Form Handler
   ======================================================================== */

document.addEventListener("DOMContentLoaded", function() {
    "use strict";

    var loginForm = document.getElementById("login-form");
    if (!loginForm) return;

    loginForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        clearAuthMessages();

        var emailInput = document.getElementById("login-email");
        var passwordInput = document.getElementById("login-password");
        var submitBtn = loginForm.querySelector(".auth-submit");

        var email = emailInput.value.trim();
        var password = passwordInput.value;

        if (!email || !password) {
            showAuthError("Please enter your email and password.");
            return;
        }

        setButtonLoading(submitBtn, true);

        try {
            // Step 1: Authenticate with Firebase
            var userCredential = await firebase.auth().signInWithEmailAndPassword(email, password);
            var idToken = await userCredential.user.getIdToken();

            // Step 2: Generate browser fingerprint
            var fingerprint = await generateFingerprint();

            // Step 3: Send token to Flask backend
            var response = await fetch(window.APP_ROOT + "/login/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken()
                },
                body: JSON.stringify({
                    id_token: idToken,
                    fingerprint_hash: fingerprint
                })
            });

            var result = await response.json();

            if (response.ok && result.success) {
                // Redirect to dashboard
                window.location.href = result.redirect;
            } else if (result.error === "device_limit") {
                showDeviceWarning(result.message);
                setButtonLoading(submitBtn, false);
            } else {
                showAuthError(result.error || "Login failed. Please try again.");
                setButtonLoading(submitBtn, false);
            }

        } catch (error) {
            // Firebase error codes
            var message = "Login failed. Please try again.";

            if (error.code === "auth/user-not-found" || error.code === "auth/wrong-password") {
                message = "Invalid email or password.";
            } else if (error.code === "auth/too-many-requests") {
                message = "Too many failed attempts. Please try again later.";
            } else if (error.code === "auth/invalid-email") {
                message = "Please enter a valid email address.";
            }

            showAuthError(message);
            setButtonLoading(submitBtn, false);
        }
    });
});


/* ========================================================================
   Registration Form Handler (Step 2: Create Account & Pay)
   ======================================================================== */

document.addEventListener("DOMContentLoaded", function() {
    "use strict";

    var registerForm = document.getElementById("register-form");
    if (!registerForm) return;

    registerForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        clearAuthMessages();

        var emailInput = document.getElementById("register-email");
        var passwordInput = document.getElementById("register-password");
        var confirmInput = document.getElementById("register-confirm");
        var firstNameInput = document.getElementById("register-first-name");
        var lastNameInput = document.getElementById("register-last-name");
        var submitBtn = registerForm.querySelector(".auth-submit");

        var email = emailInput.value.trim();
        var password = passwordInput.value;
        var confirm = confirmInput.value;
        var firstName = firstNameInput ? firstNameInput.value.trim() : "";
        var lastName = lastNameInput ? lastNameInput.value.trim() : "";

        // Client-side validation
        if (!email || !password) {
            showAuthError("Please enter your email and password.");
            return;
        }

        if (password.length < 8) {
            showAuthError("Password must be at least 8 characters.");
            return;
        }

        if (password !== confirm) {
            showAuthError("Passwords do not match.");
            return;
        }

        // Ensure we have a payment nonce from step 1
        if (!_opaqueData) {
            showAuthError("Payment information is missing. Please go back and enter your card details.");
            return;
        }

        setButtonLoading(submitBtn, true);

        try {
            // Step 1: Create account with Firebase
            var userCredential = await firebase.auth().createUserWithEmailAndPassword(email, password);

            // Step 2: Send verification email
            await userCredential.user.sendEmailVerification();

            // Step 3: Get the ID token
            var idToken = await userCredential.user.getIdToken();

            // Step 4: Get selected products and fingerprint
            var selectedProducts = getSelectedProducts();
            var fingerprint = await generateFingerprint();

            // Step 5: POST everything to the Flask backend
            var response = await fetch(window.APP_ROOT + "/register/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken()
                },
                body: JSON.stringify({
                    id_token: idToken,
                    first_name: firstName,
                    last_name: lastName,
                    fingerprint_hash: fingerprint,
                    opaque_data_descriptor: _opaqueData.dataDescriptor,
                    opaque_data_value: _opaqueData.dataValue,
                    selected_products: selectedProducts
                })
            });

            var result = await response.json();

            if (response.ok && result.success) {
                window.location.href = result.redirect;
            } else {
                showAuthError(result.error || "Registration failed. Please try again.");
                setButtonLoading(submitBtn, false);
            }

        } catch (error) {
            var message = "Registration failed. Please try again.";

            if (error.code === "auth/email-already-in-use") {
                message = "An account with this email already exists.";
            } else if (error.code === "auth/weak-password") {
                message = "Password is too weak. Use at least 8 characters with a mix of letters and numbers.";
            } else if (error.code === "auth/invalid-email") {
                message = "Please enter a valid email address.";
            }

            showAuthError(message);
            setButtonLoading(submitBtn, false);
        }
    });
});


/* ========================================================================
   Registration: Payment Continue (Step 1 → Step 2)
   ======================================================================== */

document.addEventListener("DOMContentLoaded", function() {
    "use strict";

    var continueBtn = document.getElementById("payment-continue");
    if (!continueBtn) return;

    continueBtn.addEventListener("click", async function() {
        clearAuthMessages();
        setButtonLoading(continueBtn, true);

        try {
            // Tokenize the card via Accept.js and store the nonce
            _opaqueData = await tokenizeCard();

            setButtonLoading(continueBtn, false);

            // Advance to account creation step
            showAccountStep();

        } catch (error) {
            // Error from tokenizeCard() — card validation or Accept.js failure
            var message = (typeof error === "string") ? error : "Payment validation failed. Please check your card details.";
            showAuthError(message);
            setButtonLoading(continueBtn, false);
        }
    });
});


/* ========================================================================
   Password Reset Form Handler
   ======================================================================== */

document.addEventListener("DOMContentLoaded", function() {
    "use strict";

    var resetForm = document.getElementById("reset-form");
    if (!resetForm) return;

    resetForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        clearAuthMessages();

        var emailInput = document.getElementById("reset-email");
        var submitBtn = resetForm.querySelector(".auth-submit");

        var email = emailInput.value.trim();

        if (!email) {
            showAuthError("Please enter your email address.");
            return;
        }

        setButtonLoading(submitBtn, true);

        try {
            // Firebase handles the reset email
            await firebase.auth().sendPasswordResetEmail(email);
            showAuthSuccess("If an account exists for that email, a password reset link has been sent. Check your inbox.");
            setButtonLoading(submitBtn, false);

        } catch (error) {
            // Always show a generic message to prevent email enumeration
            showAuthSuccess("If an account exists for that email, a password reset link has been sent. Check your inbox.");
            setButtonLoading(submitBtn, false);
        }
    });
});
