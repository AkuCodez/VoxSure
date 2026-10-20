# Working agreement: how this project was built

The specification's agent agreement was followed as below; deviations are stated.

* Spec treated as the source of truth; changes are recorded in `docs/PRD.md` §4.
* Existing code inspected before edits; working functionality preserved (tests re-run after each change).
* Small, tested increments; every endpoint has success and failure tests.
* No invented datasets, citations, results or deployment status. Results come from scripts in `ml/scripts/` and are stored in `ml/reports/`.
  Sample knowledge-base answers use illustrative values for a fictional campus and carry no invented links.
* Dataset was revised after observing weak classes; this is disclosed in the report (§3, §7). It is a mild form of test feedback.
* Secrets: none committed; `.env.example` has placeholders.
* **Not done without human approval:** public deployment, paid services, data retention. Deployment is left to the owner (see `docs/DEPLOYMENT.md`).
* Milestone reports: files changed, tests run, results, known issues and next steps are given in the session summaries and in `docs/TRACEABILITY.md`.
