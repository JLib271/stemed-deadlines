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

**List of deadlines (no iframe, no script).** In WordPress (for example a STEMEd+ Commons page), add an **RSS** block
and give it this feed:

    https://jlib271.github.io/stemed-deadlines/feeds/upcoming.xml

It lists the next 60 days, soonest first, each title starting with its date ("Nov. 30: Applications due: ...").
Turn on "Display excerpt" to show which site each deadline comes from, and set "Items" to how many to show.
One site only: `feeds/upcoming-funding.xml`, `upcoming-conferences.xml`, `upcoming-professional-learning.xml`,
`upcoming-faculty-development.xml`. WordPress refreshes feeds every few hours.

**Subscribe buttons.** Plain links work anywhere:

- Google Calendar: `https://calendar.google.com/calendar/r?cid=http%3A%2F%2Fjlib271.github.io%2Fstemed-deadlines%2Ffeeds%2Fall.ics`
- Apple Calendar or Outlook: `webcal://jlib271.github.io/stemed-deadlines/feeds/all.ics`
- Any calendar ("add from URL"): `https://jlib271.github.io/stemed-deadlines/feeds/all.ics`

**Iframe (optional).** `embed.html` is a compact view with subscribe buttons for sites that allow iframes:
`<iframe src="https://jlib271.github.io/stemed-deadlines/embed.html" title="STEMEd+ Deadlines" style="width:100%;height:700px;border:0"></iframe>`.
Options: `?days=30`, `?source=funding`, `?limit=10`, `?subscribe=0`, combined with `&`.
