---
name: evolution-loop
description: "Use when improving a system, workflow, model, prompt, skill, or supporting tool through iterative experiments and regression checks."
---

# Evolution Loop

Improve an authorized outcome through evidence-backed rounds. Protect established successes and converge on one maintained execution path. Quality, reliability, speed, cost, and simplicity can be objectives; their trade-offs must be explicit before selecting a candidate. Necessary improvements to supporting tools and methods are part of the same process. Distinguish the agreed target from capabilities that enable its investigation or operation; a tool can occupy either role depending on the goal.

Begin by settling the goal, system boundary, work breakdown, success criteria, and finite limits with the user or within their delegated discretion. The default round is **broad check → focused investigation → small attributable changes → broad recheck → independent confirmation across the agreed whole scope**. A single isolated defect may need only a small case loop; interacting capabilities need recurring coverage across the agreed scope.

## Agree on Goals, Scope, and Limits

Inspect the request, current implementation, active instructions, existing tests, accepted outputs, and prior decisions. Use a short targeted interview or a concrete proposal to settle the choices below before optimization begins. Ground proposals in the user's purpose, observed baseline, failure costs, and available resources; explain the consequential trade-offs rather than importing fixed targets or experiment counts.

Reuse established decisions and authorization without asking again. When the user has delegated these choices, select and explain justified settings within that delegation. Ask only about material unresolved choices that cannot be inferred or decided within it; do not treat silence as agreement. If baseline measurement is needed to propose a realistic target, first define that bounded preparatory step and the decision it will inform. Missing choices block the dependent experiment, not safe inspection and preparation.

Record the resulting agreement in the existing task plan or experiment record:

- **Outcome and success:** the user-visible result to improve, its current baseline, measurable or independently checkable final target, protected behaviors, and acceptable variation or trade-offs. Distinguish the criterion for adopting an intermediate improvement from the criterion for declaring the final goal achieved. Qualitative goals need a checkable rubric or contract.
- **Scope and work breakdown:** the system boundary for the final claim, all evaluation dimensions and relevant operating conditions, allowed product and supporting-tool changes, protected external effects, and existing user work. Propose focused problems from evidence and map each to the whole-system outcome. Distinguish what is measured from what can be changed; choose whether to investigate one problem, several separable problems, or their interaction. Neither the number of problems nor simultaneous work is a default requirement.
- **Execution path:** entry point → relevant files/functions, model/tool calls, state transitions → user-visible output; where a candidate will integrate and which consumers depend on it. Include required recovery and supported variants.
- **Baseline:** identify the accepted artifact/version, settings, initial state, data and evaluator versions, and directly observed results. Run the relevant baseline checks before editing. Known defects remain open; do not preserve them as successes.
- **Evidence and confirmation:** source inputs and truth, metrics/rubrics and denominators, comparison conditions, and the independent cases/checks needed to assess every agreed dimension and the original whole-system target. Plan access and coverage before spending the experiment budget. Model output, reviewer opinion, or a prior result is a reference to check, not ground truth when source evidence contradicts it.
- **Experiment bounds:** data-use permissions, authorized tools/models, a finite enforceable overall bound on elapsed time or experiment work, cost limits where applicable, per-run limits where needed, checkpoints, repeats, and stopping conditions for success, harm, or lack of useful progress. Propose concrete limits with reasons. Count preparation, tool development, exploration, retries, and confirmation within the total and reserve capacity for whole-scope confirmation; define how to resume without duplicating external effects.

This agreement governs both local experiments and whole-scope confirmation. If evidence calls for a different goal, decomposition, boundary, criterion, or budget, state the change and its effect on previous comparisons before proceeding, resolving it within the same authorization rules. Do not narrow the claim or relax a criterion after seeing a failure and report the original goal as achieved.

Performance improvement does not authorize new paid models, provider/data transfers, deployment, or destructive actions. Preserve existing authorization; seek additional permission only for an actual scope or side-effect change. Missing evidence blocks the dependent action, not safe independent investigation.

A case may be a stateful episode rather than a single input: retain relevant initial state, event order, timing, environment, and expected outcome. A replay must preserve the information needed for the claim being tested.

## Make the Experiment Trustworthy

Establish that the measurement path detects the difference the goal requires before optimizing against it. For new, changed, or suspect evaluation tooling, use bounded controls with known outcomes: valid and invalid outputs, unchanged candidates, simple reference methods, or source-backed judgments as appropriate. Check data transformations, case alignment, missing records, and metric direction. Quantify ordinary run-to-run variation when material. Reuse prior checks only while the relevant implementation and conditions match; a plausible score alone does not validate an evaluator.

Version the candidate, evaluator/rubric, data groups, relevant tools/dependencies, and execution conditions. Keep the measurement method fixed within a comparison. Evaluators and data preparation can evolve through the tool procedure below, but a changed evaluator cannot retroactively turn an incomparable score into a product gain. Source evidence and the agreed outcome remain authoritative.

Define a fair resource regime before comparing candidates: equal resources, performance under agreed cost/latency limits, or an explicit quality-resource trade-off. Match inputs and relevant conditions within each comparison tier. Report actual time, calls, compute, or cost as applicable; extra resources may be justified, but their contribution must be visible. Separate the cost of searching for a solution from the resources the resulting system uses. Derive limits from the task while preserving applicable model and dependency rules.

Record execution status and evidence validity separately from the candidate decision. Distinguish observed candidate failures from invalid measurements or environment failures; unresolved causes stay uncertain. Preserve all attempts, raw results, missing cases, timeouts, and resource use in the existing experiment record. Apply the prespecified denominator and timeout policy: do not silently drop failed cases, average only survivors, or represent an unmeasured metric as a numeric success. A candidate-caused failure can count against reliability even when its quality metric is unavailable; an invalid comparison calls for diagnosis, not a performance claim.

## Separate Coverage, Changes, and Experiment Effort

Use the agreed evaluation dimensions and work breakdown. Use one grouping criterion per level; give each responsibility one home and record cross-effects as links. A case may exercise several dimensions without becoming several independent samples.

Maintain a small **common regression set** spanning the agreed dimensions: representative successes, known failures, counterexamples, and consequential interactions. Reuse existing tests and source responses. Record each dimension's result and evidence level: component replay, mocked integration, live path, or unverified. No available data or environment means unverified.

The common set detects damage and guides attention; its repeated score is not an unbiased estimate of general performance. Refresh development coverage as new failure mechanisms emerge. A broader scope does not require equal sample counts, new provider calls, or full device trials for every dimension in every round.

Choose focused work by harm, prevalence, coupling to other capabilities, uncertainty, and the evidence obtainable within the current budget. Give stable dimensions inexpensive protection and investigate uncertain or consequential ones deeply. Avoid letting one difficult case indefinitely prevent progress elsewhere.

Use cheap, reliable checks to screen candidates before expensive full-path runs and independent confirmation. Define the tiers, comparable resources, and advance/stop rules before screening; allocate more effort to promising or informative candidates within the total bound. Early results are a useful filter only when they reveal decisive failures or have evidence of relevance to the final outcome. If early rankings may reverse or omit an important condition, deepen the comparison rather than eliminate a candidate on an unsupported proxy. Adaptive allocation is an experiment design choice, not a required algorithm or a license to stop on a lucky score.

Choose the smallest useful investigation:

| Investigation | Use it when | Required limit |
|---|---|---|
| Case-first | A concrete failure can reveal a mechanism | Diagnose deeply, then check related cases and the common set |
| Aspect-sweep | One behavior needs comparison across cases or conditions | Keep criteria fixed; separate distinct causes and check full-case outcomes |
| Interaction comparison | Changes may help or harm each other | Compare the necessary combinations on matched cases, not an exhaustive grid by default |

These are focused investigations inside the same round, not competing execution paths. Several independent fixes can share a round if their changes and evidence stay distinguishable. Treat inseparable contract changes as one declared unit. Every dimension need not change.

## Experiment on the Target Itself

The experiment path is itself a repeated execution path, so the same single-path and minimum-implementation rules apply to it. An experiment that imitates or patches the target measures a copy, and its result must then be transplanted, which is where the copy and the target drift apart.

- Run the target itself: the same code, prompt, skill or workflow that will be used. For code, keep the logic being improved as a module of the target that receives its devices (I/O, external services, storage, clock) as arguments. The target connects real devices; the experiment connects replay devices, case data and scoring, nothing else. When the target cannot take a device as an argument, add that argument in the target rather than reimplementing, mocking or patching its internals in the experiment. When the experiment finishes, the improved module is already the target's.
- Keep one runner. Round values (candidate commits, limits, deadline, output folder) go into a configuration file, and cases go into data files, so a new round or case changes data, not code.
- Make the runner print what the next decision needs: main and protected metrics, failures grouped by kind with case identifiers, invalid runs with their reason, and usage against limits. Keep per-case detail in files and open it only to investigate a specific failure. Never shorten the summary by dropping failures.
- Read once, then rely on the record. Where delegation is available, a delegated agent reads large code or documents and returns conclusions. Facts already established go into the resume record, and each round starts in a fresh context from that record rather than from the whole guides, code and plan.
- When a structure proves wrong, migrate the measured data the new structure needs, verify the migration, then delete the old code, branches, worktrees, copies inside data folders and every document line that describes or points to it. Do not keep backups of the old structure: leftover code draws later work back to it. Measured results and the history of tried candidates stay, in their migrated form. Confirm by searching for the old names.

## Run a Round

1. **Check broadly.** Establish the measurement path's validity, run the common set against the identified baseline, and record remaining gaps. Previously completed results can be reused only when the relevant code, configuration, inputs, state, evaluator, and conditions still match. Do not report reused evidence as a fresh run.
2. **Select and freeze the comparison.** Choose focused hypotheses and discriminating observations, the baseline/candidates, source cases, expected contracts, objectives and protected metrics, effort bounds, resource regime, screening rules, and evaluation method before inspecting candidate results. Include normal, failure, and counterconditions. Use matched inputs and state; account for order, cache, service drift, or stochastic variation where material.
3. **Investigate before changing.** Keep analysis, test, and change distinct. During a test, freeze the candidate and measurement method. Follow the cause procedure if a failure appears. If progress requires a better method or tool, make that a bounded supporting change using the procedure below. Changing either the candidate or measurement method starts a new comparison version.
4. **Make a small attributable change.** Replace, merge, or refine the responsible rule, implementation, or supporting capability in the declared path. Record connected changes as a unit; preserve separate changes so they can be evaluated or reverted independently.
5. **Recheck focused and broad behavior.** Rerun the failure, counterconditions, protected successes, and common set. Include directly affected consumers. If another dimension worsens, investigate that connection; an average gain cannot hide a breached protection.
6. **Confirm across the whole scope.** Before promoting an improvement to the agreed target, freeze the integrated candidate and compare it with the baseline on independent evidence covering the whole agreed scope, all evaluation dimensions, and the original system-level outcome. A check of only the improved problem cannot qualify it. Supporting capabilities are verified against their declared tool contract as described below; that verification does not confirm the target's performance.
7. **Decide and learn.** Record adopt, reject, defer, or keep against the agreed criteria, whether the hypothesis was supported/refuted/unresolved, and the next useful question or enabling capability. Only confirmed, adopted changes become the relevant next baseline; retain useful unconfirmed work as experimental candidates. Separate target performance gains, supporting-tool/method gains, and knowledge gained without a measured improvement. The next round starts from this evidence within the remaining budget.

For suspected interactions, compare the baseline, A alone, B alone, and A+B when that is the smallest discriminating design. Use equivalent cases, state, and conditions. If changes cannot be separated, report the bundle's effect and do not claim individual attribution. Similar timing or a shared input alone does not prove an interaction.

Set sample effort from the distinction needed and cost of error. Small batches discover problems but may not establish reliable rates or rare-event safety. Preserve failures and all planned repetitions; do not retry until a pass. Follow any prespecified adaptive allocation or stopping rule; otherwise a post-result change to sampling or evaluation starts a new comparison and is not retrospective evidence that the old criterion passed. When stochastic performance is the claim, use prespecified repeats and uncertainty appropriate to independent sampling units. Deterministic contracts can use exact assertions. Do not invent universal sample counts or pass thresholds.

Keep the history of tried candidates and inspected results. Searching more candidates or repeatedly checking a score can select a lucky winner even with an unchanged benchmark. Treat the best exploration score as a hypothesis, not confirmed performance. Freeze the selected candidate and confirm it against the baseline using the whole-scope independent-evidence rules; use inference appropriate to the actual selection and stopping design when making statistical claims. Do not promote a noise-level gain merely because it ranks first.

## Diagnose the Mechanism

State the observed failure and intended behavior. Follow a cause chain from symptom through intermediate inputs, outputs, state, and responsibility boundaries. Ask the next why about the preceding mechanism; verify every causal link needed for the proposed fix. Mark unsupported links as assumptions.

If the chain loses its subject, a failure recurs, or the next move is another exception, zoom out: restate the outcome, execution order, contracts, source evidence, symptom location, and uncertain assumptions. Select a boundary, then zoom back into a test that can distinguish the suspected mechanism. A fixed number of why questions is not evidence.

Check the existing path and active rules first, then prior passing solutions and relevant decisions. Restore or refine a general solution before inventing another. Decide whether the cause belongs to data, state, code, prompt wording, measurement, tool capability, rendering, or workflow order. Where correctness depends on an unresolved domain judgment, consult the authoritative source or ask the responsible person about the concrete case.

An optimization may begin from a measured bottleneck and a falsifiable hypothesis rather than a defect. Test the hypothesis with a bounded comparison before claiming causality. If evidence cannot distinguish causes, report uncertainty and seek the next useful observation instead of adding a patch.

## Evolve Supporting Tools and Methods

An experiment may reveal that the next improvement needs better instrumentation, a method, a library, data preparation, a simulator, a test runner, or an evaluator. Improving or introducing that capability is legitimate evolution work when it enables a specific comparison, removes a measured bottleneck, or makes necessary evidence reliable. It need not produce an immediate product-score gain. If the tool itself is the requested target, define its outcome and whole scope in the opening agreement.

Before changing support tooling, state the evidence gap or bottleneck, the next experiment it enables, the existing capabilities checked for reuse, the smallest adequate change, its verification contract and affected consumers, and its cost within the remaining overall bound. Apply the same minimum-implementation and integration rules as product changes. Prefer adequate existing, standard, platform, or installed capabilities; a new library or method is allowed when the need is demonstrated and the existing options cannot meet it. Verify current primary documentation and compatibility where needed. Existing authorization covers necessary work within scope; obtain additional permission only when an actual permission, dependency policy, data exposure, cost, or side-effect boundary requires it.

Keep changes to the target and supporting tools distinguishable so their effects can be attributed. Verify the tool on independent contract cases and its real consumers before relying on it. Adopt a verified tool improvement against its declared contract; do not report improved experiment speed, coverage, or observability as improved target performance. Candidates for the agreed target still require the original whole-scope confirmation. If both must change together, declare the bundle and avoid claiming separate causal effects.

Evaluation changes require an additional comparison boundary: justify them from source evidence or a verified evaluator defect, validate the corrected measurement path, freeze its new version, and reassess baseline and candidate under it. Rescore preserved outputs only if they contain all information needed and execution behavior was unaffected; otherwise rerun the affected comparisons. Keep old results labeled with their old evaluator, and never compare old-baseline scores directly with new-evaluator scores. Correcting evaluation must not weaken the agreed product contract to make a candidate pass. Results used to design or choose the new method also count in data exposure history; re-establish independent coverage before subsequent confirmation.

Integrate reusable tooling into the existing owned workflow and remove superseded trial duplication while preserving raw evidence and required diagnostics. Charge tool construction, installation, verification, and retries to the same overall budget, then return to the experiment it enables. Do not let supporting work become an unbounded tool-building project; if it cannot be completed within the agreement, retain the established baseline and report the precise gap or scope change needed.

## Keep Changes in the Maintained Path

Before editing, state the integration point, existing elements to reuse/replace/merge/remove, preserved contracts, and before/after verification. Apply the local minimum-change rules: check necessity and existing implementation before adding structure. Review prompts and instructions with prompt-guide before executing or committing them; for skill changes use skill-review, which includes prompt-guide and skill-writing-guide.

Prefer a general change justified by the contract, input structure, or verified failure mechanism. For shared changes, check instruction hierarchy, role boundaries, output contracts, and previously passing behaviors; make approved contract changes explicit. Case-specific observations belong in experiment evidence and regression tests, not new runtime exceptions.

Judge complexity by responsibilities, relationships, state, and maintenance burden, not file or line counts alone. Required branches, recovery, or a new component can be valid within the approved scope when existing elements cannot meet the contract; explain the necessity, additional burden, and integration. Remove obsolete duplication and trial-only production branches. Do not remove required recovery, diagnostics, tests, or source evidence merely to shrink the code.

Component replay and isolated candidate configurations are useful for exploration. Product success must be demonstrated through the declared integrated path and affected consumers. If the required environment is unavailable, report the strongest verified level and defer the unsupported adoption or deployment claim.

After cleanup or integration changes, rerun affected checks on the final artifact. Preserve unrelated work, the prior baseline, raw evidence, and reproducible regression cases. Revert or isolate only the candidate changes that failed, without repeating completed paid calls, writes, messages, or learning events.

## Separate Development from Confirmation

The goal is the success criterion; out-of-sample describes the independence of the evidence used to test it. Whole-scope confirmation must assess the original agreed system-level outcome as well as every evaluation dimension, relevant operating condition, and consequential interaction. Map these to representative independent cases or checks before the run. The boundary is the system agreed at the start, not just the edited component and not every imaginable input or unrelated surrounding system.

Freeze the integrated candidate and criteria, then assess baseline and candidate under comparable conditions across that scope. Passing local development tests plus old common-regression tests does not replace this confirmation. Missing independent coverage or a required environment leaves the candidate unconfirmed; preserve it and report what is needed instead of silently omitting a dimension. Broad development checks can filter candidates before this gate, so every exploratory edit need not consume held-out data.

Give each source case/group a stable identity and record its provenance, role, and use history. Freeze references and permitted output variations before the comparison:

- **Development and common regression:** data examined to diagnose, adjust, choose candidates or methods, or prevent known regressions. Reuse freely within the authorized scope, but label the resulting scores as development evidence.
- **Candidate confirmation:** whole-scope evidence held out of the current candidate's development, evaluated after the candidate and criteria are frozen. Once results influence a later revision, those cases are development evidence for that revision and cannot confirm it independently. Replan independent coverage within the remaining budget before confirming a subsequent candidate.
- **Final evaluation:** whole-scope evidence reserved for the selected integrated system when a final performance or release claim is required. Do not spend this set on every development round. A confirmation run can also serve as final evaluation when that use and its criteria were set in advance and its independence is intact. If results guide a change or further selection, they no longer independently confirm that choice; obtain new evidence or qualify/defer the claim.

Separate at the unit that could leak information: source document, person, session, near-duplicate template, environment, event sequence, or time period as appropriate. Names changed in the same template, segments of one recording, or repeated model calls are not automatically independent samples. Check both content grouping and exposure history; a different split label is insufficient.

Use varied cases that test transfer and counterconditions, not paraphrases of a known failure alone. Record synthetic/same-author, expert, and real-user evidence distinctly. A fixed candidate tested on new cases supports only the population and conditions those cases represent. Where prior exposure of a third-party model is unknown, state that limit.

Keep comparison sets fixed within a round. When cases or environments change between rounds, retain a common anchor or rerun the baseline on the new set before attributing a score change to the candidate. Do not pool results from different versions as the current version's performance.

Use source evidence and domain judgment to decide correctness. Deterministic tools can calculate exact matches, rates, latency, cost, schema validity, and reproducible contract checks. Semantic judgments require evidence-based review by a qualified person or model, with uncertain cases marked; a model must not be its own sole source of truth. Follow applicable agent/script role guidance for LLM-assisted code.

## Decide, Stop, and Report

Apply protections before comparing improvements. Judge changes to the agreed target against its whole-scope criteria, and supporting-tool changes against the declared tool contract and affected consumers. For each separable candidate or declared change unit:

| Decision | Evidence and next action |
|---|---|
| Adopt | The intended benefit meets the agreed adoption criterion, protections and regression hold, and independent verification and integration for the declared scope above are complete. Use this artifact as the relevant next baseline. An allowed intermediate improvement does not imply the final goal is achieved; adoption is also distinct from deployment. |
| Reject | Harm, regression, lack of benefit, or dependence on an unsupported bypass is established. Isolate/revert the candidate and retain the reason. |
| Defer | Data, uncertainty, environment, or attribution cannot support a decision. Keep the accepted baseline and specify the evidence needed; preserve the candidate separately. |
| Keep | Current behavior is acceptable and no justified change is supported. Preserve it under common checks. Known unresolved defects remain open. |

A deterministic contract repair can use independent contract-based checks covering the agreed scope where statistical generalization is not the claim; explain their limit. This changes the form of evidence, not the required coverage. Cost/speed/simplicity improvements still have to preserve the agreed quality and reliability constraints.

End successfully when the final target and protections pass whole-scope independent evaluation. Stop or redirect the dependent experiment when a protection is breached, an authorized limit would be exceeded, necessary permission/evidence is missing, or the agreed lack-of-progress condition is met. End each comparison at its declared stopping point. A new round, retry, or candidate does not reset the overall bound. If time or resources end before confirmation, report progress and the unconfirmed candidate, not success.

Keep raw results and the resume point. Continue safe independent work within the remaining limits. Start another round only for a useful unresolved question with authorization and resources for the necessary work; otherwise retain the baseline rather than manufacture another change.

Before promoting a candidate, review the actual changed artifact and nearby contracts. Check for case tuning, conflicting rules, responsibility drift, moved failures, and disconnected patches. Complete the applicable project review process on the final artifact. Preserve the existing trigger and authorization boundaries of the target unless the user requested their change.

Report the result without creating a second management system:

- Agreed final target and intermediate adoption criterion; whole-scope coverage, checked dimensions, evidence levels, and unverified gaps.
- Focus and rationale; baseline/candidate, tool, evaluator, and data versions; cases/groups, initial state, criteria, and bounds.
- Verified mechanism or remaining hypothesis; product and supporting changes, separate/bundled effects, and what each experiment taught.
- Run status and evidence validity; focused and broad results with denominators, missing/failed cases, regressions, independent confirmation, uncertainty, and resource use.
- Adoption decision and final-goal status separately; total resources used/remaining, stopping reason, remaining defects, and the next discriminating question or exact resume requirement.

A successful round leaves a clearer maintained path, preserved evidence, and a justified decision. Evaluation records and experimental candidates remain outside the product's execution path.
