/* CloudCart UI behaviour (presentation only - no API calls, no backend changes) */
(function () {
  "use strict";
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* navbar shadow on scroll */
  var nav = $(".cc-nav");
  var onScroll = function () { if (nav) nav.classList.toggle("scrolled", window.scrollY > 8); };
  window.addEventListener("scroll", onScroll, { passive: true }); onScroll();

  /* toasts (server-rendered, we only add dismiss behaviour) */
  function closeToast(t) { t.classList.add("out"); setTimeout(function () { t.remove(); }, 300); }
  $$(".cc-toast").forEach(function (t, i) {
    var x = $(".t-x", t); if (x) x.addEventListener("click", function () { closeToast(t); });
    setTimeout(function () { closeToast(t); }, 5000 + i * 400);
  });

  /* scroll reveal */
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { threshold: 0.08 });
    $$(".reveal").forEach(function (el) { io.observe(el); });
  } else { $$(".reveal").forEach(function (el) { el.classList.add("in"); }); }

  /* image skeleton -> fade in */
  $$("img[data-skel]").forEach(function (img) {
    var wrap = img.parentElement; wrap.classList.add("skel");
    var done = function () { wrap.classList.remove("skel"); img.style.opacity = 1; };
    img.style.opacity = 0;
    if (img.complete) done(); else { img.addEventListener("load", done); img.addEventListener("error", function () { img.src = "/static/images/placeholder.svg"; }); }
  });

  /* cart badge bump when count increases */
  var badge = $("#cartBadge");
  try {
    var now = badge ? parseInt(badge.textContent, 10) || 0 : 0;
    var prev = parseInt(sessionStorage.getItem("cc_cart") || "0", 10);
    if (badge && now > prev) badge.classList.add("bump");
    sessionStorage.setItem("cc_cart", String(now));
  } catch (e) {}

  /* quantity stepper on product page */
  $$("[data-qty]").forEach(function (box) {
    var input = $("input", box);
    $$("[data-step]", box).forEach(function (b) {
      b.addEventListener("click", function () {
        var v = (parseInt(input.value, 10) || 1) + parseInt(b.dataset.step, 10);
        var min = parseInt(input.min, 10) || 1, max = parseInt(input.max, 10) || 9999;
        input.value = Math.max(min, Math.min(max, v));
      });
    });
  });

  /* loading spinner on main submit buttons (never disables, so form values are still sent) */
  $$("form").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      var b = e.submitter;
      if (b && !b.name && b.classList.contains("btn-glow") && !e.defaultPrevented) {
        setTimeout(function () { b.classList.add("is-loading"); }, 0);
      }
    });
  });
  window.addEventListener("pageshow", function () { $$(".is-loading").forEach(function (b) { b.classList.remove("is-loading"); }); });

  /* confirm modal for <form data-confirm="..."> (replaces browser confirm()) */
  var modalEl = $("#confirmModal");
  if (modalEl && window.bootstrap) {
    var modal = new bootstrap.Modal(modalEl), pending = null;
    $$("form[data-confirm]").forEach(function (f) {
      f.addEventListener("submit", function (e) {
        e.preventDefault(); pending = f;
        $("#confirmText").textContent = f.dataset.confirm;
        modal.show();
      });
    });
    $("#confirmYes").addEventListener("click", function () { if (pending) { var f = pending; pending = null; modal.hide(); f.submit(); } });
  }

  /* tooltips */
  if (window.bootstrap) $$('[data-bs-toggle="tooltip"]').forEach(function (el) { new bootstrap.Tooltip(el); });

  /* image upload preview (admin product form) */
  var file = $("#imageInput"), prev2 = $("#imagePreview");
  if (file && prev2) file.addEventListener("change", function () {
    var f = file.files && file.files[0];
    if (f) { prev2.src = URL.createObjectURL(f); prev2.style.display = "block"; }
  });
})();
