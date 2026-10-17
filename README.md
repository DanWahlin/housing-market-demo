<p align="center">
  <img src="images/logo.png" alt="Housing market demo logo: a house with rising chart bars inside a blue hexagon badge" width="260">
</p>

<h1 align="center">Housing Market Demo</h1>

<p align="center">
  One public dataset, four AI agents, all working at the same time in the GitHub Copilot app.
</p>

This repo has everything for the talk **"GitHub Copilot app: Put AI Agents to Work for Developers, Knowledge Workers, and Leaders."** In the talk, you start four agent sessions in the GitHub Copilot app. Each one builds something different from U.S. housing data:

| Agent builds | For | Result |
| --- | --- | --- |
| An interactive website, deployed to Azure | Developers and IT managers | [Live site](https://calm-rock-09895ae0f.5.azurestaticapps.net) · [code](site/) |
| An Excel workbook with a PivotTable and dashboard | Business analysts | [Workbook](analysis/housing-market-analysis.xlsx) |
| A 7-slide executive briefing | Leaders and project managers | [Briefing](briefings/housing-market-briefing.pptx) |
| A session brief from your Microsoft 365 email and meetings (WorkIQ) | Project managers | Not in this repo because it has private event details |

You don't need to write code to run the demo. You paste a prompt and check what the agent builds.

## What's in this repo

| Path | What it is |
| --- | --- |
| [`talk/copilot-app-put-ai-agents-to-work.pptx`](talk/copilot-app-put-ai-agents-to-work.pptx) | The talk slides, with speaker notes |
| [`talk/outline.md`](talk/outline.md) | The 35-minute timeline, all prompts, and the timing from a full test run |
| [`data/`](data/), [`scripts/fetch-data.mjs`](scripts/fetch-data.mjs) | Public housing data (FHFA House Price Index and CFPB mortgage data) and the script that downloads it. The data agent makes both. See [`data/README.md`](data/README.md). |
| [`AGENTS.md`](AGENTS.md) | Instructions that every agent reads first: data sources, data rules, output folders, and metric definitions |
| [`templates/github-dark-template.pptx`](templates/github-dark-template.pptx) | The slide template the briefing agent copies |
| [`site/`](site/), [`analysis/`](analysis/), [`briefings/`](briefings/) | The finished results from our test run |

For a live run, start from the `demo-start` branch. It has the instructions and the slide template, but no data and no results, so the agents do everything from scratch.

## What you need

- The GitHub Copilot app. New to it? Start with the free [GitHub Copilot app for beginners](https://github.com/github/copilot-app-for-beginners) course.
- Node.js 24 and Python 3
- Microsoft Excel and PowerPoint to open the results
- For the website deploy: the Azure CLI, signed in with `az login`. The site uses the Free tier of Azure Static Web Apps.
- For the session brief: the WorkIQ MCP server connected to your Microsoft 365 account

## Run the demo

1. Clone this repo and add it as a project in the Copilot app.
2. In the prompt box, open the mode menu and set **Tool permissions** to **Approve all**. If you skip this, sessions in Autopilot stop and wait for you to approve each command.
3. Start two sessions from `demo-start` (in the workspace menu, set **Base branch** to `demo-start`), both in **Autopilot**:
   - **Get the data** (prompt 1). It downloads the data, checks it, and pushes it to the `live-data` branch.
   - **WorkIQ session brief** (prompt 5). It does not need the housing data.
4. When the data session pushes `live-data`, start the website, Excel, and PowerPoint sessions (prompts 2 to 4) with **Base branch** set to `live-data`. If the network fails, use `main`, which already has the data. Start the website in **Plan** mode and the other two in **Autopilot**.
5. When the website plan appears, approve it and pick **Autopilot**.

In our test run, the data was ready in about 2 minutes. The WorkIQ, PowerPoint, and website sessions finished 2 to 9 minutes after they started. Excel is the slowest. It took 20 minutes in one run because it had to find the cause of a repair message. With the Excel tips in `AGENTS.md`, it took 11 minutes.

## Prompts

<details>
<summary><b>1. Get the data</b> (Autopilot, from <code>demo-start</code>)</summary>

```text
Get the public housing data for this demo. Use the "Data" section in AGENTS.md.

1. Write scripts/fetch-data.mjs in Node.js with no npm packages. It downloads the FHFA House Price Index and the CFPB HMDA data and writes the five CSV files listed in AGENTS.md to data/.
2. Run it. Check each file: the row count, the first and last period, and no empty key values. Show me a short summary table.
3. Write data/README.md: a short data dictionary with the sources and links.
4. Commit the script and the data. Then push this branch to GitHub as live-data, and replace live-data if it already exists.
```

</details>

<details>
<summary><b>2. Website</b> (Plan mode, then Autopilot)</summary>

```text
Plan a public website called "U.S. Housing Market Explorer" in site/ that uses the data in data/. The audience is business leaders who look at it on a large screen and on their phones.

The site must have:
- A hero section with four headline numbers for the latest quarter: U.S. home price change year over year, U.S. change since 2019 Q4, and the states with the fastest and slowest year-over-year change.
- An interactive U.S. map colored by year-over-year home price change. Hover shows the state numbers. Click opens a state panel with the state's price index trend and its mortgage originations by loan purpose from 2018 to 2025.
- A play button and slider that animate the map through every quarter since 2000.
- A ranked bar chart of the 15 metros with the largest year-over-year change.
- A dark, modern design with smooth animations. It must work on phones and be accessible (keyboard, labels, contrast).

Tech: Vite, TypeScript, and D3. No backend. Convert the CSV files to small JSON files at build time. Add Vitest tests for the data math (year-over-year change and rankings).

When the site is done:
1. Run the tests and the build.
2. Open the site in the browser preview.
3. Deploy dist/ to the Azure Static Web App swa-housing-market-demo (Free tier) in resource group rg-housing-market-demo in eastus2. Create them with az only if they do not exist. Use the SWA CLI with the deployment token.
4. Show the live URL and save a QR code for it as site/qr-code.png.

Keep the plan short.
```

</details>

<details>
<summary><b>3. Excel workbook</b> (Autopilot)</summary>

```text
Build an Excel workbook, analysis/housing-market-analysis.xlsx, for a business analyst. Use the data in data/.

The workbook must have:
- A Data sheet with one Excel table. Each row is a state and year (2018 to 2025). Include the state name, region, loans and dollar volume for each loan purpose, average loan size, and the Q4 year-over-year home price change.
- A real Excel PivotTable on that table: rows are regions, columns are years, values are total loans and average loan size. Add a PivotChart for it.
- A Dashboard sheet: a state drop-down that updates KPI cards and charts through formulas, a heat map of year-over-year home price change (states by year, color scale), and a sparkline for each state.
- Clear number formats, frozen header rows, and a Notes sheet with the sources.

When the workbook is done, open it once in Microsoft Excel to make sure that it opens without a repair message, and then close it.
```

</details>

<details>
<summary><b>4. PowerPoint briefing</b> (Autopilot)</summary>

```text
Create a 7-slide executive briefing, briefings/housing-market-briefing.pptx, about the U.S. housing market. Use the data in data/. Use the look of templates/github-dark-template.pptx (colors, fonts, and card style).

The audience is busy leaders. Tell this story: where home prices are now, how fast they changed, which states and metros lead and which lag, how mortgage originations changed from 2018 to 2025 (home purchase compared to refinance), and three takeaways.

Each slide has one headline that states the insight and one chart or visual. Use native PowerPoint charts so people can edit them. Add speaker notes to each slide.

When the deck is done, render each slide to PNG, check for text that overflows or overlaps, and fix any problems.
```

</details>

<details>
<summary><b>5. WorkIQ session brief</b> (Autopilot, from <code>demo-start</code>)</summary>

Change `Fannie Mae` to the name of your event or customer.

```text
Use WorkIQ to find the emails, Teams messages, and meetings about my upcoming GitHub Copilot app session for Fannie Mae.

Write a short brief to talk/session-brief.md with:
- The goals of the session
- The audience roles
- What the organizers asked the talk to cover

Rules:
- Use roles only. Never include names, email addresses, or phone numbers.
- Do not include logistics, such as places, dates, times, travel, or building access.
- Skip anything that looks internal or confidential, such as pricing, account plans, or contracts. Say that you skipped it, but do not describe it.
- List your sources by type and date only.

Then compare the brief with talk/outline.md. Add a "Gaps" section that lists what the organizers asked for that the talk does not cover yet.
```

</details>

<details>
<summary><b>6. Weekly automation</b> (create it in Automations)</summary>

```text
Every Monday at 8:00 AM, run node scripts/fetch-data.mjs. If the FHFA or HMDA data changed, rebuild and redeploy the website, update the PowerPoint briefing and the Excel workbook, and write a five-line summary of what changed in the housing data since last week.
```

</details>

<details>
<summary><b>7. Optional: fix bugs and open a pull request</b> (send to the website session after it deploys)</summary>

```text
Review site/ for accessibility and correctness problems. Fix the problems that you find, add a test for each fix, then commit and open a pull request.
```

</details>

## Give this talk yourself

The timeline, a presenter checklist, and the backup plan are in [`talk/outline.md`](talk/outline.md). Some tips from the test runs:

- The WorkIQ prompt above leaves out logistics, so it is safe on a projector. It still reads your real email, so run it the day before and read the result. In our runs it found 8 to 9 gaps in the talk plan, which is worth mentioning on stage.
- Start the data and WorkIQ sessions first, and talk about where the data comes from while the agent downloads it. Then start the other three. Show the results in the order they finish: brief, briefing, website, workbook.
- Keep the finished results in `main` as a backup. If a session is slow on stage, open the result from `main` and keep going.
- Slide 12 has a QR code for the live site. Ask people to open it on their phones. It gets the non-developers in the room involved.
- Change the title slide, which says "Fannie Mae AI Summit," to your event. Slides 7 and 8 use a Morph transition to show you as a conductor and each session as a section of the orchestra.
- Leave five minutes at the end for questions or a slow step.

## Data and disclaimer

Data comes from the [FHFA House Price Index](https://www.fhfa.gov/data/hpi/datasets) and the [CFPB HMDA Data Browser](https://ffiec.cfpb.gov/documentation/api/data-browser/). Both are public U.S. government data and need no API key. The FHFA data is public domain (CC0), and "FHFA HPI®" is a registered trademark of FHFA. The HMDA data in this repo is state-level totals only, with no loan-level records.

Built from public FHFA and CFPB data. Not an official Fannie Mae, FHFA, or CFPB product.
