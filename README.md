# Rahul Drabit Chowdhury - Research Portfolio

A static academic and professional portfolio for Rahul Drabit Chowdhury. The site is intentionally framework-free so it can be published directly through GitHub Pages.

## Structure

- `index.html`, `research.html`, `publications.html`, `experience.html`, `education.html`, `opensource.html`, `projects.html`, and `contact.html` provide dedicated, accessible pages for each section.
- `css/styles.css` contains the responsive light-default/dark theme system.
- `js/app.js` loads local JSON records and dynamically renders section components.
- `data/*.json` contains curated records (profile, research, publications, education, experience, skills, projects) and generated GitHub metadata.
- `scripts/sync_github.py` refreshes approved public GitHub contributions.
- `.github/workflows/validate.yml` checks every change.
- `.github/workflows/sync.yml` opens a review pull request when GitHub data changes.

## Content ownership

Biography, education, experience, research, publications, projects, and skills are curated records. GitHub contribution metadata is generated only from repositories listed in `data/github-sync.json`. The sync workflow never publishes directly to `main` and does not rewrite authored narrative content.

## Local preview

Run a static server from the repository root, for example:

```powershell
python -m http.server 8000
```

Then open `http://localhost:8000`.

Opening `index.html` directly will not load JSON data in browsers that block local module requests, so use a local server for previewing the complete page.

## GitHub sync

The scheduled workflow uses the built-in GitHub Actions token and runs every six hours. It can also be started manually with `workflow_dispatch`. The generated data is reviewed through a pull request before it reaches the published site.
