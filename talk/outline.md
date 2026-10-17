# GitHub Copilot app: Put AI Agents to Work for Developers, Knowledge Workers, and Leaders

35-minute session for Fannie Mae. One agent gets the public data, and then four agents build four results at the same time.

## Storyline

> One question about the U.S. housing market. Four people need four different answers: a developer needs a live app, an analyst needs a workbook, a leader needs a briefing, and the presenter needs to know what the organizers expect. You start all four with agents, at the same time, and you review the results.

## Timeline

Lunch follows the session, so the plan ends at 32:00 and keeps 3 minutes for questions and delays.

| Time | Segment | What the audience sees | Roles |
| --- | --- | --- | --- |
| 0:00 to 4:00 | Slides 1 to 10 | The opening question, the problem for each role, the quote, the app, the conductor and orchestra (Morph from slide 7 to slide 8), the storyline | Everyone |
| 4:00 to 6:00 | Slide 11, then start two sessions | From `demo-start`, start **Get the data** and **WorkIQ brief** in **Autopilot**. Talk about the public sources while the agent writes the download script. | Everyone |
| 6:00 to 9:00 | Data is ready, start three sessions | Show the data summary table. From `live-data`, start the website in **Plan** mode, and Excel and PowerPoint in **Autopilot**. Approve the website plan and select **Autopilot**. The sidebar shows five agents. | Everyone |
| 9:00 to 12:00 | WorkIQ brief | The brief from Microsoft 365, the privacy rules in the prompt, and the gaps that it found in this talk plan | Project managers, knowledge workers |
| 12:00 to 15:00 | Review the agent work | Open the data session's diff: the download script and `data/README.md`. Explain worktrees: each agent works on its own branch. | Developers, IT managers |
| 15:00 to 19:00 | PowerPoint briefing | Open the deck. Click a chart to show that it is native and editable. Show the speaker notes. | Leaders, project managers |
| 19:00 to 23:00 | Website and deploy | Browser preview, Play button, state panel, tests, Azure Static Web Apps URL, QR code for phones | Developers, IT managers |
| 23:00 to 27:00 | Excel workbook | PivotTable and PivotChart, the state drop-down that drives the dashboard, the heat map, the sparklines. Excel is the slowest session, so show it last. | Business analysts |
| 27:00 to 29:00 | Automation | Create the weekly automation that gets new data and updates all outputs | Leaders, IT managers |
| 29:00 to 32:00 | Slides 12 to 16 | What the agents built, how you stay in control, the quote, one task to try this week | Everyone |
| 32:00 to 35:00 | Questions | Buffer for questions or a slow live step | Everyone |

## Test runs (17 October 2026)

**Run 2** used the current flow: the data session started from an empty `demo-start`, and the other sessions started from its pushed branch.

| Session | Result | Time |
| --- | --- | --- |
| Get the data | Wrote `scripts/fetch-data.mjs`, downloaded all 5 files, checked them, and wrote `data/README.md`. The values match run 1 exactly. | About 2 minutes |
| WorkIQ brief | No names, 2 items skipped, 9 gaps found | About 2 minutes |
| PowerPoint briefing | 7 slides, native charts, speaker notes. Same numbers as the website (+2.3% year over year, +64.0% since 2019 Q4). | About 8.5 minutes |
| Website | 11 Vitest tests pass, build passes, deployed to the same Azure Static Web App | About 9 minutes, including the plan approval |
| Excel workbook | PivotTable and PivotChart, dashboard, heat map, and two sparkline columns. Opens in Excel with no repair message. | About 20 minutes. About 9 minutes went to finding the cause of an Excel repair message (one bad table formula). |
| Excel workbook (run 3, with the new Excel tips in `AGENTS.md`) | Same features. Opens with no repair message, the PivotTable refreshes, and the drop-down values match the data. | About 11 minutes |

**Run 1** started from data that was already in the repo. The sessions lost about 16 minutes while they waited for tool approval. Without that wait, the WorkIQ brief took about 5 minutes, the Excel workbook about 8, the PowerPoint briefing about 10, and the website about 9.

The finished results from the latest runs are in `main`: `data/` and `scripts/` (run 2), `site/` and `briefings/` (run 2), and `analysis/` (run 3). If a live session is slow, show the finished result from `main`. The WorkIQ brief is not in the repo because it has private event details.

## Presenter checklist

### The day before

1. Send the talk deck (`talk/copilot-app-put-ai-agents-to-work.pptx`) to the organizers. They asked for materials before the event.
2. Run the private prep version of the WorkIQ prompt and read the brief. Do not show it on stage.
3. Do one full rehearsal from `demo-start`. This also puts every prompt in your prompt history, so on stage you press **Cmd+R**, search, and select the prompt instead of pasting it.
4. Record your screen during the rehearsal. If the venue network fails, you can play the recording.

### At the venue, before you start

1. Test the venue Wi-Fi. If it is slow, use your phone hotspot.
2. Run `az account show` to make sure that you are signed in to Azure.
3. Make sure that the WorkIQ MCP server is connected (**Customize** > **MCP**).
4. Hide private content: close other projects in the Copilot app sidebar (or use a separate profile with only this project), close email and chat, and turn on a macOS Focus mode so that no notifications appear.
5. Make the app text large enough for the back of the room.
6. In the Copilot app, open the **housing-market-demo** project. Do not add data to `demo-start`. The data session downloads it live.
7. **Important:** In the composer, open the mode menu, select **Tool permissions**, and then select **Approve all**. Do this before you send each prompt. If you do not, Autopilot sessions stop and wait for approval.

### On stage

- If the data session fails, start the other sessions from `main`, which already has the data, and say so.
- If a session is slow, show its finished result from `main` and continue.
- **Wow moment:** while the website session works, send it a follow-up such as "Make the map colors more vivid and highlight the selected state." It shows that you can steer an agent while it works.
- Before the last slides, show slide 12 and ask the audience to scan the QR code for the live site.

## Prompts

Start each prompt in a new **project session** (worktree) in the housing-market-demo project. In the workspace menu, set **Base branch** to `demo-start` for the data and WorkIQ sessions. For the website, Excel, and PowerPoint sessions, set **Base branch** to `live-data`. The app takes the base branch from GitHub, so the data session pushes its work to `live-data`. If the network fails, use `main`, which already has the data.

### Get the data (Autopilot, from `demo-start`)

Everyone. Start this first. It takes about 2 minutes.

```text
Get the public housing data for this demo. Use the "Data" section in AGENTS.md.

1. Write scripts/fetch-data.mjs in Node.js with no npm packages. It downloads the FHFA House Price Index and the CFPB HMDA data and writes the five CSV files listed in AGENTS.md to data/.
2. Run it. Check each file: the row count, the first and last period, and no empty key values. Show me a short summary table.
3. Write data/README.md: a short data dictionary with the sources and links.
4. Commit the script and the data. Then push this branch to GitHub as live-data, and replace live-data if it already exists.
```

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

When the workbook is done, open it once in Microsoft Excel to make sure that it opens without a repair message, and then close it.
```

### Session 3: PowerPoint briefing (Autopilot)

Knowledge workers and leaders.

```text
Create a 7-slide executive briefing, briefings/housing-market-briefing.pptx, about the U.S. housing market. Use the data in data/. Use the look of templates/github-dark-template.pptx (colors, fonts, and card style).

The audience is busy leaders. Tell this story: where home prices are now, how fast they changed, which states and metros lead and which lag, how mortgage originations changed from 2018 to 2025 (home purchase compared to refinance), and three takeaways.

Each slide has one headline that states the insight and one chart or visual. Use native PowerPoint charts so people can edit them. Add speaker notes to each slide.

When the deck is done, render each slide to PNG, check for text that overflows or overlaps, and fix any problems.
```

### Session 4: WorkIQ session brief (Autopilot, from `demo-start`)

Knowledge workers and leaders. Run this prompt once before the talk and read the result before you show it live.

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

This is the stage version. It leaves out logistics, so it is safe on a projector. For your own preparation the day before, use this private version, which adds logistics and open asks. Do not show its result on stage.

<details>
<summary>Private prep version</summary>

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

</details>

### Weekly automation

Leaders and IT managers. The abstract promises automation, so keep this segment. Create it in **Automations**, show it, and do not run it on stage.

```text
Every Monday at 8:00 AM, run node scripts/fetch-data.mjs. If the FHFA or HMDA data changed, rebuild and redeploy the website, update the PowerPoint briefing and the Excel workbook, and write a five-line summary of what changed in the housing data since last week.
```

### Optional: fix bugs and open a pull request

Developers. The abstract promises agents that fix bugs and open pull requests. The repo must be on GitHub so that the agent can open the pull request. After the website session deploys, send it this follow-up prompt:

```text
Review site/ for accessibility and correctness problems. Fix the problems that you find, add a test for each fix, then commit and open a pull request.
```

## Other ideas

- **Code review agent:** Ask a second session to review the website for accessibility and security problems before you deploy it. This shows that you check agent work, and IT managers like it.
- **Phone moment:** Show the QR code on the screen and ask the audience to open the live site. This is the strongest moment for the non-developers.
- **Sessions that talk to each other:** Ask the WorkIQ session to send its gap list to the PowerPoint session, so the deck answers the organizers' questions.
