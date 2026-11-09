(function () {
  "use strict";

  function initSidebar() {
    var toggle = document.getElementById("menu-toggle");
    var sidebar = document.getElementById("sidebar");
    var overlay = document.getElementById("sidebar-overlay");
    if (!toggle || !sidebar || !overlay) return;

    function close() {
      sidebar.classList.remove("is-open");
      overlay.classList.remove("is-open");
    }

    toggle.addEventListener("click", function () {
      sidebar.classList.toggle("is-open");
      overlay.classList.toggle("is-open", sidebar.classList.contains("is-open"));
    });

    overlay.addEventListener("click", close);
    sidebar.querySelectorAll("a.nav-link").forEach(function (link) {
      link.addEventListener("click", close);
    });
    window.addEventListener("keydown", function (event) {
      if (event.key === "Escape") close();
    });
  }

  function initFlash() {
    document.querySelectorAll(".flash").forEach(function (flash) {
      var closeBtn = flash.querySelector(".flash-close");
      if (closeBtn) {
        closeBtn.addEventListener("click", function () {
          flash.classList.add("is-leaving");
          setTimeout(function () { flash.remove(); }, 220);
        });
      }
    });

    var autoClose = document.querySelectorAll(".flash-success, .flash-info");
    autoClose.forEach(function (flash) {
      setTimeout(function () {
        if (!flash.isConnected) return;
        flash.classList.add("is-leaving");
        setTimeout(function () { flash.remove(); }, 220);
      }, 5000);
    });
  }

  function initConfirm() {
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
      form.addEventListener("submit", function (event) {
        if (!window.confirm(form.getAttribute("data-confirm"))) {
          event.preventDefault();
        }
      });
    });
  }

  function initDemoChips() {
    var username = document.getElementById("username");
    var password = document.getElementById("password");
    if (!username || !password) return;

    document.querySelectorAll(".demo-chip[data-username]").forEach(function (chip) {
      chip.addEventListener("click", function () {
        username.value = chip.getAttribute("data-username");
        password.value = chip.getAttribute("data-password");
        username.focus();
      });
    });
  }

  function initCoverPreview() {
    var preview = document.getElementById("cover-preview");
    if (!preview) return;

    var titleInput = document.querySelector("[data-preview-title]");
    var authorInput = document.querySelector("[data-preview-author]");
    var colorInput = document.getElementById("cover_color");
    var titleLabel = document.getElementById("preview-title");
    var authorLabel = document.getElementById("preview-author");

    function syncTitle() {
      if (titleLabel && titleInput) titleLabel.textContent = titleInput.value.trim() || "Tên sách";
    }
    function syncAuthor() {
      if (authorLabel && authorInput) authorLabel.textContent = authorInput.value.trim() || "Tác giả";
    }
    function syncColor(color) {
      preview.style.setProperty("--cover", color);
      if (colorInput) colorInput.value = color;
    }

    if (titleInput) titleInput.addEventListener("input", syncTitle);
    if (authorInput) authorInput.addEventListener("input", syncAuthor);
    if (colorInput) colorInput.addEventListener("input", function () { syncColor(colorInput.value); });

    document.querySelectorAll(".swatch[data-color]").forEach(function (swatch) {
      swatch.addEventListener("click", function () { syncColor(swatch.getAttribute("data-color")); });
    });
  }

  function initResponsiveTables() {
    document.querySelectorAll(".data-table").forEach(function (table) {
      var headers = Array.prototype.map.call(
        table.querySelectorAll("thead th"),
        function (th) { return th.textContent.trim(); }
      );
      table.querySelectorAll("tbody tr").forEach(function (row) {
        Array.prototype.forEach.call(row.children, function (cell, index) {
          if (headers[index]) cell.setAttribute("data-label", headers[index]);
        });
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initSidebar();
    initFlash();
    initConfirm();
    initDemoChips();
    initCoverPreview();
    initResponsiveTables();
  });
})();
