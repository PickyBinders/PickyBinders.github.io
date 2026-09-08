---
title: "Home"
layout: homelay
permalink: /
description: "Context-aware deep learning for protein structure, interaction and design. Department of Computational Biology, University of Lausanne."
---

<section class="hero">
  <div class="hero-copy">
    <p class="hero-affiliation"><a href="{{ site.links.department }}">Department of Computational Biology</a><span><a href="https://www.unil.ch/">University of Lausanne</a></span></p>
    <h1>Context-aware<br>deep learning<span class="hero-subject">for protein structure,<br>interaction &amp; design.</span></h1>
    <div class="hero-actions"><a href="{{ '/research/' | relative_url }}">Research ↗</a><a href="{{ '/team/' | relative_url }}">People ↗</a></div>
  </div>
  <div class="hero-visual">
    <img class="logo-light" src="{{ '/assets/img/pb_logo_black.png' | relative_url }}" alt="Picky Binders" width="320" height="320">
    <img class="logo-dark" src="{{ '/assets/img/pb_logo_white.png' | relative_url }}" alt="Picky Binders" width="320" height="320">
    <p class="hero-logo-caption">(A.K.A Jay Lab)</p>
  </div>
</section>

<section class="theme-grid" aria-label="Research themes">
  {% for theme in site.data.research_themes %}
  <a class="theme-item" href="{{ '/research/' | relative_url }}#{{ theme.id }}">
    <span class="theme-number">0{{ forloop.index }}</span><h2>{{ theme.title }}</h2>
    <p>{{ theme.concepts | join: ' · ' }}</p>
  </a>
  {% endfor %}
</section>

<div class="home-updates home-section">
<section class="news-section">
  <div class="section-heading"><h2>News</h2><span class="section-note">From the group</span></div>
  {% include news.html limit=4 %}
</section>

<aside class="contact-panel" id="contact" aria-labelledby="contact-heading">
  <img src="{{ '/assets/img/janani-durairaj.jpg' | relative_url }}" alt="Jay (Janani Durairaj)" width="64" height="64" loading="lazy">
  <h2 id="contact-heading">Jay <span>(Janani Durairaj)</span></h2>
  <p>Assistant Professor</p>
  <p><a href="{{ site.links.department }}">Department of Computational Biology</a><br><a href="https://www.unil.ch/">University of Lausanne</a></p>
  <div class="project-links"><a href="mailto:{{ site.email }}">Email ↗</a><a href="{{ site.links.personal }}">Personal website ↗</a><a href="{{ site.links.google_scholar }}">Scholar ↗</a><a href="{{ site.links.github }}">GitHub ↗</a></div>
</aside>
</div>

<section class="home-section home-join">
  <div><h2>Upcoming positions</h2><p>PhD · Postdoc</p></div>
  <a href="mailto:{{ site.email }}">Interested? Email Jay ↗</a>
</section>
