---
title: "Team"
layout: gridlay
permalink: /group/
description: "People, research interests and upcoming positions. Department of Computational Biology, University of Lausanne."
---

<div class="page-heading team-page-heading">
  <h1 class="page-title">{% include title-glyph.html glyph="🏵" %}<span>Team</span></h1>
  <picture>
    <source type="image/webp" srcset="{{ '/assets/img/team/group-640.webp' | relative_url }} 640w, {{ '/assets/img/team/group-1280.webp' | relative_url }} 1280w" sizes="(max-width: 700px) calc(100vw - 5rem), 640px">
    <img class="team-group-photo" src="{{ '/assets/img/team/group-1280.jpg' | relative_url }}" alt="Group photo" width="1982" height="1941" fetchpriority="high">
  </picture>
</div>

<section class="team-section" id="unil" aria-label="Current and upcoming members">
  <div class="team-grid">
    {% assign members = site.data.team_members | where: 'group', 'unil' | sort: 'order' %}
    {% for member in members %}{% include member-card.html member=member %}{% endfor %}
  </div>
</section>

<section class="team-section" id="collaboration" aria-label="Members in collaboration with the Schwede group">
  <p class="collaboration-intro">In collaboration with the <a href="{{ site.links.schwede }}">Schwede group</a>.</p>
  <div class="team-grid">
    {% assign members = site.data.team_members | where: 'group', 'schwede' | sort: 'order' %}
    {% for member in members %}{% include member-card.html member=member %}{% endfor %}
  </div>
</section>
