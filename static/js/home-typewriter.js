/* static/js/home-typewriter.js
 *
 * Typewriter reveal for the hero tagline below AUDITMATON. Reads the
 * phrase from a data-text attribute, types it character-by-character,
 * and plays a synthesized typewriter clack per keystroke via the Web
 * Audio API (no external audio asset).
 *
 * Respects prefers-reduced-motion: instantly fills the tagline and
 * skips sound when the user has requested reduced motion.
 *
 * Browser autoplay policy: an AudioContext starts in "suspended"
 * state on a cold page load and only transitions to "running" after
 * a real user gesture (click / touchend / keydown). The first
 * animation on a fresh visit will therefore be silent. We expose
 * click-to-replay on the tagline element so the user has a clear
 * affordance to hear the sound on demand; the click itself counts
 * as the gesture that unsuspends the AudioContext.
 */

(function () {

    // Typewriter clacks silenced 2026-05-30. Annie felt the synthesized
    // audio would get annoying for visitors who load the homepage
    // repeatedly. The typewriter animation, click-to-replay affordance,
    // and finishing cursor all still work; only the sound is muted.
    // Flip back to true to restore the clacks.
    var AUDIO_ENABLED = false;

    document.addEventListener("DOMContentLoaded", function () {
        var tagline = document.querySelector(".home-hero-tagline");
        var target = document.querySelector(".home-hero-tagline-text");
        var cursor = document.querySelector(".home-hero-tagline-cursor");
        if (!tagline || !target) return;

        var text = target.getAttribute("data-text") || "";

        // Reduced-motion users get the full phrase instantly, no sound
        var reduceMotion = window.matchMedia
            && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (reduceMotion) {
            target.textContent = text;
            if (cursor) cursor.style.display = "none";
            tagline.style.cursor = "default";
            return;
        }

        var audio = createKeyClickAudio();
        var player = createTypewriter(target, cursor, text, audio);

        tagline.setAttribute("title", AUDIO_ENABLED ? "Click to replay with sound" : "Click to replay");
        tagline.addEventListener("click", function () {
            // The click itself is the user gesture that lets the
            // AudioContext resume — so the next clacks WILL play.
            audio.resume();
            player.run();
        });

        player.run();
    });


    /**
     * Builds the audio engine. Returns { play, resume }.
     *
     * play() — fires one synthesized clack. Silently no-ops if the
     *          AudioContext is unavailable or still suspended.
     * resume() — explicit hook used from a user-gesture handler to
     *            unsuspend the AudioContext per autoplay policy.
     *
     * Returns:
     *   object: { play: function, resume: function }
     */
    function createKeyClickAudio() {
        // Short-circuit when the AUDIO_ENABLED flag is off. No
        // AudioContext is created, so no autoplay-policy gesture
        // listeners are attached either.
        if (!AUDIO_ENABLED) {
            return { play: function () {}, resume: function () {} };
        }
        var AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) {
            return { play: function () {}, resume: function () {} };
        }

        var ctx = new AudioCtx();

        // Best-effort resume on any global gesture so subsequent
        // page-load animations (after the user has interacted once)
        // come back with sound automatically.
        if (ctx.state === "suspended") {
            var resumeOnce = function () {
                ctx.resume();
                ["click", "touchstart", "keydown"].forEach(function (e) {
                    document.removeEventListener(e, resumeOnce, true);
                });
            };
            ["click", "touchstart", "keydown"].forEach(function (e) {
                document.addEventListener(e, resumeOnce, true);
            });
        }

        return {
            play: function () { playKeyClick(ctx); },
            resume: function () {
                if (ctx && ctx.state === "suspended") ctx.resume();
            }
        };
    }


    /**
     * Synthesizes and plays a single typewriter clack.
     *
     * The sound is a short noise burst routed through a bandpass
     * filter with a fast decay envelope. The center frequency is
     * jittered per call so successive clacks don't sound identical.
     *
     * Args:
     *   ctx (AudioContext): The audio context to play through.
     */
    function playKeyClick(ctx) {
        if (!ctx || ctx.state !== "running") return;

        var dur = 0.04;
        var bufSize = Math.floor(ctx.sampleRate * dur);
        var buf = ctx.createBuffer(1, bufSize, ctx.sampleRate);
        var data = buf.getChannelData(0);
        for (var i = 0; i < bufSize; i++) {
            // Decaying white noise: amplitude tapers to zero by buffer end
            data[i] = (Math.random() * 2 - 1) * (1 - i / bufSize);
        }

        var src = ctx.createBufferSource();
        src.buffer = buf;

        var filter = ctx.createBiquadFilter();
        filter.type = "bandpass";
        filter.frequency.value = 2000 + Math.random() * 800;
        filter.Q.value = 1.4;

        var gain = ctx.createGain();
        gain.gain.value = 0.22;
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);

        src.connect(filter);
        filter.connect(gain);
        gain.connect(ctx.destination);

        src.start();
        src.stop(ctx.currentTime + dur);
    }


    /**
     * Builds a re-entrant typewriter player. Returns { run }.
     *
     * run() — clears any in-flight animation, then types the phrase
     *         from char 0. Safe to call from a click handler to
     *         replay the animation; the prior pending setTimeout
     *         chain is canceled before the new one starts.
     *
     * Args:
     *   target (HTMLElement): Element whose textContent receives the slice
     *   text (string): Full phrase to type
     *   audio (object): Audio engine with a play() method
     *
     * Returns:
     *   object: { run: function }
     */
    function createTypewriter(target, cursor, text, audio) {
        var CHAR_DELAY_MS = 110;
        var SPACE_PAUSE_MS = 220;   // extra hold after a space, between words
        var START_DELAY_MS = 350;
        var pendingTimer = null;

        function typeChar(i) {
            target.textContent = text.slice(0, i);
            if (i > 0 && text[i - 1] !== " ") audio.play();
            if (i < text.length) {
                pendingTimer = setTimeout(function () {
                    typeChar(i + 1);
                }, nextDelay(i > 0 ? text[i - 1] : ""));
            } else {
                pendingTimer = null;
                // Hand off to the finishing animation: 5 more blinks
                // then settle hidden. Force a reflow between remove and
                // add so the animation restarts from iteration 0.
                if (cursor) {
                    cursor.classList.remove("is-finishing");
                    void cursor.offsetWidth;
                    cursor.classList.add("is-finishing");
                }
            }
        }

        /**
         * Returns the delay (ms) before typing the next character.
         * Mixes a baseline pace with occasional quick bursts and brief
         * hesitations to mimic the irregular rhythm of a real typist.
         *
         * Args:
         *   prev (string): the character that was just typed (or "" if none)
         *
         * Returns:
         *   number: delay in milliseconds
         */
        function nextDelay(prev) {
            // Inter-word hold so word breaks read clearly
            if (prev === " ") {
                return CHAR_DELAY_MS + SPACE_PAUSE_MS + (Math.random() - 0.5) * 40;
            }
            var roll = Math.random();
            // 10% chance: brief hesitation, as if the typist paused
            if (roll < 0.10) return 200 + Math.random() * 140;
            // 15% chance: quick succession, fingers in rhythm
            if (roll < 0.25) return 50 + Math.random() * 35;
            // 75% baseline: normal pace with wider jitter than a flat metronome
            return CHAR_DELAY_MS + (Math.random() - 0.5) * 110;
        }

        return {
            run: function () {
                if (pendingTimer) {
                    clearTimeout(pendingTimer);
                    pendingTimer = null;
                }
                target.textContent = "";
                // Clear the finishing state so the cursor blinks
                // normally throughout the fresh type-on.
                if (cursor) cursor.classList.remove("is-finishing");
                pendingTimer = setTimeout(function () { typeChar(0); }, START_DELAY_MS);
            }
        };
    }

})();
