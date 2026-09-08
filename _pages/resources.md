---
title: "Resources"
layout: gridlay
permalink: /resources/
description: "Courses, workshops, tutorials and slides."
---

<div class="page-heading">
  <h1 class="page-title">{% include title-glyph.html glyph="☀" %}<span>Resources</span></h1>
  <p class="page-intro">Courses · Tutorials · Slides</p>
</div>

<div class="resource-list">
  {% assign resources = site.teaching | sort: 'date' | reverse %}
  {% assign cutoff = site.resources_since | date: '%Y-%m-%d' %}
  {% for item in resources %}
  {% assign resource_date = item.date | date: '%Y-%m-%d' %}
  {% if resource_date < cutoff %}{% continue %}{% endif %}
  <article class="resource-row">
    <div><time datetime="{{ item.date | date_to_xmlschema }}">{{ item.date | date: '%Y' }}</time><span class="resource-kind">{{ item.kind | default: 'Resource' }}</span></div>
    <div><h2>{{ item.title | remove: '<p>' | remove: '</p>' }}</h2>{% if item.authors %}<p>{% for author in item.authors %}{{ author.name }}{% unless forloop.last %}, {% endunless %}{% endfor %}</p>{% endif %}</div>
    <div>
      {% if item.html %}<a class="button button-secondary" href="{{ item.html }}" target="_blank" rel="noopener">Open material</a>
      {% elsif item.slides %}<a class="button button-secondary" href="{{ '/assets/pdf/' | append: item.slides | relative_url }}">View slides</a>
      {% else %}<a class="button button-secondary" href="{{ item.url | relative_url }}">View resource</a>{% endif %}
    </div>
  </article>
  {% endfor %}
</div>
