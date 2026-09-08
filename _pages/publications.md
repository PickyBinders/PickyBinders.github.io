---
title: "Publications"
layout: gridlay
permalink: /publications/
description: "Selected papers and publications from Google Scholar, from 2023 onward."
---

<div class="page-heading"><h1 class="page-title">{% include title-glyph.html glyph="🦉" %}<span>Publications</span></h1><p class="page-intro"><a href="{{ site.links.google_scholar }}">Google Scholar ↗</a>{% if site.data.publication_sync.updated %}<span class="sync-date">Updated {{ site.data.publication_sync.updated | date: '%-d %b %Y' }}</span>{% endif %}</p></div>

<section aria-labelledby="selected-heading">
  <div class="section-heading"><h2 id="selected-heading">Selected papers</h2></div>
  <div class="work-grid">
    {% for rank in (1..4) %}{% for pair in site.data.publication_links %}{% assign extra = pair[1] %}{% if extra.featured == rank %}
      {% assign publication = site.data.publications | where: 'id', pair[0] | first %}
      {% if publication %}{% include publication.html publication=publication featured=true full_title=true %}{% endif %}
    {% endif %}{% endfor %}{% endfor %}
  </div>
</section>

<section class="all-publications" aria-labelledby="all-heading">
  <div class="section-heading"><h2 id="all-heading">Publications from 2023</h2><span class="section-note">{{ site.data.publications.size }} entries</span></div>
  <label class="visually-hidden" for="pubSearch">Filter publications</label>
  <input type="search" class="pub-search" id="pubSearch" placeholder="Title, author, year or topic…" aria-controls="pubList">
  <div id="pubList">
    {% assign years = site.data.publications | group_by: 'year' %}
    {% for year in years %}
    <section class="publication-year" data-publication-year>
      <h3 class="year-label">{% if year.name == '0' %}Undated{% else %}{{ year.name }}{% endif %}</h3>
      <div>{% for publication in year.items %}{% include publication.html publication=publication %}{% endfor %}</div>
    </section>
    {% endfor %}
  </div>
  <p id="pubEmpty" hidden role="status">No matching publications.</p>
</section>
