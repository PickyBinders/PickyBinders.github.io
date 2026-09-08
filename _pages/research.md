---
title: "Research"
layout: gridlay
permalink: /research/
description: "Molecular interactions, protein representations and protein design."
---

<div class="page-heading"><h1 class="page-title">{% include title-glyph.html glyph="💡" %}<span>Research</span></h1><p class="page-intro">Structure · Interaction · Design</p></div>
{% for theme in site.data.research_themes %}
<section class="research-section" id="{{ theme.id }}">
  <div class="research-heading"><span class="theme-number">0{{ forloop.index }}</span><h2>{{ theme.title }}</h2></div>
  <div class="project-grid">
    {% assign projects = site.projects | sort: 'importance' %}
    {% for project in projects %}{% if project.research_area == theme.id and project.show_in_research != false %}{% include project-card.html project=project %}{% endif %}{% endfor %}
  </div>
</section>
{% endfor %}
