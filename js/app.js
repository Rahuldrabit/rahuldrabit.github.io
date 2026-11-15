const DATA_FILES = {
  research: '../data/research.json',
  publications: '../data/publications.json',
  experience: '../data/experience.json',
  projects: '../data/projects.json',
  education: '../data/education.json',
  skills: '../data/skills.json',
  github: '../data/github.json'
};

const escapeHtml = (value = '') => String(value)
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#039;');

const safeUrl = (value = '#') => {
  try {
    const url = new URL(value, window.location.href);
    return ['http:', 'https:', 'mailto:'].includes(url.protocol) ? url.href : '#';
  } catch {
    return '#';
  }
};

const linkAttrs = (url) => {
  const external = /^https?:\/\//.test(url);
  return external ? ' target="_blank" rel="noopener noreferrer"' : '';
};

function setupTheme() {
  const root = document.documentElement;
  const button = document.querySelector('.theme-toggle');
  if (!button) return;
  const updateButton = () => {
    const dark = root.dataset.theme === 'dark';
    button.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
    button.title = dark ? 'Switch to light theme' : 'Switch to dark theme';
  };
  button.addEventListener('click', () => {
    const nextTheme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = nextTheme;
    try {
      localStorage.setItem('theme', nextTheme);
    } catch {
      // The theme still works when browser storage is unavailable.
    }
    updateButton();
  });
  updateButton();
}

function setupMenu() {
  const toggle = document.querySelector('.menu-toggle');
  const menu = document.querySelector('.nav-menu');
  if (!toggle || !menu) return;
  const setOpen = (open) => {
    menu.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.querySelector('.menu-icon').textContent = open ? '×' : '☰';
    toggle.querySelector('.sr-only').textContent = open ? 'Close navigation' : 'Open navigation';
  };
  toggle.addEventListener('click', () => setOpen(!menu.classList.contains('is-open')));
  menu.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setOpen(false)));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menu.classList.contains('is-open')) {
      setOpen(false);
      toggle.focus();
    }
  });
  window.matchMedia('(max-width: 1050px)').addEventListener('change', () => setOpen(false));
}

function setupReveal() {
  const elements = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    elements.forEach((element) => element.classList.add('is-visible'));
    return;
  }
  const observer = new IntersectionObserver((entries, currentObserver) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        currentObserver.unobserve(entry.target);
      }
    });
  }, { threshold: .12 });
  elements.forEach((element) => {
    element.classList.add('reveal-pending');
    observer.observe(element);
  });
}

function renderResearch(records = []) {
  return records.map((record) => {
    const url = record.url ? safeUrl(record.url) : '#';
    const tag = url === '#' ? 'article' : 'a';
    const attrs = tag === 'a' ? ` href="${escapeHtml(url)}"${linkAttrs(record.url)}` : '';
    return `<${tag} class="research-item"${attrs}>
    <div><div class="research-title">${escapeHtml(record.title)}</div><div class="research-meta">${escapeHtml(record.area || 'Research in progress')}</div></div>
    <span class="research-status">${escapeHtml(record.status || 'Ongoing')}</span>
  </${tag}>`;
  }).join('');
}

function renderPublications(records = []) {
  if (!Array.isArray(records) || records.length === 0) {
    return `<div class="empty-state">
      <p class="empty-title">Publications forthcoming</p>
      <p class="empty-desc">Peer-reviewed conference papers, journal articles, and referee-accepted publications are currently in preparation and under review. Once published, complete bibliographic citations, DOIs, and links will appear here.</p>
      <div class="empty-links link-row">
        <a href="https://scholar.google.com/citations?user=BV6XABcAAAAJ&hl=en" target="_blank" rel="noopener noreferrer">Google Scholar Profile ↗</a>
        <a href="https://www.researchgate.net/profile/Rahul-Chowdhury-12" target="_blank" rel="noopener noreferrer">ResearchGate Profile ↗</a>
      </div>
    </div>`;
  }
  return records.map((record) => {
    const period = record.date || record.year || '';
    const metaParts = [record.venue, period].filter(Boolean);
    const metaText = metaParts.map(escapeHtml).join(' · ');
    const doiBadge = record.doi
      ? `<span class="publication-doi">· DOI: <a href="${escapeHtml(safeUrl(`https://doi.org/${record.doi}`))}"${linkAttrs(`https://doi.org/${record.doi}`)}>${escapeHtml(record.doi)}</a></span>`
      : '';
    const linksList = Array.isArray(record.links) && record.links.length > 0
      ? `<div class="publication-links link-row">${record.links.map((link) => `<a href="${escapeHtml(safeUrl(link.url || '#'))}"${linkAttrs(link.url || '')}>${escapeHtml(link.label || 'Link')} ↗</a>`).join('')}</div>`
      : '';

    return `<article class="publication-item">
      <div class="publication-main">
        <h3 class="publication-title"><a href="${escapeHtml(safeUrl(record.url || '#'))}"${linkAttrs(record.url || '')}>${escapeHtml(record.title)}</a></h3>
        <div class="publication-meta">${metaText} ${doiBadge}</div>
        ${linksList}
      </div>
      <span class="research-status">${escapeHtml(record.type || 'Paper')}</span>
    </article>`;
  }).join('');
}

function renderExperience(records = []) {
  return records.map((record) => `<article class="timeline-item"><div class="timeline-date">${escapeHtml(record.period)}<br>${escapeHtml(record.location || '')}</div><div><div class="timeline-role">${escapeHtml(record.role)}</div><div class="timeline-org">${escapeHtml(record.organization)}</div><p class="timeline-description">${escapeHtml(record.description)}</p><div class="tag-list">${(record.tags || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}</div></div></article>`).join('');
}

function renderProjects(records = []) {
  return records.map((record, index) => `<a class="project-card${record.featured ? ' project-card-featured' : ''}" href="${escapeHtml(safeUrl(record.url || '#'))}"${linkAttrs(record.url || '')}><div class="project-card-top"><span class="project-number">0${index + 1} / ${escapeHtml(record.type || 'Project')}</span><span class="project-status">${escapeHtml(record.status || 'Selected work')}</span></div><h3>${escapeHtml(record.title)}</h3><p>${escapeHtml(record.description)}</p><div class="tag-list">${(record.tags || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}</div></a>`).join('');
}

function renderEducation(records = []) {
  return records.map((record) => `<article class="education-item"><div class="education-degree">${escapeHtml(record.degree)}</div><div class="education-meta">${escapeHtml(record.institution)} · ${escapeHtml(record.period)} · ${escapeHtml(record.location || '')}</div></article>`).join('');
}

function renderSkills(groups = []) {
  return groups.map((group) => `<div class="skill-group"><h3>${escapeHtml(group.name)}</h3><p>${(group.items || []).map(escapeHtml).join(' · ')}</p></div>`).join('');
}

function updateGithubMetadata(data) {
  const updated = document.querySelector('#github-updated');
  if (updated && data.generatedAt) updated.textContent = `Last sync: ${new Date(data.generatedAt).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}`;
  const prs = document.querySelector('#metric-prs');
  if (prs && Number.isInteger(data.metrics?.mergedPrs) && data.metrics.mergedPrs >= 0) prs.textContent = `${data.metrics.mergedPrs}+`;
}

function renderGithub(data = {}) {
  const records = data.contributions || [];
  return records.map((record) => `<a class="contribution-card" href="${escapeHtml(safeUrl(record.url || '#'))}"${linkAttrs(record.url || '')}><span class="card-kicker">${escapeHtml(record.repository)} · PR #${escapeHtml(record.number)}</span><h3>${escapeHtml(record.title)}</h3><p>${escapeHtml(record.summary || 'Open-source contribution')}</p><div class="card-footer"><span>${escapeHtml(record.status || 'Reviewed')}</span><strong>${escapeHtml(record.mergedAt || record.updatedAt || '')}</strong></div></a>`).join('');
}

const SECTIONS = {
  research: { data: 'research', render: renderResearch, label: 'Research records' },
  publications: { data: 'publications', render: renderPublications, label: 'Publication records' },
  experience: { data: 'experience', render: renderExperience, label: 'Experience records' },
  products: { data: 'projects', render: (records) => renderProjects(records.filter((record) => record.category === 'live-product')), label: 'Product records' },
  framework: { data: 'projects', render: (records) => renderProjects(records.filter((record) => record.category === 'engineering-framework')), label: 'Framework records' },
  'research-projects': { data: 'projects', render: (records) => renderProjects(records.filter((record) => ['research-system', 'research-project'].includes(record.category))), label: 'Research records' },
  education: { data: 'education', render: renderEducation, label: 'Education records' },
  skills: { data: 'skills', render: renderSkills, label: 'Skill records' },
  github: { data: 'github', render: renderGithub, label: 'GitHub contributions' }
};

function validateData(key, data) {
  const records = key === 'github' ? data?.contributions : data;
  if (!Array.isArray(records) || records.some((record) => !record || typeof record !== 'object' || Array.isArray(record))) {
    throw new Error(`Invalid ${key} records`);
  }
  if (key === 'github' && (!Number.isInteger(data.metrics?.mergedPrs) || data.metrics.mergedPrs < 0)) {
    throw new Error('Invalid GitHub metrics');
  }
}

async function loadData() {
  const targets = [...document.querySelectorAll('[data-section]')];
  const required = new Set(targets.map((target) => SECTIONS[target.dataset.section]?.data).filter(Boolean));
  if (document.querySelector('#metric-prs')) required.add('github');
  if (document.querySelector('#metric-projects')) required.add('research');

  await Promise.all([...required].map(async (key) => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    const affected = targets.filter((target) => SECTIONS[target.dataset.section]?.data === key);
    try {
      const response = await fetch(new URL(DATA_FILES[key], import.meta.url), { signal: controller.signal });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      validateData(key, data);
      affected.forEach((target) => {
        const section = SECTIONS[target.dataset.section];
        try {
          target.innerHTML = section.render(data);
        } catch (error) {
          target.innerHTML = `<p class="loading-state">${section.label} are temporarily unavailable.</p>`;
          console.warn(`Could not render ${target.dataset.section}`, error);
        }
      });
      if (key === 'github') updateGithubMetadata(data);
      if (key === 'research') {
        const metric = document.querySelector('#metric-projects');
        if (metric) metric.textContent = `${data.length}+`;
      }
    } catch (error) {
      console.warn(`Could not load ${key} data`, error);
      affected.forEach((target) => {
        target.innerHTML = `<p class="loading-state">${SECTIONS[target.dataset.section].label} are temporarily unavailable.</p>`;
      });
    } finally {
      clearTimeout(timeout);
    }
  }));
}

setupTheme();
setupMenu();
setupReveal();
const yearEl = document.querySelector('#current-year');
if (yearEl) yearEl.textContent = String(new Date().getFullYear());
loadData();
