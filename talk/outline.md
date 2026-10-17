# GitHub Copilot app: AI Agents for Developers, Knowledge Workers, and Everyone in Between

35-minute session for Fannie Mae. One public dataset, four roles, four agents that run at the same time.

## Storyline

> One question about the U.S. housing market. Four people need four different answers: a developer needs a live app, an analyst needs a workbook, a leader needs a briefing, and the presenter needs to know what the organizers expect. You start all four with agents, at the same time, and you review the results.

## Timeline

| Time | Segment | What the audience sees | Roles |
| --- | --- | --- | --- |
| 0:00 to 4:00 | Slides: the problem | The opening question, the problem for each role, the quote, the app in one picture, the storyline | Everyone |
| 4:00 to 8:00 | Start four sessions | Session 1 starts in **Plan** mode. Sessions 2, 3, and 4 start in **Autopilot**. The sidebar shows four agents at work. | Everyone |
| 8:00 to 10:00 | Approve the plan | Read the website plan, then approve it and switch to **Autopilot**. Talk about worktrees: each agent works on its own branch, so the agents do not conflict. | Developers, IT managers |
| 10:00 to 14:00 | WorkIQ brief | The session brief from Microsoft 365, the privacy rules in the prompt, and the gap check against this outline | Knowledge workers, leaders |
| 14:00 to 19:00 | PowerPoint briefing | Open the deck. Click a chart to show that it is a native, editable chart. Read the speaker notes. | Knowledge workers, leaders |
| 19:00 to 24:00 | Excel workbook | PivotTable and PivotChart, the state drop-down that drives the dashboard, the heat map | Business analysts |
| 24:00 to 29:00 | Website and deploy | Browser preview in the app, animated map, tests, deploy to Azure Static Web Apps, QR code so the audience opens the live site on their phones | Developers, IT managers |
| 29:00 to 31:00 | Optional: automation | Create a weekly automation that gets new data and updates the site and the deck every Monday | Leaders, IT managers |
| 31:00 to 35:00 | Slides: close | What you saw, the quote, how to start | Everyone |

## Before the talk

1. In the Copilot app, open the **housing-market-demo** project.
2. Run `python3 scripts/fetch_data.py` to get the latest data, then commit it.
3. Run `az account show` to make sure that you are signed in to Azure.
4. Make sure that the WorkIQ MCP server is connected (**Customize** > **MCP**).
5. Copy each prompt below into a text file so you can paste it quickly.
6. Keep the backup branches from the proof run. If a live session is slow, switch to the backup output and continue the story.

## Prompts

Start each prompt in a new **project session** (worktree) in the housing-market-demo project.

### Session 1: Website (Plan mode, then Autopilot)

Developers and IT managers.

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

When the plan appears, approve it and select **Autopilot**.

### Session 2: Excel workbook (Autopilot)

Business analysts.

```text
Build an Excel workbook, analysis/housing-market-analysis.xlsx, for a business analyst. Use the data in data/.

The workbook must have:
- A Data sheet with one Excel table. Each row is a state and year (2018 to 2025). Include the state name, region, loans and dollar volume for each loan purpose, average loan size, and the Q4 year-over-year home price change.
- A real Excel PivotTable on that table: rows are regions, columns are years, values are total loans and average loan size. Add a PivotChart for it.
- A Dashboard sheet: a state drop-down that updates KPI cards and charts through formulas, a heat map of year-over-year home price change (states by year, color scale), and a sparkline for each state.
- Clear number formats, frozen header rows, and a Notes sheet with the sources.

When the workbook is done, open it in Microsoft Excel to make sure that it opens without a repair message. Save a PNG screenshot of the Dashboard sheet to analysis/.
```

### Session 3: PowerPoint briefing (Autopilot)

Knowledge workers and leaders.

```text
Create a 7-slide executive briefing, briefings/housing-market-briefing.pptx, about the U.S. housing market. Use the data in data/. Use the look of templates/github-dark-template.pptx (colors, fonts, and card style).

The audience is busy leaders. Tell this story: where home prices are now, how fast they changed, which states and metros lead and which lag, how mortgage originations changed from 2018 to 2025 (home purchase compared to refinance), and three takeaways.

Each slide has one headline that states the insight and one chart or visual. Use native PowerPoint charts so people can edit them. Add speaker notes to each slide.

When the deck is done, render each slide to PNG, check for text that overflows or overlaps, and fix any problems.
```

### Session 4: WorkIQ session brief (Autopilot)

Knowledge workers and leaders. Run this prompt once before the talk and read the result before you show it live.

```text
Use WorkIQ to find the emails, Teams messages, and meetings about my upcoming GitHub Copilot app session for Fannie Mae.

Write a one-page brief to talk/session-brief.md with:
- The goals of the session
- The audience roles
- Logistics: date, time, length, and format
- Open asks or questions from the organizers

Rules:
- Use roles only. Never include names, email addresses, or phone numbers.
- Skip anything that looks internal or confidential, such as pricing, account plans, or contracts. Say that you skipped it, but do not describe it.
- List your sources by type and date only.

Then compare the brief with talk/outline.md. Add a "Gaps" section that lists what the organizers asked for that the talk does not cover yet.
```

### Optional: weekly automation

Leaders and IT managers. Create it in **Automations**, show it, and do not run it on stage.

```text
Every Monday at 8:00 AM, run python3 scripts/fetch_data.py. If the FHFA or HMDA data changed, rebuild and redeploy the website, update the PowerPoint briefing and the Excel workbook, and write a five-line summary of what changed in the housing data since last week.
```

## Other ideas

- **Code review agent:** Ask a second session to review the website for accessibility and security problems before you deploy it. This shows that you check agent work, and IT managers like it.
- **Phone moment:** Show the QR code on the screen and ask the audience to open the live site. This is the strongest moment for the non-developers.
- **Sessions that talk to each other:** Ask the WorkIQ session to send its gap list to the PowerPoint session, so the deck answers the organizers' questions.
