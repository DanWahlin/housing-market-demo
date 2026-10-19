# Narration script: GitHub Copilot app demo

Read each block during its time window. The windows match the video exactly. The timing assumes about 150 words a minute.
Generate one audio file per scene and name it with the scene ID (for example, `s01.mp3`). Then run `python add-narration.py <folder>`. It places each file at the start of its scene. If a file is longer than its window, the script reports it, so you can shorten that text or slow the clip.

## s01 · 00:00 to 00:14 · 14.8 s

*On screen: Slide 01*

Hi, I'm Dan Wahlin from GitHub. In the next few minutes, I'll show you how the GitHub Copilot app lets you put AI agents to work, for developers, project managers, business analysts, and leaders.

## s02 · 00:14 to 00:27 · 12.4 s

*On screen: Slide 02*

Let's start with a question. How much of your day is real work, and how much goes to hunting for information, switching between tools, and waiting on other people?

## s03 · 00:27 to 00:46 · 19.0 s

*On screen: Slide 03*

Every role has work that waits. Developers have bugs and missing tests. Project managers build status reports by hand. Analysts move data between spreadsheets and systems. And leaders wait on all of it. A chat assistant helps with answers, but the work still lands on you.

## s04 · 00:46 to 00:55 · 9.2 s

*On screen: Slide build*

Here's the idea. You bring the ideas and the judgment. Agents do the steps. Multiply the two, and you get impact.

## s05 · 00:55 to 01:06 · 11.2 s

*On screen: Slide 05*

Derek Sivers said it well: ideas are just a multiplier of execution. Agents raise the execution side for everyone, not only for people who write code.

## s06 · 01:06 to 01:18 · 12.0 s

*On screen: Slide 06*

The GitHub Copilot app is one desktop workspace for many agents. You hand off a task, run several at once, and review the results before you accept them.

## s07 · 01:18 to 01:23 · 5.2 s

*On screen: Slide 07*

Think of yourself as a conductor. A conductor doesn't play every instrument.

## s08 · 01:23 to 01:45 · 21.8 s

*On screen: Slide build*

You set the direction, and each section plays its part. In today's demo, one agent builds a website, another builds an Excel workbook, another builds an executive briefing, and another reads Microsoft 365 with WorkIQ. An automation keeps the beat every week. And you stand in the middle: you plan, review, and approve.

## s09 · 01:45 to 01:56 · 10.4 s

*On screen: Slide 09*

Our story uses one public dataset: the FHFA House Price Index and CFPB mortgage data, for all fifty states and one hundred metro areas.

## s09b · 01:56 to 02:17 · 21.4 s

*On screen: Slide 10*

Here's how you work with agents. You describe the outcome you want. For bigger work, you read the plan first. Then you hand it off to Autopilot, and the agents work at the same time. When they finish, you review the diffs, previews, and files, and then you merge, share, or deploy.

## s10 · 02:17 to 02:20 · 3.0 s

*On screen: Slide 11*

Let's go to the live demo.

## d01 · 02:20 to 02:35 · 15.0 s

*On screen: Agent 1: get the data*

I start with the session that gets the public data. I pick the demo-start branch, choose Autopilot, and paste the prompt. I also start a second session that uses WorkIQ, and I'll come back to it later.

## d02 · 02:35 to 02:53 · 17.6 s

*On screen: Writing and running the download script*

The agent reads the instructions in the repo, writes a small Node.js script with no extra packages, and downloads the data straight from FHFA and the CFPB. There's no API key, and no manual download.

## d03 · 02:53 to 03:14 · 21.0 s

*On screen: Data checked and pushed*

In about two minutes, the data is ready. The agent checked every file: the row counts, the first and last period, and missing values. It wrote a data dictionary, then pushed everything to a branch called live-data, so the other agents can start from it.

## d04 · 03:14 to 03:32 · 18.4 s

*On screen: Agents 2, 3, and 4 start from live-data*

Now I start three more sessions from live-data: the website in Plan mode, and the Excel workbook and the executive briefing in Autopilot. Each one works on its own branch, in its own worktree, so they never collide.

## d05 · 03:32 to 03:48 · 15.7 s

*On screen: Review the plan, then hand it off*

For the website, the agent shows me its plan first: the tasks, the files, and the deploy steps. It looks good, so I approve it, and the agent switches to Autopilot.

## d06 · 03:48 to 04:12 · 24.1 s

*On screen: Four agents working at the same time*

Now four agents work at the same time, each in its own session. Watch the sidebar: the website agent writes code and tests, the Excel agent builds a workbook, the briefing agent builds slides, and the WorkIQ agent reads my Microsoft 365 data. While they work, I'm free to do something else, like talk to you.

## d07 · 04:12 to 04:34 · 22.3 s

*On screen: Website: tested, built, and deployed*

The website is done. The agent ran its tests and the build, deployed the site to Azure Static Web Apps, and then opened the live site in the app's browser panel. It even checked its own work in the browser and fixed two layout problems before it deployed.

## d08 · 04:34 to 04:45 · 11.3 s

*On screen: Every quarter since 2000*

Here's the map. When I press play, it animates home price changes for every quarter since the year two thousand.

## d09 · 04:45 to 05:06 · 20.4 s

*On screen: State details and top metros*

I can open any state, like Texas, to see its price trend compared with the U.S., and its mortgage loans by purpose from 2018 to 2025. Below the map are the fifteen metro areas with the largest change in the last year.

## d10 · 05:06 to 05:15 · 8.7 s

*On screen: Excel workbook: done*

The Excel workbook is done too. The agent even opened it in Excel to make sure that it opens without errors.

## d11 · 05:15 to 05:35 · 20.4 s

*On screen: A real PivotTable, KPI cards, and a heat map*

Here's the dashboard. When I pick a state, like Texas, Florida, or New York, the KPI cards and charts update. There's a real PivotTable and PivotChart, and a heat map with a sparkline for every state. That's work that takes an analyst hours.

## d12 · 05:35 to 05:52 · 16.8 s

*On screen: WorkIQ: a brief from Microsoft 365*

Now the WorkIQ session. It searched my email, Teams, and calendar for this talk, and wrote a one-page brief. My prompt told it to use roles only, never names, and to skip anything confidential.

## d13 · 05:52 to 06:17 · 24.9 s

*On screen: The brief: goals, roles, logistics, and gaps*

Here's the brief. It has the goals, the five audience roles, the date, time, and place, and the open questions from the organizers. It lists its sources by type and date only, with no names. Then it compared all of that with my talk outline, and found nine gaps I still need to close. That information was spread across eleven emails.

## d14 · 06:17 to 06:40 · 23.5 s

*On screen: Executive briefing: native, editable charts*

Last, the executive briefing for leaders. Seven slides, each with one headline that states the insight, and one chart. These are native PowerPoint charts that you can edit, and every slide has speaker notes. And the numbers match the website exactly, because every agent read the same instructions in the repo.

## d15 · 06:40 to 07:00 · 19.6 s

*On screen: Automation: refresh every Monday*

Finally, an automation. I give it a name, pick a weekly trigger, and describe the job: every Monday, get new data, rebuild the website, the workbook, and the briefing, and summarize what changed. Set it up once, and it keeps running.

## e01 · 07:00 to 07:11 · 11.2 s

*On screen: Slide 12*

So, four results, built at the same time from one dataset: a live website, an analyst workbook, an executive briefing, and a brief from Microsoft 365.

## e02 · 07:11 to 07:26 · 14.7 s

*On screen: Slide 13*

And you stay in control. You read the plan before work starts. Each agent works on its own branch. You choose which tools can run without asking. And nothing is accepted until you review it.

## e03 · 07:26 to 07:34 · 8.8 s

*On screen: Slide 14*

Alan Kay said, the best way to predict the future is to invent it. With agents, more people can invent.

## e04 · 07:34 to 07:46 · 11.2 s

*On screen: Slide 15*

So pick one task this week and hand it to an agent. The free course, GitHub Copilot app for beginners, shows you how, step by step.

## e05 · 07:46 to 07:53 · 7.5 s

*On screen: Slide 16*

Bring an idea, and put an agent to work on it. Thanks for watching.
