import difflib
from typing import Any, cast

from agents import FunctionTool, function_tool

from app.tools.base import BaseAgentTools


class ExtractorAgentTools(BaseAgentTools):
    def get_all(self) -> list[FunctionTool]:
        return [
            function_tool(func)
            for func in (
                self.get_snapshot,
                self.search_elements,
            )
        ]

    async def get_snapshot(self, depth: int | None = None) -> str:
        """Get current page accessibility snapshot with element references.
        The snapshot shows the page structure
        in YAML format with [ref=eX] references
        that can be used with other tools to interact with elements."""
        page = await self.get_active_page()
        snapshot = await page.locator('body').aria_snapshot(
            mode='ai', depth=depth
        )
        return snapshot

    async def search_elements(
        self, keywords: list[str], max_results: int = 10
    ) -> str:
        """Search page elements by keywords (case-insensitive)
        and return a ranked list of matches.

        Parses the page DOM, ranks visible elements by how well
        their text/label matches the keywords (closest matches first),
        and returns compact lines
        like: [s0] button "Subscribe" (matched: subscribe | score=1.00).
        The refs (s0, s1, ...) can be passed directly to click_element,
        type_into_element and press_key_on_element.

        Args:
            keywords: List of keywords/phrases to look for.
            max_results: Maximum number of matches to return (default 10).

        Returns:
            Ranked, newline-separated list of matching elements with refs."""

        if not keywords:
            return 'No keywords provided.'

        keywords = [kw.lower().strip() for kw in keywords if kw.strip()]

        page = await self.get_active_page()
        candidates = await page.evaluate(SEARCH_JS)

        scored: list[tuple[float, list[str], dict[str, Any]]] = []
        for cand in candidates:
            score, matched = self._score_candidate(cand, keywords)
            if score > 0:
                scored.append((score, matched, cand))

        # Highest score first; ties broken by shorter text (more specific).
        scored.sort(key=lambda x: (-x[0], len(x[2].get('text') or '')))

        if not scored:
            quoted = ', '.join(f'"{kw}"' for kw in keywords)
            return f'No elements match the keywords: {quoted}.'

        top = scored[: max(0, max_results)]
        lines = []
        for score, matched, cand in top:
            ref = cand['ref']
            label = self._candidate_label(cand)
            snippet = (cand.get('text') or '').strip().replace('\n', ' ')
            if len(snippet) > 80:
                snippet = snippet[:77] + '...'
            kw_part = ', '.join(matched)
            lines.append(
                f'[{ref}] {label} "{snippet}" '
                f'(matched: {kw_part} | score={score:.2f})'
            )
        return '\n'.join(lines)

    @staticmethod
    def _candidate_label(cand: dict[str, Any]) -> str:
        tag = cand.get('tag', '?')
        if tag == 'input':
            itype = cand.get('type') or 'text'
            return f'input[{itype}]'
        return cast(str, tag)

    @staticmethod
    def _score_candidate(
        cand: dict[str, Any], keywords: list[str]
    ) -> tuple[float, list[str]]:
        searchable = cand.get('searchable', '')
        score = 0.0
        matched: list[str] = []
        for kw in keywords:
            if kw in searchable:
                score += 1.0
                matched.append(kw)
            else:
                ratio = difflib.SequenceMatcher(None, kw, searchable).ratio()
                if ratio >= 0.6:
                    score += ratio * 0.5
                    matched.append(kw)

        # Bias toward directly interactable elements so the clickable target
        # ranks above a non-interactive wrapper that shares the same text.
        # Only applied when the element actually matched a keyword, otherwise
        # unrelated interactive elements would always leak into the results.
        if score > 0:
            tag = cand.get('tag')
            role = cand.get('role')
            if tag in _INTERACTIVE_TAGS or role == 'button':
                score += 0.05
        return score, matched


# Tags that map directly to an interactable target (used to bias ranking).
_INTERACTIVE_TAGS = {'button', 'a', 'input', 'textarea', 'select'}

# ruff: disable[E501]
SEARCH_JS = r"""
() => {
  // Clear stale search refs from a previous call.
  document.querySelectorAll('[data-agent-ref]').forEach(function (el) {
    el.removeAttribute('data-agent-ref');
  });

  var MAX = 500;
  var TEXT_LIMIT = 250;

  function isVisible(el) {
    var rect = el.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) return false;
    var style = getComputedStyle(el);
    return style.visibility !== 'hidden' && style.display !== 'none';
  }

  var candidates = [];
  var counter = 0;
  var all = document.querySelectorAll('body *');
  for (var i = 0; i < all.length; i++) {
    var el = all[i];
    if (!isVisible(el)) continue;

    var ariaLabel = el.getAttribute('aria-label') || '';
    var placeholder = el.getAttribute('placeholder') || '';
    var title = el.getAttribute('title') || '';
    var name = el.getAttribute('name') || '';
    var value = el.value || '';
    var alt = el.getAttribute('alt') || '';
    var inner = (el.innerText || '').replace(/\s+/g, ' ').trim();
    var searchable = [ariaLabel, placeholder, title, name, value, alt, inner]
      .join(' ')
      .toLowerCase();
    if (!searchable.trim()) continue;

    var ref = 's' + counter;
    el.setAttribute('data-agent-ref', ref);
    var type =
      el.tagName === 'INPUT'
        ? el.getAttribute('type') || 'text'
        : undefined;

    candidates.push({
      ref: ref,
      tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role') || undefined,
      name: name || undefined,
      type: type,
      text: inner.slice(0, TEXT_LIMIT),
      searchable: searchable.slice(0, TEXT_LIMIT),
    });

    counter++;
    if (counter >= MAX) break;
  }
  return candidates;
}
"""
# ruff: enable[E501]
