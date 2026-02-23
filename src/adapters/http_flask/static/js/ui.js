/* ═══════════════════════════════════════════════════════════════════════════
   UI.JS — ScenarioBuilder minimal UI interactions (vanilla JS, no deps)
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  "use strict";

  var SB = {};

  /* ── Modal ─────────────────────────────────────────────────────────── */
  SB.openModal = function (id) {
    var overlay = document.getElementById(id);
    if (overlay) overlay.classList.add("is-open");
  };

  SB.closeModal = function (id) {
    var overlay = document.getElementById(id);
    if (overlay) overlay.classList.remove("is-open");
  };

  // Close modal on overlay click (not inner .sb-modal)
  document.addEventListener("click", function (e) {
    if (e.target.classList.contains("sb-modal-overlay")) {
      e.target.classList.remove("is-open");
    }
  });

  // Close modal on Escape
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      var openModals = document.querySelectorAll(".sb-modal-overlay.is-open");
      openModals.forEach(function (m) { m.classList.remove("is-open"); });
    }
  });

  /* ── Copy seed to clipboard ────────────────────────────────────────── */
  SB.copySeed = function (el) {
    var text = el.textContent || el.innerText;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text.trim()).then(function () {
        var orig = el.textContent;
        el.textContent = "Copied!";
        setTimeout(function () { el.textContent = orig; }, 1200);
      });
    }
  };

  /* ── Button loading state ──────────────────────────────────────────── */
  SB.setLoading = function (btn, loading) {
    if (loading) {
      btn.classList.add("sb-btn--loading");
      btn.disabled = true;
    } else {
      btn.classList.remove("sb-btn--loading");
      btn.disabled = false;
    }
  };

  // Expose globally
  window.SB = SB;
})();
