# DECISIONS MADE FOR SCOPING THE TOOL #


<img width="746" height="941" alt="architecture_1" src="https://github.com/user-attachments/assets/8a3921c8-1393-4033-b67e-a55491a42520" />


## Why four AI agents are needed ##
The four steps chosen for AI intervention are not arbitrary — they are the steps where manual work is highest, the output is most formulaic, and the risk of AI error is lowest.

•	Step 5 (comparison) is the highest-friction data work in the process. It is pure computation — comparing numbers across platforms. A computer should do this, not a person.

•	Step 7 (analysis) is where a human currently spends 30–45 minutes forming a hypothesis that could be generated from the data in seconds. The agent does not replace the manager's judgment — it gives them a hypothesis to agree or disagree with.

•	Step 9 (decisions) is included because structuring options is something AI does well, but executing on those options is something only a human should do. The hybrid design is intentional and permanent, not a temporary compromise.

•	Step 10 (reporting) is the most automatable step in the entire chain. Writing a narrative from structured data is exactly what language models are built for. The manager's job becomes editorial, not compositional.

Steps 1, 2, 6, and 8 are deliberately left to human or platform automation. They either require no improvement (platforms auto-generate data in Step 2), are better served by existing tools (Power BI in Step 6), or involve judgment and relationship that no tool should touch (the team meeting in Step 8).

## Why steps 3 and 4 are automated even though they are not AI steps ##
Steps 3 (pulling reports) and 4 (consolidating data) are not AI steps — they are simple scheduled automation and data normalisation. But they are the most important steps to get right, because every AI agent downstream inherits the quality of what these two steps produce.

If Step 3 fails (an API is down, a credential expires), the Monday morning analysis is missing a channel. If Step 4 normalises incorrectly (mapping the wrong metric), the comparison agent in Step 5 produces confident wrong output. These two steps were prioritised not because they are glamorous but because they are foundational.

The original process had four people each manually exporting one platform. That means four failure points, four people context-switching on Monday morning, and four slightly different time windows for the data. Centralising this in a single scheduled job with a visible sync status log eliminates all four failure points and makes the data collection consistent.

## Why the interface has only three screens ##
The temptation when building internal tools is to surface everything. The problem is that surfacing everything means the manager has to decide what matters — which is exactly the job the tool is supposed to do for them.

Three screens maps to three jobs the manager has on a Monday morning: understand what happened (numbers), understand why it happened (analysis), and communicate it to leadership (report). Every feature that does not serve one of those three jobs was cut.

A dashboard builder would serve a fourth job — exploring data deeply. Power BI already does that job. Pulse does not compete with it.

## Why there is no login system in v1 ##
Authentication adds build time and introduces friction for a tool the team needs to open quickly on Monday morning. In v1, Pulse is accessed via a single internal URL. This is appropriate for a small, trusted internal team.

Access control becomes necessary when: the tool contains client-sensitive data that different team members should not see, or when the tool expands to multiple teams or clients. Neither condition applies in v1. Adding it now would be premature.

## Why attribution modelling is excluded ##
Attribution — figuring out which channel actually caused a conversion when a customer touched Google Ads, then saw a Meta reel, then clicked an email — is one of the genuinely hard problems in marketing analytics. Every platform claims credit for every conversion. The true answer requires probabilistic modelling across touchpoints, which produces an estimate, not a fact.

Including attribution modelling in v1 would mean the tool produces numbers that the manager cannot verify against any single platform's native reporting. That breaks trust immediately. The team needs to trust Pulse's numbers before they can trust its analysis. Introducing uncertainty into the numbers layer before trust is established is the wrong order.

The correct sequencing is: per-channel analysis in v1, cross-channel attribution in v2 after the team has three months of experience with the per-channel view.

## What to revisit with more time ##
**IF GIVEN 2 MORE WEEKS BEFORE V1 SHIPS**

•	Data validation layer: automated checks that flag when a platform's numbers are statistically implausible (e.g. ROAS suddenly 10x for one day — likely a tracking error, not a performance breakthrough). This currently relies on the manager noticing.

•	HubSpot data quality scoring: a simple indicator of how complete the CRM data is, so the manager knows whether to trust the leads and revenue numbers before the meeting.

•	Agent confidence indicator: a visible signal on each AI output showing how much data supported the conclusion. 'Based on 4 weeks of data' vs 'based on 1 week of data' are very different levels of reliability.

**CANDIDATES FOR V2 (ONLY IF TEAM ASKS FOR THEM)**

•	Natural language Q&A: ask Pulse 'what happened to Meta last Tuesday?' and get an answer. High value, moderate build cost. Include only after the core Monday workflow is trusted.

•	Campaign-level drill-down: currently Pulse shows channel-level data only. Going one level deeper — which specific Google campaign drove the ROAS improvement — would require surfacing more data without overwhelming the interface.

•	Cross-channel attribution modelling: see reasoning above. Appropriate after 3 months of v1 use.

•	Client-facing reports: if the team needs to share Pulse-generated reports directly with clients, a separate export template (white-labelled, without internal notes) would be the right addition.

•	Slack bot integration: instead of a copy-to-Slack button, a Slack bot that posts the Monday summary automatically to the team channel. Low build cost, high convenience.

**THINGS DELIBERATELY NOT REVISITING**

•	Real-time monitoring and push alerts: the team's workflow is weekly. Alerts would interrupt without adding value until the team explicitly asks for them.

•	Budget auto-execution: permanently excluded. The financial and trust risk of automating budget decisions outweighs any time saving. Human approval is not a v1 constraint — it is a design principle.

•	Replacing Power BI or existing BI tools: Pulse is additive, not a replacement. The team knows their BI tools. Pulse feeds them better data. That is the correct relationship.
