const DATA_FILES = {
  profile: '../data/profile.json',
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
  const updateButton = () => {
    const dark = root.dataset.theme === 'dark';
    button.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
    button.title = dark ? 'Switch to light theme' : 'Switch to dark theme';
  };
  button.addEventListener('click', () => {
    const nextTheme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = nextTheme;
    localStorage.setItem('theme', nextTheme);
    updateButton();
  });
  updateButton();
}

function setupMenu() {
  const toggle = document.querySelector('.menu-toggle');
  const menu = document.querySelector('.nav-menu');
  toggle.addEventListener('click', () => {
    const open = menu.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.querySelector('.menu-icon').textContent = open ? '×' : '☰';
  });
  menu.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
    menu.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.querySelector('.menu-icon').textContent = '☰';
  }));
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
  elements.forEach((element) => observer.observe(element));
}

function renderResearch(records = []) {
  return records.map((record) => `<a class="research-item" href="${escapeHtml(safeUrl(record.url || '#'))}"${linkAttrs(record.url || '')}>
    <div><div class="research-title">${escapeHtml(record.title)}</div><div class="research-meta">${escapeHtml(record.area || 'Research in progress')}</div></div>
    <span class="research-status">${escapeHtml(record.status || 'Ongoing')}</span>
  </a>`).join('');
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

function renderGithub(data = {}) {
  const records = data.contributions || [];
  const updated = document.querySelector('#github-updated');
  if (updated && data.generatedAt) updated.textContent = `Last sync: ${new Date(data.generatedAt).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}`;
  const prs = document.querySelector('#metric-prs');
  if (prs && data.metrics?.mergedPrs) prs.textContent = `${data.metrics.mergedPrs}+`;
  return records.map((record) => `<a class="contribution-card" href="${escapeHtml(safeUrl(record.url || '#'))}"${linkAttrs(record.url || '')}><span class="card-kicker">${escapeHtml(record.repository)} · PR #${escapeHtml(record.number)}</span><h3>${escapeHtml(record.title)}</h3><p>${escapeHtml(record.summary || 'Open-source contribution')}</p><div class="card-footer"><span>${escapeHtml(record.status || 'Reviewed')}</span><strong>${escapeHtml(record.mergedAt || record.updatedAt || '')}</strong></div></a>`).join('');
}

async function loadData() {
  const entries = await Promise.all(Object.entries(DATA_FILES).map(async ([key, path]) => {
    try {
      let response = await fetch(path);
      if (!response.ok) {
        const altPath = path.startsWith('../') ? path.replace(/^\.\.\//, '') : ('../' + path);
        response = await fetch(altPath);
      }
      if (!response.ok) throw new Error(`${response.status}`);
      return [key, await response.json()];
    } catch (error) {
      console.warn(`Could not load ${key} data`, error);
      return [key, null];
    }
  }));
  return Object.fromEntries(entries);
}

function render(data) {
  const sections = {
    research: data.research ? renderResearch(data.research) : '<p class="loading-state">Research records are temporarily unavailable.</p>',
    publications: data.publications ? renderPublications(data.publications) : '<p class="loading-state">Publication records are temporarily unavailable.</p>',
    experience: data.experience ? renderExperience(data.experience) : '<p class="loading-state">Experience records are temporarily unavailable.</p>',
    products: data.projects ? renderProjects(data.projects.filter((record) => record.category === 'live-product')) : '<p class="loading-state">Product records are temporarily unavailable.</p>',
    framework: data.projects ? renderProjects(data.projects.filter((record) => record.category === 'engineering-framework')) : '<p class="loading-state">Framework records are temporarily unavailable.</p>',
    'research-projects': data.projects ? renderProjects(data.projects.filter((record) => record.category === 'research-system' || record.category === 'research-project')) : '<p class="loading-state">Research records are temporarily unavailable.</p>',
    education: data.education ? renderEducation(data.education) : '<p class="loading-state">Education records are temporarily unavailable.</p>',
    skills: data.skills ? renderSkills(data.skills) : '<p class="loading-state">Skill records are temporarily unavailable.</p>',
    github: data.github ? renderGithub(data.github) : '<p class="loading-state">GitHub snapshot is temporarily unavailable.</p>'
  };
  Object.entries(sections).forEach(([key, html]) => {
    const target = document.querySelector(`[data-section="${key}"]`);
    if (target) target.innerHTML = html;
  });
  const projectMetric = document.querySelector('#metric-projects');
  if (projectMetric && Array.isArray(data.research)) projectMetric.textContent = `${data.research.length}+`;
}

setupTheme();
setupMenu();
const yearEl = document.querySelector('#current-year');
if (yearEl) yearEl.textContent = String(new Date().getFullYear());
loadData().then(render).finally(setupReveal);
