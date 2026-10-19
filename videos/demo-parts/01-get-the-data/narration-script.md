# Narration: Get the public data

Read each block during its time window. Name each audio file with its scene ID (for example, `d01.mp3`), then run `python add-narration.py <audio-folder> --video video-nocc.mp4 --timing narration-timing.csv` in this folder.

## d01 · 00:00 to 00:15 · 15.0 s

*On screen: Agent 1: get the data*

I start with the session that gets the public data. I pick the demo-start branch, choose Autopilot, and paste the prompt. I also start a second session that uses WorkIQ, and I'll come back to it later.

## d02 · 00:15 to 00:32 · 17.6 s

*On screen: Writing and running the download script*

The agent reads the instructions in the repo, writes a small Node.js script with no extra packages, and downloads the data straight from FHFA and the CFPB. There's no API key, and no manual download.

## d03 · 00:32 to 00:54 · 21.4 s

*On screen: Data checked and pushed*

In about two minutes, the data is ready. The agent checked every file: the row counts, the first and last period, and missing values. It wrote a data dictionary, then pushed everything to a branch called live-data, so the other agents can start from it.
