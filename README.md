# STEMEd+ Deadlines

Every deadline from across STEMEd+ Commons in one place, and in one calendar:
**https://jlib271.github.io/stemed-deadlines/**

Subscribe once in Google Calendar, Outlook, or Apple Calendar ("add calendar from URL"):

    https://jlib271.github.io/stemed-deadlines/feeds/all.ics

## Where the deadlines come from

Each day this site downloads the deadline calendars published by:

| Site | Calendar | What it holds |
|---|---|---|
| [STEMEd+ Funding](https://jlib271.github.io/stemed-funding/) | `feeds/deadlines.ics` | open calls for STEM+ education research and practice |
| [STEMEd+ Conferences](https://jlib271.github.io/stemed-conferences/) | `feeds/deadlines.ics` | proposal, registration, and travel-award deadlines |
| [STEMEd+ Professional Learning](https://jlib271.github.io/stemed-professional-learning/) | `feeds/deadlines.ics` | programs for K-12 teachers and informal educators |
| [STEMEd+ Faculty Development](https://jlib271.github.io/stemed-faculty-development/) | `feeds/deadlines.ics` | teaching professional development for college faculty, instructors, graduate students, and postdocs |

It keeps deadlines from today on, puts the site's name in front of each event (for example
`[Conferences] Proposals due: NARST 2027`), and writes:

| | |
|---|---|
| `index.html` | the page: deadlines grouped by day, "next 60 days" by default, with search and a site filter |
| `feeds/all.ics` | one calendar with every deadline |
| `feeds/<site>.ics` | one calendar per site (`funding`, `conferences`, `professional-learning`, `faculty-development`) |
| `embed.html` | a compact view with subscribe buttons, for embedding in another website (see below) |
| `deadlines.json` | everything listed |

If a site cannot be reached, its deadlines from the last published `deadlines.json` are kept, and the page says
which site was unreachable. To add or correct a deadline, use the site it comes from; this site only combines them.
Sites are listed in `config/sources.json`.

## How it works

A GitHub Actions workflow (`.github/workflows/update.yml`) runs every day after the other sites have rebuilt,
and on every push: it runs the tests, builds the site into `output/`, and publishes it to GitHub Pages. It needs
only the Python standard library.

Run it locally:

```sh
python -m unittest discover -s tests -t .
python -m stemed_deadlines --out output    # then open output/index.html through a local web server
```

To publish: Settings → Pages → Source: **GitHub Actions**.

STEMEd+ Deadlines is part of [STEMEd+ Commons](https://stemedplus.hcommons.org/).

## License

Code: MIT ([LICENSE](LICENSE)).

## Show the deadlines on another website

Paste this into a Custom HTML block (for example on a STEMEd+ Commons WordPress page):

```html
<iframe src="https://jlib271.github.io/stemed-deadlines/embed.html" title="STEMEd+ Deadlines"
        style="width:100%;height:700px;border:0" loading="lazy"></iframe>
```

Options, added to the end of the `src` address: `?days=30` (how far ahead to show; default 60), `?source=funding`
(one site: `funding`, `conferences`, `professional-learning`, `faculty-development`), `?limit=10` (at most 10
deadlines), `?subscribe=0` (hide the subscribe box). Combine them with `&`, e.g. `embed.html?days=90&limit=15`.
