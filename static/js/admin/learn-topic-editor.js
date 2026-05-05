(function () {
  function initEditor() {
    if (typeof SimpleMDE === "undefined") {
      return;
    }

    var textareas = document.querySelectorAll("textarea.js-rich-markdown");
    textareas.forEach(function (textarea) {
      if (textarea.dataset.richMarkdownInitialized) {
        return;
      }

      new SimpleMDE({
        element: textarea,
        spellChecker: false,
        status: ["lines", "words"],
        renderingConfig: {
          codeSyntaxHighlighting: false
        }
      });

      textarea.dataset.richMarkdownInitialized = "true";
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initEditor);
  } else {
    initEditor();
  }
})();
