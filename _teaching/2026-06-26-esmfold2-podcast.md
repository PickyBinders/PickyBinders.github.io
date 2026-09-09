---
layout: page
title: "Journal Club podcast"
description: "Our first recorded Journal Club podcast, hosted by Lorenzo, covers the ESMFold2 preprint."
date: 2026-06-26
kind: Podcast
html: https://youtu.be/cOOe_pKK2JQ
link_label: Listen
preprint: https://www.biorxiv.org/content/10.64898/2026.06.03.729735v1
preprint_title: Language Modeling Materializes a World Model of Protein Biology
authors:
  - name: Lorenzo Pantolini (host)
  - name: Ieva Pudžiuvelytė
  - name: Daniil Litvinov
  - name: Jay
  - name: Océane Follonier
  - name: Dylan Abramson
  - name: Diana Rapota
  - name: Tereza Kubatova
technical_support: Rok Breznikar
---

{{ page.description }}

{% for author in page.authors %}{{ author.name }}{% unless forloop.last %}, {% endunless %}{% endfor %}

Technical support: {{ page.technical_support }}.

[Listen to the episode]({{ page.html }}) · [{{ page.preprint_title }}]({{ page.preprint }})
