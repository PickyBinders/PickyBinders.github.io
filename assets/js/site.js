(function () {
  'use strict';

  var root = document.documentElement;
  var themeToggle = document.getElementById('darkModeToggle');

  function currentTheme() {
    return root.getAttribute('data-bs-theme') || 'light';
  }

  function syncThemeControl() {
    if (!themeToggle) return;
    var dark = currentTheme() === 'dark';
    themeToggle.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
  }

  if (themeToggle) {
    syncThemeControl();
    themeToggle.addEventListener('click', function () {
      var next = currentTheme() === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-bs-theme', next);
      try { localStorage.setItem('picky-theme', next); } catch (error) { /* Keep the in-memory choice. */ }
      syncThemeControl();
    });
  }

  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-toggle-target]');
    if (!button) return;
    var target = document.getElementById(button.getAttribute('data-toggle-target'));
    if (!target) return;
    var opening = !target.classList.contains('show');
    target.classList.toggle('show', opening);
    button.setAttribute('aria-expanded', String(opening));
    var symbol = button.querySelector('span[aria-hidden="true"]');
    if (symbol) symbol.textContent = opening ? '−' : '+';
  });

  var publicationSearch = document.getElementById('pubSearch');
  if (publicationSearch) {
    publicationSearch.addEventListener('input', function () {
      var query = publicationSearch.value.toLowerCase().trim();
      document.querySelectorAll('#pubList [data-pub-searchable]').forEach(function (entry) {
        var year = entry.closest('[data-publication-year]').querySelector('.year-label').textContent;
        entry.hidden = Boolean(query && !(year + ' ' + entry.textContent).toLowerCase().includes(query));
      });
      document.querySelectorAll('[data-publication-year]').forEach(function (year) {
        year.hidden = !year.querySelector('[data-pub-searchable]:not([hidden])');
      });
      document.getElementById('pubEmpty').hidden = Boolean(document.querySelector('#pubList [data-pub-searchable]:not([hidden])'));
    });
  }

  var searchToggle = document.getElementById('searchToggle');
  var searchOverlay = document.getElementById('searchOverlay');
  var searchInput = document.getElementById('searchInput');
  var searchResults = document.getElementById('searchResults');
  var searchData;
  var searchLoad;
  var searchTimer;
  var previousFocus;
  var background = [];

  function searchIsOpen() {
    return searchOverlay && searchOverlay.classList.contains('open');
  }

  function openSearch() {
    if (!searchOverlay || searchIsOpen()) return;
    previousFocus = document.activeElement;
    background = Array.from(document.querySelectorAll('body > nav, body > main, body > footer, body > .skip-link'))
      .map(function (element) { return { element: element, inert: element.inert }; });
    background.forEach(function (item) { item.element.inert = true; });
    searchOverlay.classList.add('open');
    searchOverlay.setAttribute('aria-hidden', 'false');
    searchToggle.setAttribute('aria-expanded', 'true');
    searchInput.focus();
  }

  function closeSearch() {
    if (!searchIsOpen()) return;
    window.clearTimeout(searchTimer);
    searchOverlay.classList.remove('open');
    searchOverlay.setAttribute('aria-hidden', 'true');
    searchToggle.setAttribute('aria-expanded', 'false');
    searchInput.value = '';
    searchResults.replaceChildren();
    searchResults.setAttribute('aria-busy', 'false');
    background.forEach(function (item) { item.element.inert = item.inert; });
    if (previousFocus && previousFocus.isConnected) previousFocus.focus();
  }

  function resultNode(item) {
    var link = document.createElement('a');
    link.className = 'search-result-item';
    link.href = item.url;
    var title = document.createElement('div');
    title.className = 'search-result-title';
    title.textContent = item.title;
    var snippet = document.createElement('div');
    snippet.className = 'search-result-snippet';
    snippet.textContent = item.content.slice(0, 160).trim() + (item.content.length > 160 ? '…' : '');
    link.append(title, snippet);
    return link;
  }

  function renderSearch(query) {
    searchResults.replaceChildren();
    if (!query) return;
    var needle = query.toLowerCase();
    var matches = searchData.filter(function (item) {
      return (item.title + ' ' + item.content).toLowerCase().includes(needle);
    }).slice(0, 10);
    if (!matches.length) {
      var empty = document.createElement('div');
      empty.className = 'search-no-results';
      empty.textContent = 'No results for “' + query + '”.';
      searchResults.appendChild(empty);
      return;
    }
    matches.forEach(function (item) { searchResults.appendChild(resultNode(item)); });
  }

  function runSearch() {
    if (!searchIsOpen() || !searchInput.value.trim()) return;
    if (searchData) { renderSearch(searchInput.value.trim()); return; }
    searchResults.setAttribute('aria-busy', 'true');
    if (!searchLoad) {
      searchLoad = fetch(searchOverlay.getAttribute('data-search-url'))
        .then(function (response) {
          if (!response.ok) throw new Error('Search index unavailable');
          return response.json();
        })
        .then(function (data) { searchData = data; })
        .finally(function () { searchLoad = null; });
    }
    searchLoad.then(function () {
      // A slow fetch must use the latest query, never the one that started it.
      if (searchIsOpen()) renderSearch(searchInput.value.trim());
    }).catch(function () {
      if (searchIsOpen() && searchInput.value.trim()) searchResults.textContent = 'The search index could not be loaded.';
    }).finally(function () { searchResults.setAttribute('aria-busy', 'false'); });
  }

  if (searchToggle && searchOverlay) {
    searchToggle.addEventListener('click', openSearch);
    document.getElementById('searchClose').addEventListener('click', closeSearch);
    searchOverlay.addEventListener('click', function (event) { if (event.target === searchOverlay) closeSearch(); });
    searchInput.addEventListener('input', function () {
      window.clearTimeout(searchTimer);
      searchResults.replaceChildren();
      searchResults.setAttribute('aria-busy', 'false');
      searchTimer = window.setTimeout(runSearch, 120);
    });
    document.addEventListener('keydown', function (event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        searchOverlay.classList.contains('open') ? closeSearch() : openSearch();
      } else if (event.key === 'Escape' && searchOverlay.classList.contains('open')) {
        closeSearch();
      } else if (event.key === 'Tab' && searchIsOpen()) {
        var focusable = Array.from(searchOverlay.querySelectorAll('input, button, a[href]'));
        var first = focusable[0];
        var last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    });
  }

  var navbar = document.querySelector('.navbar');
  window.addEventListener('scroll', function () {
    if (navbar) navbar.classList.toggle('scrolled', window.scrollY > 8);
  }, { passive: true });

}());
