// Throwaway, shared policy for all three provider-selection visual variants.
// The approved planning Answers, not the historical runtime objectives, define this policy.
(function () {
  'use strict';

  const data = window.RatingsData;
  const objectives = {
    cap: 'Highest capability',
    ppi: 'Best value',
    price: 'Lowest qualifying price'
  };
  const roles = [
    { id: 'explorer', label: 'Explorer', index: 'Intelligence', objective: 'ppi', description: 'Find and explain existing code and repository behavior.' },
    { id: 'researcher', label: 'Researcher', index: 'Intelligence', objective: 'ppi', description: 'Verify external facts and produce sourced findings.' },
    { id: 'planner', label: 'Planner', index: 'Intelligence', objective: 'cap', description: 'Choose an approach and produce decisions and an actionable plan.' },
    { id: 'coder', label: 'Coder', index: 'Coding', objective: 'cap', description: 'Make and verify changes, including fault diagnosis.' },
    { id: 'reviewer', label: 'Reviewer', index: 'Coding', objective: 'cap', description: 'Assess changes or proposals independently.' },
    { id: 'coordinator', label: 'Coordinator', index: 'Agentic', objective: 'cap', description: 'Divide and delegate work, manage dependencies and combine results.' },
    { id: 'generalist', label: 'Generalist', index: 'Intelligence', objective: 'ppi', description: 'Handle mixed, end-to-end work when no specialist fits.' },
    { id: 'utility', label: 'Utility', index: 'Intelligence', objective: 'price', description: 'Produce bounded auxiliary outputs; short output does not imply low capability needs.' }
  ];
  const shortcuts = ['OpenAI', 'Anthropic', 'Google', 'DeepSeek', 'xAI'];
  const textOrder = (a, b) => a < b ? -1 : a > b ? 1 : 0;
  const providers = [...new Set([...data.models.map(model => model.provider), ...shortcuts])].sort(textOrder);
  const effortById = new Map(data.efforts.map(effort => [effort.id, effort]));
  const scenarios = [
    { id: 'recorded', label: 'Recorded curated fixture', description: 'Copied fixture values. Terminal-Bench and OpenRouter metadata are synthesized in the original fixture; this is not live market advice.' },
    { id: 'missing-timing', label: 'Synthetic preview: missing timing', description: 'Hide all recorded Artificial Analysis timing for GPT-5.6 Luna at every effort. Scores and matching task costs remain unchanged; no replacement timing is invented.' }
  ];
  const baseRecords = data.models.flatMap(model => model.configurations.map(configuration => ({ model, configuration })));
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const nonnegative = value => finite(value) && value >= 0;
  const present = value => finite(value) ? value : null;
  const configurationKey = (model, configuration) => model.key + '::' + configuration.effort;
  const sourceUrl = data.sources.artificialAnalysis.sourceUrl;
  const number = (value, digits = 4) => finite(value) ? Number(value.toFixed(digits)).toString() : 'unavailable';
  const money = value => '$' + number(value, 6);

  // Existing distinct-value grading: equal values never split, small sets may skip bands.
  function grades(values) {
    const ordered = [...new Set(values.filter(finite))].sort((a, b) => b - a);
    return new Map(ordered.map((value, index) => [value, 5 - Math.floor(index * 5 / ordered.length)]));
  }

  function recordsFor(scenario) {
    if (scenario !== 'missing-timing') return baseRecords;
    return baseRecords.map(record => record.model.key === 'gpt-5-6-luna' ? {
      model: record.model,
      configuration: { ...record.configuration, firstAnswer: null, outputSpeed: null, firstToken: null, response500: null, syntheticTiming: true }
    } : record);
  }

  function compare(a, b, objective, index) {
    let difference;
    if (index !== 'Intelligence') difference = b.score - a.score;
    else if (objective === 'ppi') difference = b.value - a.value || b.score - a.score || a.cost - b.cost;
    else if (objective === 'price') difference = a.cost - b.cost || b.score - a.score;
    else difference = b.score - a.score || a.cost - b.cost;
    return difference || a.effortOrder - b.effortOrder || textOrder(a.modelKey, b.modelKey);
  }

  function requiredReason(row, context) {
    if (!context.supported) return context.unsupportedReason;
    if (!finite(row.score)) {
      return context.index === 'Intelligence'
        ? 'No Artificial Analysis Intelligence score is recorded at this effort; a matching Intelligence task cost is also required.'
        : 'No Artificial Analysis ' + context.index + ' score is recorded at this effort. Other indexes and independent sources are not substitutes.';
    }
    if (context.index === 'Intelligence' && !nonnegative(row.cost)) return 'A finite, non-negative matching Intelligence benchmark task cost is unavailable at this effort. Token list prices and other benchmarks are not substitutes.';
    if (context.objective === 'ppi' && row.cost === 0) return 'Best value needs a positive matching Intelligence benchmark task cost. A published zero does not provide a finite capability-per-dollar ratio.';
    if (context.objective === 'price' && row.grade < 2) return 'This effort does not meet the inclusive capability grade 2 minimum for Lowest qualifying price.';
    return null;
  }

  function rowFor(record, context) {
    const model = record.model;
    const configuration = record.configuration;
    const effort = effortById.get(configuration.effort);
    const score = present(configuration.scores[context.index]);
    const cost = context.index === 'Intelligence' && nonnegative(configuration.intelligenceCost) ? configuration.intelligenceCost : null;
    const metadata = model.metadata;
    const row = {
      key: configurationKey(model, configuration),
      modelKey: model.key,
      name: model.name,
      provider: model.provider,
      effort: effort ? effort.label : 'Unspecified',
      effortOrder: effort ? effort.order : data.efforts.length,
      effortId: configuration.effort,
      score,
      grade: finite(score) ? context.indexGrades[context.index].get(score) : null,
      cost,
      value: context.index === 'Intelligence' && finite(score) && cost > 0 ? score / cost : null,
      firstAnswer: nonnegative(configuration.firstAnswer) ? configuration.firstAnswer : null,
      outputSpeed: nonnegative(configuration.outputSpeed) ? configuration.outputSpeed : null,
      firstToken: nonnegative(configuration.firstToken) ? configuration.firstToken : null,
      response500: nonnegative(configuration.response500) ? configuration.response500 : null,
      tokenShare: metadata && finite(metadata.tokenShare) ? metadata.tokenShare : null,
      vision: metadata && Array.isArray(metadata.inputModalities) ? metadata.inputModalities.includes('image') : null,
      frontier: null,
      replacement: null,
      reason: null,
      sourceUrl: configuration.artificialAnalysis ? sourceUrl : data.sources.deepSWE.sourceUrl,
      sourceOnly: !model.canonical,
      syntheticTiming: !!configuration.syntheticTiming,
      index: context.index,
      selected: false
    };
    row.reason = requiredReason(row, context);
    return row;
  }

  function dominates(candidate, row) {
    return candidate.key !== row.key && candidate.score >= row.score && candidate.cost <= row.cost && (candidate.score > row.score || candidate.cost < row.cost);
  }

  function contextFor(input) {
    const state = input || {};
    const role = roles.find(candidate => candidate.id === state.role) || roles[0];
    const objective = Object.hasOwn(objectives, state.objective) ? state.objective : role.objective;
    const provider = typeof state.provider === 'string' ? state.provider : 'all';
    const filter = state.filter === '4' || state.filter === '5' ? state.filter : 'all';
    const scenario = scenarios.some(candidate => candidate.id === state.scenario) ? state.scenario : 'recorded';
    const records = recordsFor(scenario);
    const supported = role.index === 'Intelligence' || objective === 'cap';
    const unsupportedReason = supported ? null : objectives[objective] + ' is unavailable for the ' + role.index + ' index: no matching benchmark task-cost basis is established. Your objective selection is retained; choose Highest capability to compare these scores.';
    const context = {
      role, objective, provider, filter, scenario, records, index: role.index, supported, unsupportedReason,
      scopedModels: data.models.filter(model => provider === 'all' || model.provider === provider),
      scopeLabel: provider === 'all' ? 'All providers' : provider + ' only',
      indexGrades: Object.fromEntries(['Intelligence', 'Coding', 'Agentic'].map(index => [index, grades(records.map(record => record.configuration.scores[index]))])),
      selectedByModel: new Map(), replacements: new Map(), filteredOut: [], unranked: []
    };
    context.rows = records.map(record => rowFor(record, context));
    context.rowsByKey = new Map(context.rows.map(row => [row.key, row]));
    context.recordByKey = new Map(records.map(record => [configurationKey(record.model, record.configuration), record]));
    const inScope = row => provider === 'all' || row.provider === provider;
    context.comparisonRows = role.index === 'Intelligence'
      ? context.rows.filter(row => inScope(row) && finite(row.score) && nonnegative(row.cost))
      : [];

    // ponytail: this tiny immutable fixture uses a quadratic sweep; index the skyline only for a full live catalog.
    for (const row of context.comparisonRows) {
      const dominators = context.comparisonRows.filter(candidate => dominates(candidate, row));
      row.frontier = dominators.length === 0;
      if (!dominators.length) continue;
      const sameEffort = dominators.filter(candidate => candidate.effortOrder === row.effortOrder);
      const pool = sameEffort.length ? sameEffort : dominators;
      pool.sort((a, b) => b.score - a.score || a.cost - b.cost || a.effortOrder - b.effortOrder || textOrder(a.modelKey, b.modelKey));
      const replacement = pool[0];
      context.replacements.set(row.key, replacement);
      row.replacement = {
        key: replacement.key, name: replacement.name, effort: replacement.effort,
        provider: replacement.provider, score: replacement.score, cost: replacement.cost,
        scoreGain: replacement.score - row.score, costSaving: row.cost - replacement.cost,
        basis: sameEffort.length ? 'same effort' : 'cross-effort fallback'
      };
    }
    context.frontierPath = context.comparisonRows.filter(row => row.frontier).sort((a, b) => a.cost - b.cost || b.score - a.score || a.effortOrder - b.effortOrder || textOrder(a.modelKey, b.modelKey));

    if (supported) {
      for (const model of context.scopedModels) {
        const modelRows = context.rows.filter(row => row.modelKey === model.key);
        const eligible = modelRows.filter(row => row.reason === null).sort((a, b) => compare(a, b, objective, role.index));
        if (!eligible.length) {
          const measured = modelRows[0];
          if (measured) context.unranked.push({ ...measured, reason: modelReason(model, modelRows, context) });
          continue;
        }
        const selected = eligible[0];
        selected.selected = true;
        context.selectedByModel.set(model.key, selected);
      }
    }
    const selectedRows = [...context.selectedByModel.values()].sort((a, b) => compare(a, b, objective, role.index));
    context.filteredOut = filter === 'all' ? [] : selectedRows.filter(row => row.grade < Number(filter)).map(row => ({ ...row, reason: 'The objective selects ' + row.effort + ' with capability grade ' + row.grade + ', below the active grade ' + filter + ' display filter. The filter does not select another effort.' }));
    context.ranked = filter === 'all' ? selectedRows : selectedRows.filter(row => row.grade >= Number(filter));
    return context;
  }

  function modelReason(model, rows, context) {
    if (!rows.some(row => finite(row.score))) return 'No Artificial Analysis ' + context.index + ' score is recorded for any measured effort. ' + (model.canonical ? 'No other index is substituted.' : 'This is an identifiable DeepSWE source-only model; its independent score cannot replace the selected index.');
    if (context.index === 'Intelligence' && !rows.some(row => finite(row.score) && nonnegative(row.cost))) return 'No measured effort has both an Intelligence score and a finite, non-negative matching Intelligence benchmark task cost.';
    if (context.objective === 'ppi' && !rows.some(row => finite(row.score) && row.cost > 0)) return 'No measured effort has a positive matching Intelligence task cost, so Best value is unavailable for this model.';
    if (context.objective === 'price') return 'No otherwise eligible measured effort meets the inclusive capability grade 2 minimum for Lowest qualifying price.';
    return 'No measured effort has the data required by the active objective.';
  }

  function activeConstraints(context) {
    return context.role.label + ', ' + context.scopeLabel + ', ' + objectives[context.objective] + ', ' + (context.filter === 'all' ? 'all capability grades' : 'capability grade ' + context.filter + ' or higher');
  }

  function evaluate(state) {
    const context = contextFor(state);
    let sections = [];
    if (context.ranked.length && context.index === 'Intelligence') {
      sections = [
        { title: 'Cost frontier', kind: 'frontier', rows: context.ranked.filter(row => row.frontier) },
        { title: 'Dominated configurations', kind: 'dominated', rows: context.ranked.filter(row => row.frontier === false) }
      ].filter(section => section.rows.length);
    } else if (context.ranked.length) sections = [{ title: context.index + ' comparison', kind: 'ranked', rows: context.ranked }];
    const selectedProviders = context.provider === 'all' ? providers : [context.provider];
    const picks = selectedProviders.map(provider => {
      const candidates = context.ranked.filter(row => row.provider === provider);
      let reason = null;
      if (!context.supported) reason = context.unsupportedReason;
      else if (!candidates.length) {
        const models = context.scopedModels.filter(model => model.provider === provider);
        reason = 'No qualifying configuration for ' + provider + ' under ' + activeConstraints(context) + '. ' + (models.length ? 'Required data and the active constraints are not relaxed.' : 'This small curated fixture contains no models for this creator; this is not a statement about real provider coverage.');
      } else if (candidates.length === 1) reason = 'Only one distinct model qualifies for this creator under the active constraints. No runner-up is fabricated.';
      return { provider, primary: candidates[0] || null, runnerUp: candidates[1] || null, reason };
    });
    const notices = [];
    if (context.scenario === 'missing-timing') notices.push('Synthetic preview: all Artificial Analysis timing for GPT-5.6 Luna is hidden. Scores and matching task costs are unchanged; timing never affects selection.');
    if (!context.supported) notices.push(context.unsupportedReason);
    else if (!context.ranked.length) notices.push('No qualifying configuration for ' + activeConstraints(context) + '. Your selections are retained; no effort, creator or data requirement is substituted.');
    return {
      role: context.role, objective: context.objective, index: context.index,
      supported: context.supported, unsupportedReason: context.unsupportedReason,
      scope: context.scopeLabel + (context.index === 'Intelligence' ? ' · Intelligence comparisons across all measured efforts' : ' · ' + context.index + ' scores; cost comparisons unavailable'),
      ranked: context.ranked, sections, unranked: context.unranked, picks,
      totalModels: context.scopedModels.length, comparisonCount: context.comparisonRows.length,
      notice: notices.length ? notices.join(' ') : null,
      frontierPath: context.frontierPath, comparisonRows: context.comparisonRows,
      filteredOut: context.filteredOut,
      gradeReference: gradeReference(context)
    };
  }

  function gradeReference(context) {
    const scores = context.records.map(record => record.configuration.scores[context.index]).filter(finite);
    return {
      index: context.index, configurations: scores.length, distinctScores: new Set(scores).size,
      description: 'Capability grades 1–5 use distinct ' + context.index + ' scores across all scored model × effort configurations in the refresh, before provider selection, capability display filters and the price floor. Higher is better; equal scores share a band. Independent sources have separate per-effort grade populations.'
    };
  }

  function independentGrades(context, field, effort) {
    return grades(context.records.filter(record => record.configuration.effort === effort).map(record => {
      const rating = record.configuration[field];
      return rating ? rating.value : null;
    }));
  }

  function ratingsFor(record, context) {
    const configuration = record.configuration;
    const ratings = ['Intelligence', 'Coding', 'Agentic'].map(index => {
      const value = present(configuration.scores[index]);
      return {
        source: 'Artificial Analysis', label: index + ' score', value,
        grade: finite(value) ? context.indexGrades[index].get(value) : null,
        sourceUrl, unit: 'index points', formattedValue: finite(value) ? number(value) : '—',
        synthetic: false,
        note: 'Curated preview fixture, not live market advice. Grade population: all scored configurations for this index, across efforts and creators.'
      };
    });
    for (const [field, label, ratingLabel] of [['deepSWE', 'DeepSWE', 'Pass rate on one attempt'], ['terminalBench', 'Terminal-Bench', 'Best-agent accuracy']]) {
      const source = data.sources[field];
      const rating = configuration[field];
      const value = rating ? present(rating.value) : null;
      ratings.push({
        source: label, label: ratingLabel, value,
        grade: finite(value) ? independentGrades(context, field, configuration.effort).get(value) : null,
        sourceUrl: source.sourceUrl, unit: 'fraction',
        formattedValue: finite(value) ? number(value * 100, 2) + '%' : '—',
        synthetic: source.synthetic, note: source.note,
        agent: rating && (rating.agentLabel || rating.agent) || null,
        confidenceLow: rating && present(rating.confidenceLow), confidenceHigh: rating && present(rating.confidenceHigh),
        standardError: rating && present(rating.standardError), date: rating && rating.date || null,
        submissions: field === 'terminalBench' ? configuration.terminalBenchSubmissions : undefined
      });
    }
    return ratings;
  }

  function alternativesFor(row, context) {
    if (context.index !== 'Intelligence' || !context.comparisonRows.some(candidate => candidate.key === row.key)) return [];
    return context.comparisonRows.filter(candidate => candidate.cost < row.cost && candidate.score >= row.score - 5)
      .sort((a, b) => a.cost - b.cost || b.score - a.score || a.effortOrder - b.effortOrder || textOrder(a.modelKey, b.modelKey)).slice(0, 3);
  }

  function pricingFor(configuration) {
    if (!configuration.pricing) return [];
    const labels = {
      price_1m_input_tokens: 'Input tokens', price_1m_output_tokens: 'Output tokens',
      price_1m_cache_hit_tokens: 'Cached input tokens', price_1m_cache_write_tokens: 'Cache-write tokens'
    };
    return Object.entries(labels).map(([key, label]) => ({ label, value: present(configuration.pricing[key]), unit: 'USD per million tokens', sourceUrl, note: 'Token list price, not a benchmark task cost or a model-selection input.' }));
  }

  function explanationFor(row, record, context, selected, alternatives) {
    const parts = [];
    const objectiveRule = context.index !== 'Intelligence'
      ? context.index + ' score descending, then lower reasoning effort and canonical model identity. Intelligence cost is not a tie-break.'
      : context.objective === 'ppi' ? 'Intelligence score divided by positive matching Intelligence task cost, then score descending and task cost ascending.'
        : context.objective === 'price' ? 'Matching Intelligence task cost ascending, then Intelligence score descending, after the inclusive capability grade 2 floor.'
          : 'Intelligence score descending, then matching Intelligence task cost ascending.';
    parts.push(context.role.label + ' uses the Artificial Analysis ' + context.index + ' index as a published-score proxy, not verified role performance. ' + (context.supported ? objectives[context.objective] + ' compares ' + objectiveRule + ' Remaining exact ties prefer lower reasoning effort, then canonical model identity.' : context.unsupportedReason));
    if (selected) {
      parts.push('The same objective keys select one measured effort within ' + row.name + ' and order the selected models. The selected effort is ' + selected.effort + ', with ' + context.index + ' score ' + number(selected.score) + (context.index === 'Intelligence' ? ' and matching task cost ' + money(selected.cost) : '') + '. ' + (row.key === selected.key ? 'This is that selected configuration.' : 'You are inspecting the separate measured ' + row.effort + ' configuration, not a fallback selection.') + ' The capability display filter is applied only after effort selection.');
      if (context.filter !== 'all') parts.push(selected.grade >= Number(context.filter) ? 'The selected configuration meets the active capability grade ' + context.filter + ' or higher display filter.' : 'The selected configuration is capability grade ' + selected.grade + ', so the active grade ' + context.filter + ' or higher filter hides it. A higher effort is not substituted to satisfy that display filter.');
    } else if (context.provider !== 'all' && row.provider !== context.provider) parts.push('This model is outside the active provider selection. It is not a candidate or a comparison point in this scope.');
    else parts.push('No objective-selected effort qualifies for this model. ' + (context.supported ? modelReason(record.model, context.rows.filter(candidate => candidate.modelKey === row.modelKey), context) : context.unsupportedReason));
    if (row.reason && selected && row.key !== selected.key) parts.push('This inspected configuration is not eligible: ' + row.reason);
    const reference = gradeReference(context);
    parts.push((row.grade === null ? 'The inspected configuration has no selected-index capability grade. ' : 'Its selected-index capability grade is ' + row.grade + ' of 5. ') + reference.description + ' This fixture has ' + reference.configurations + ' scored configurations and ' + reference.distinctScores + ' distinct scores for ' + context.index + '.');
    if (!record.model.canonical) parts.push('Source-only identity: ' + record.model.sourceIdentity.model + ' in DeepSWE. No Artificial Analysis identity row is loaded, so its alias is not promoted to a canonical scored model. Creator attribution comes from the fixture README, not an Artificial Analysis join.');
    if (context.index === 'Intelligence') {
      parts.push('Advisory scope: ' + context.scopeLabel + ', across all ' + context.comparisonRows.length + ' scored-and-priced measured configurations. Neither the capability display filter nor the Lowest qualifying price floor removes advisory points. The benchmark task cost is the published Intelligence workload cost at this effort, not token list pricing or another benchmark run cost.');
      if (row.frontier === true) parts.push('This configuration is on the cost frontier in the active scope: no comparison point has an equal-or-higher Intelligence score at equal-or-lower task cost with at least one strict improvement.');
      if (row.frontier === false) {
        const replacement = context.replacements.get(row.key);
        parts.push('This configuration is dominated in the active scope. Preferred replacement: ' + replacement.name + ' at ' + replacement.effort + ', score ' + number(replacement.score) + ' at ' + money(replacement.cost) + '. It gains ' + number(replacement.score - row.score) + ' Intelligence points and saves ' + money(row.cost - replacement.cost) + ' per benchmark task. Replacement selection prefers a same-effort strict improvement; only if none exists does it compare other efforts. Within that pool it maximizes score gain, then cost saving.');
      }
      if (row.frontier === null) parts.push('No cost-frontier claim is available for this configuration in the active scope.');
      if (context.frontierPath.length) parts.push('Full-effort frontier path, ordered by benchmark task cost: ' + context.frontierPath.map(point => point.name + ' (' + point.effort + '): ' + number(point.score) + ' at ' + money(point.cost)).join(' → ') + '.');
      parts.push(alternatives.length ? 'Separate cheaper alternatives: ' + alternatives.map(alternative => alternative.name + ' (' + alternative.effort + '), score ' + number(alternative.score) + ' at ' + money(alternative.cost)).join('; ') + '. These are the top three lower-cost configurations with an Intelligence score no more than five points below the inspected score, ordered by task cost. They are not provider-pick runner-ups.' : 'No cheaper alternative meets the active comparison scope and the Intelligence score band of no more than five points below this configuration.');
    } else parts.push('Matching ' + context.index + ' task cost is not established. Capability per dollar, lowest-price advice, the cost frontier, dominated replacements and cheaper alternatives are unavailable for this index. Intelligence costs are not reused.');
    parts.push((row.firstAnswer === null ? 'Time to first answer token is unavailable (—); it is not reconstructed or replaced.' : 'Time to first answer token is the recorded median ' + number(row.firstAnswer) + ' seconds, including thinking.') + ' Output tokens per second is a separate throughput measure' + (row.outputSpeed === null ? ' and is unavailable (—).' : ': ' + number(row.outputSpeed) + '.') + ' Timing never filters, orders or breaks ties. The separately recorded Time to first token and Estimated response time for 500 answer tokens are not whole-agent task durations.');
    if (record.model.metadata) {
      const metadata = record.model.metadata;
      parts.push('Synthesized OpenRouter preview metadata: context window ' + metadata.contextLength.toLocaleString('en-US') + ' tokens; input ' + metadata.inputModalities.join(', ') + '; output ' + metadata.outputModalities.join(', ') + '. These hand-written metadata values are not live capability measurements.');
    } else parts.push('No OpenRouter context or modality record is loaded for this model; those capabilities are unavailable, not inferred.');
    const pricing = pricingFor(record.configuration).filter(price => price.value !== null);
    if (pricing.length) parts.push('Recorded token list prices, separate from task cost: ' + pricing.map(price => price.label + ' ' + money(price.value) + ' per million tokens').join('; ') + '. They are not used for eligibility, value, price ranking or ties.');
    parts.push('OpenRouter 30-day token share is unavailable in this fixture. If recorded, it is display-only and never affects eligibility, ordering, ties or grades. DeepSWE and Terminal-Bench ratings remain independent; Terminal-Bench submissions are explicitly synthesized preview data.');
    if (row.syntheticTiming) parts.push('Synthetic preview active: all recorded Artificial Analysis timing for this model has been hidden; its scores and matching costs are unchanged.');
    return parts.join('\n\n');
  }

  function details(key, state) {
    const context = contextFor(state);
    let row = context.rowsByKey.get(key);
    if (!row) {
      const model = data.models.find(candidate => candidate.key === key);
      if (!model) return null;
      row = context.selectedByModel.get(model.key) || context.rows.find(candidate => candidate.modelKey === model.key);
    }
    if (!row) return null;
    const record = context.recordByKey.get(row.key);
    const selected = context.selectedByModel.get(row.modelKey) || null;
    const alternatives = alternativesFor(row, context);
    const configurations = context.rows.filter(candidate => candidate.modelKey === row.modelKey).sort((a, b) => a.effortOrder - b.effortOrder);
    const directRank = context.ranked.findIndex(candidate => candidate.key === row.key);
    const providerRows = context.ranked.filter(candidate => candidate.provider === row.provider);
    const providerRank = providerRows.findIndex(candidate => candidate.key === row.key);
    return {
      row, configurations, ratings: ratingsFor(record, context), alternatives,
      replacement: context.replacements.get(row.key) || null,
      explanation: explanationFor(row, record, context, selected, alternatives),
      sourceUrl: row.sourceUrl,
      frontierPath: context.frontierPath, comparisonRows: context.comparisonRows,
      gradeReference: gradeReference(context),
      metadata: record.model.metadata || { contextLength: null, inputModalities: null, outputModalities: null, tokenShare: null, synthetic: false, note: 'No OpenRouter metadata record is loaded for this model.' },
      pricing: pricingFor(record.configuration),
      sourceIdentity: { canonical: record.model.canonical, modelKey: record.model.key, artificialAnalysis: record.configuration.artificialAnalysis, deepSWE: record.configuration.deepSWE, providerSource: record.model.providerSource },
      selection: {
        selected, isSelected: !!selected && selected.key === row.key,
        eligible: row.reason === null && (context.provider === 'all' || row.provider === context.provider),
        reason: row.reason, directRank: directRank >= 0 ? directRank + 1 : null,
        providerRank: providerRank >= 0 ? providerRank + 1 : null,
        capabilityFilter: context.filter, priceFloor: context.objective === 'price' && context.index === 'Intelligence' ? 2 : null,
        objective: context.objective, index: context.index,
        timingAffectsOrder: false
      }
    };
  }

  window.Ratings = { roles, objectives, providers, snapshot: data.snapshot, scenarios, evaluate, details };
}());
