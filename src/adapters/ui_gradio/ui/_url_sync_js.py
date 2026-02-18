"""Browser URL-sync script generation for the Gradio SPA router.

Extracted from ``app.py`` to reduce that module's size.
"""

from __future__ import annotations

import json
from typing import Dict

from adapters.ui_gradio.ui.router import PAGE_TO_URL

# Elem-ID of each page container (must match what build_*_page sets).
ELEM_ID_TO_PAGE: Dict[str, str] = {
    "page-home": "home",
    "page-list-scenarios": "list_scenarios",
    "page-scenario-detail": "scenario_detail",
    "page-create-scenario": "create_scenario",
    "page-edit-scenario": "edit_scenario",
    "page-favorites": "favorites",
}


def build_url_sync_head_js() -> str:
    """Return a ``<script>`` tag that keeps the browser URL in sync.

    Client-side behaviour:
    1. **MutationObserver** — watches each page container for
       attribute changes.  When a container becomes visible,
       it pushes the matching URL via ``history.pushState``.
    2. **popstate** — handles browser back/forward by showing
       the correct page container directly via style manipulation.
    """
    # Python dicts → JS object literals
    elem_to_page_js = json.dumps(ELEM_ID_TO_PAGE)
    page_to_url_js = json.dumps(PAGE_TO_URL)

    # Reverse map: page name → elem id
    page_to_elem_js = json.dumps({v: k for k, v in ELEM_ID_TO_PAGE.items()})

    return (
        "<script>\n"
        "(function() {\n"
        f"  var ELEM_TO_PAGE = {elem_to_page_js};\n"
        f"  var PAGE_TO_URL  = {page_to_url_js};\n"
        f"  var PAGE_TO_ELEM = {page_to_elem_js};\n"
        "\n"
        "  /* 1. Push URL when a page container becomes visible */\n"
        "  function _getInputVal(elemId) {\n"
        "    var c = document.getElementById(elemId);\n"
        "    if (!c) return '';\n"
        "    var inp = c.querySelector('textarea') || c.querySelector('input');\n"
        "    return inp ? inp.value : '';\n"
        "  }\n"
        "\n"
        "  function startObserver() {\n"
        "    var observer = new MutationObserver(function(mutations) {\n"
        "      for (var i = 0; i < mutations.length; i++) {\n"
        "        var el = mutations[i].target;\n"
        "        var pageName = ELEM_TO_PAGE[el.id];\n"
        "        if (!pageName) continue;\n"
        "        var isVisible = el.offsetParent !== null\n"
        "                        || getComputedStyle(el).display !== 'none';\n"
        "        if (isVisible) {\n"
        "          var targetUrl = PAGE_TO_URL[pageName];\n"
        "          if (targetUrl) {\n"
        "            /* Create container is shared: check editing mirror */\n"
        "            if (pageName === 'create_scenario') {\n"
        "              var eid = _getInputVal('editing-card-id-mirror');\n"
        "              if (eid) {\n"
        "                targetUrl = PAGE_TO_URL['edit_scenario'] + '?id=' + encodeURIComponent(eid);\n"
        "                pageName = 'edit_scenario';\n"
        "              }\n"
        "            }\n"
        "            var current = window.location.pathname + window.location.search;\n"
        "            if (current !== targetUrl) {\n"
        "              history.pushState({page: pageName}, '', targetUrl);\n"
        "            }\n"
        "          }\n"
        "        }\n"
        "      }\n"
        "    });\n"
        "    var ids = Object.keys(ELEM_TO_PAGE);\n"
        "    for (var j = 0; j < ids.length; j++) {\n"
        "      var el = document.getElementById(ids[j]);\n"
        "      if (el) observer.observe(el, { attributes: true });\n"
        "    }\n"
        "  }\n"
        "\n"
        "  /* 2. Handle browser back/forward — hide/show containers */\n"
        "  window.addEventListener('popstate', function(e) {\n"
        "    var page = (e.state && e.state.page) ? e.state.page : 'home';\n"
        "    /* edit_scenario reuses create_scenario container */\n"
        "    var showPage = (page === 'edit_scenario') ? 'create_scenario' : page;\n"
        "    var allIds = Object.keys(ELEM_TO_PAGE);\n"
        "    for (var k = 0; k < allIds.length; k++) {\n"
        "      var container = document.getElementById(allIds[k]);\n"
        "      if (!container) continue;\n"
        "      var shouldShow = (ELEM_TO_PAGE[allIds[k]] === showPage);\n"
        "      container.style.display = shouldShow ? '' : 'none';\n"
        "    }\n"
        "  });\n"
        "\n"
        "  /* 3. Detail page: replace URL with ?id=<card_id> when mirror updates */\n"
        "  var _lastDetailMirror = '';\n"
        "  var _lastEditMirror = '';\n"
        "  setInterval(function() {\n"
        "    /* Detail view mirror */\n"
        "    var dval = _getInputVal('detail-card-id-mirror');\n"
        "    if (dval && dval !== _lastDetailMirror) {\n"
        "      _lastDetailMirror = dval;\n"
        "      var detailEl = document.getElementById('page-scenario-detail');\n"
        "      if (detailEl && (detailEl.offsetParent !== null\n"
        "                       || getComputedStyle(detailEl).display !== 'none')) {\n"
        "        var url = PAGE_TO_URL['scenario_detail'] + '?id=' + encodeURIComponent(dval);\n"
        "        var current = window.location.pathname + window.location.search;\n"
        "        if (current !== url) {\n"
        "          history.replaceState({page: 'scenario_detail'}, '', url);\n"
        "        }\n"
        "      }\n"
        "    }\n"
        "    /* Edit form mirror */\n"
        "    var eval2 = _getInputVal('editing-card-id-mirror');\n"
        "    if (eval2 && eval2 !== _lastEditMirror) {\n"
        "      _lastEditMirror = eval2;\n"
        "      var createEl = document.getElementById('page-create-scenario');\n"
        "      if (createEl && (createEl.offsetParent !== null\n"
        "                       || getComputedStyle(createEl).display !== 'none')) {\n"
        "        var url2 = PAGE_TO_URL['edit_scenario'] + '?id=' + encodeURIComponent(eval2);\n"
        "        var cur2 = window.location.pathname + window.location.search;\n"
        "        if (cur2 !== url2) {\n"
        "          history.replaceState({page: 'edit_scenario'}, '', url2);\n"
        "        }\n"
        "      }\n"
        "    }\n"
        "    /* When editing mirror clears and create form is visible, revert to /sb/create/ */\n"
        "    if (!eval2 && _lastEditMirror) {\n"
        "      _lastEditMirror = '';\n"
        "      var createEl2 = document.getElementById('page-create-scenario');\n"
        "      if (createEl2 && (createEl2.offsetParent !== null\n"
        "                        || getComputedStyle(createEl2).display !== 'none')) {\n"
        "        var cur3 = window.location.pathname + window.location.search;\n"
        "        if (cur3 !== PAGE_TO_URL['create_scenario']) {\n"
        "          history.replaceState({page: 'create_scenario'}, '', PAGE_TO_URL['create_scenario']);\n"
        "        }\n"
        "      }\n"
        "    }\n"
        "  }, 300);\n"
        "\n"
        "  /* Boot — start observer after Gradio renders */\n"
        "  if (document.readyState === 'loading') {\n"
        "    document.addEventListener('DOMContentLoaded', function() {\n"
        "      setTimeout(startObserver, 800);\n"
        "    });\n"
        "  } else {\n"
        "    setTimeout(startObserver, 800);\n"
        "  }\n"
        "})();\n"
        "</script>"
    )
