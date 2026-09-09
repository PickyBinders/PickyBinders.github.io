---
title: "Resources"
layout: gridlay
permalink: /resources/
description: "Courses, tutorials, slides and Journal Club podcasts."
---

<div class="page-heading">
  <h1 class="page-title">{% include title-glyph.html glyph="☀" %}<span>Resources</span></h1>
  <p class="page-intro">Courses · Tutorials · Slides · Podcasts</p>
</div>

<div class="resource-list">
  {% assign resources = site.teaching | sort: 'date' | reverse %}
  {% assign cutoff = site.resources_since | date: '%Y-%m-%d' %}
  {% for item in resources %}
  {% assign resource_date = item.date | date: '%Y-%m-%d' %}
  {% if resource_date < cutoff %}{% continue %}{% endif %}
  <article class="resource-row">
    <div><time datetime="{{ item.date | date_to_xmlschema }}">{{ item.date | date: '%b %Y' }}</time><span class="resource-kind">{{ item.kind | default: 'Resource' }}</span></div>
    <div><h2>{{ item.title | remove: '<p>' | remove: '</p>' }}</h2>{% if item.authors %}<p>{% for author in item.authors %}{{ author.name }}{% unless forloop.last %}, {% endunless %}{% endfor %}</p>{% endif %}{% if item.technical_support %}<p>Technical support: {{ item.technical_support }}</p>{% endif %}</div>
    <div class="resource-links">
      {% if item.html %}<a class="button button-secondary" href="{{ item.html }}" target="_blank" rel="noopener">{{ item.link_label | default: 'Open material' }}</a>
      {% elsif item.slides %}<a class="button button-secondary" href="{{ '/assets/pdf/' | append: item.slides | relative_url }}">View slides</a>
      {% else %}<a class="button button-secondary" href="{{ item.url | relative_url }}">View resource</a>{% endif %}
      {% if item.preprint %}<a class="button button-secondary" href="{{ item.preprint }}" target="_blank" rel="noopener">Preprint ↗</a>{% endif %}
    </div>
  </article>
  {% endfor %}
</div>
