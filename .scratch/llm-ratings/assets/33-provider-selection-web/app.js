/* Throwaway UI only. Policy and fixture data stay in policy.js and data.js. */
(() => {
  'use strict';

  const ratings = window.Ratings;
  const app = document.getElementById('app');
  const modelDialog = document.getElementById('model-dialog');
  const policyDialog = document.getElementById('policy-dialog');
  const previewDialog = document.getElementById('preview-dialog');
  const switcher = document.getElementById('prototype-switcher');
  const variants = { A: 'Focus desk', B: 'Comparison canvas', C: 'Provider lens' };
  const shortcutProviders = ['all', 'OpenAI', 'Anthropic', 'Google', 'DeepSeek', 'xAI'];
  const explorer = ratings.roles.find(role => role.label === 'Explorer') || ratings.roles[0];
  const initialVariant = new URL(location.href).searchParams.get('variant');
  const state = {
    variant: Object.hasOwn(variants, initialVariant) ? initialVariant : 'A',
    role: explorer.id, objective: explorer.objective, provider: 'all', filter: 'all',
    scenario: 'recorded', view: 'table', selectedKey: null, detailOpen: false
  };
  const localPreview = location.protocol === 'file:' || ['localhost', '127.0.0.1', '[::1]', '::1'].includes(location.hostname)
    || new URL(location.href).searchParams.get('prototype') === '1';
  const providerNames = [...new Set([...shortcutProviders.slice(1), ...ratings.providers])];
  const filters = { all: 'All capability grades', 4: 'Grade 4 or higher', 5: 'Grade 5 only' };
  let result;
  let selectedDetail;
  let detailTriggerId = null;
  const inlineInTable = () => matchMedia('(min-width: 1180px)').matches;

  const escape = value => String(value ?? '').replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const number = (value, maximumFractionDigits = 1, minimumFractionDigits = 0) => finite(value)
    ? new Intl.NumberFormat('en-US', { maximumFractionDigits, minimumFractionDigits }).format(value)
    : '<span class="unavailable" title="Unavailable in this fixture">—</span>';
  const cost = value => finite(value) ? `$${number(value, 4, 3)}` : number(null);
  const grade = value => finite(value) ? `<span class="grade">Grade ${number(value, 0)} of 5</span>` : number(null);
  const providerLabel = () => state.provider === 'all' ? 'All providers' : state.provider;
  const intelligence = () => result.index === 'Intelligence';
  const policyState = () => ({ role: state.role, objective: state.objective, provider: state.provider, filter: state.filter, scenario: state.scenario });
  const externalLink = (url, label, className = '') => /^https?:\/\//i.test(url || '')
    ? `<a class="${className}" href="${escape(url)}" target="_blank" rel="noopener noreferrer">${escape(label)}</a>`
    : escape(label);
  const sourceAddress = url => String(url || '').replace(/^https?:\/\//, '');

  function field(name, label, options) {
    return `<label class="field" for="${name}-select"><span>${label}</span><select id="${name}-select" data-state="${name}">${options}</select></label>`;
  }

  function roleChooser() {
    return field('role', 'Role', ratings.roles.map(role => `<option value="${escape(role.id)}" ${state.role === role.id ? 'selected' : ''}>${escape(role.label)}</option>`).join(''));
  }

  function providerChooser() {
    return field('provider', 'Full provider chooser', `<option value="all" ${state.provider === 'all' ? 'selected' : ''}>All providers</option>${providerNames.map(provider => `<option value="${escape(provider)}" ${state.provider === provider ? 'selected' : ''}>${escape(provider)}</option>`).join('')}`);
  }

  function objectiveControls(includeRole = false, includeProvider = false) {
    return `<div class="selection-controls">${includeRole ? roleChooser() : ''}
      ${field('objective', 'Objective', Object.entries(ratings.objectives).map(([id, label]) => `<option value="${id}" ${state.objective === id ? 'selected' : ''}>${escape(label)}</option>`).join(''))}
      ${field('filter', 'Capability filter', ['all', '4', '5'].map(id => `<option value="${id}" ${state.filter === id ? 'selected' : ''}>${id === 'all' ? 'All grades' : filters[id]}</option>`).join(''))}
      ${includeProvider ? providerChooser() : ''}
    </div>`;
  }

  function roleNavigation(position) {
    return `<nav class="role-navigation ${position}" aria-label="Choose a role">${ratings.roles.map(role => `<button type="button" id="role-${escape(role.id)}" data-role="${escape(role.id)}" aria-pressed="${state.role === role.id}"><span>${escape(role.label)}</span>${position === 'role-rail' && state.role === role.id ? `<small>${escape(role.index)} index</small>` : ''}</button>`).join('')}</nav>`;
  }

  function providerControls(rail = false, includeChooser = true) {
    return `<section class="provider-controls ${rail ? 'provider-rail-controls' : ''}" aria-label="Provider selection">
      ${rail || includeChooser ? `<h2 class="control-heading">${rail ? 'Model creator' : 'Provider'}</h2>` : ''}
      <div class="provider-shortcuts">${shortcutProviders.map((provider, index) => `<button type="button" id="provider-shortcut-${index}" data-provider="${provider}" aria-pressed="${state.provider === provider}">${provider === 'all' ? 'All providers' : provider}</button>`).join('')}</div>
      ${includeChooser ? providerChooser() : ''}
      ${rail ? '<p class="rail-note">A provider is the model creator, not an API gateway.</p>' : ''}
    </section>`;
  }

  function tabs() {
    return `<div class="view-tabs" role="tablist" aria-label="Comparison view"><button type="button" id="view-table" role="tab" aria-selected="${state.view === 'table'}" aria-controls="results" tabindex="${state.view === 'table' ? 0 : -1}" data-view="table">Model table</button><button type="button" id="view-picks" role="tab" aria-selected="${state.view === 'picks'}" aria-controls="results" tabindex="${state.view === 'picks' ? 0 : -1}" data-view="picks">Provider picks</button></div>`;
  }

  function roleHeader() {
    return `<div class="role-heading"><h1>${escape(result.role.label)} models</h1><p>${escape(result.role.description)}</p></div>`;
  }

  function scenarioNotice() {
    if (state.scenario === 'recorded') return '';
    const scenario = ratings.scenarios.find(item => item.id === state.scenario);
    return `<aside class="scenario-notice" aria-label="Active preview state"><strong>Preview state: ${escape(scenario?.label || state.scenario)}</strong><span>${escape(scenario?.description || '')}</span><button type="button" data-action="recorded">Use recorded fixture</button></aside>`;
  }

  function comparisonHeading() {
    return `<div class="comparison-heading"><div><h2>${state.view === 'table' ? 'Model comparison' : 'Primary and runner-up'}</h2><p class="comparison-scope" id="comparison-scope"><strong>${escape(providerLabel())}</strong><span>Advice scope: ${escape(result.scope)}</span></p></div><p class="result-count">${result.ranked.length} ranked ${result.ranked.length === 1 ? 'model' : 'models'}<span>${escape(result.index)} index</span></p></div>`;
  }

  function sourceCaption() {
    return `<p class="source-caption">${externalLink(ratings.snapshot.sourceUrl, 'Artificial Analysis')}<span>Preview fixture. ${dateLabel()}.</span><strong>Not live market advice.</strong></p>`;
  }

  function recoveries(unsupported = false) {
    if (unsupported) return '<button type="button" data-action="supported-objective">Use Highest capability</button>';
    return `${state.provider !== 'all' ? '<button type="button" data-action="all-providers">All providers</button>' : ''}${state.filter !== 'all' ? '<button type="button" data-action="clear-filter">Clear capability filter</button>' : ''}${state.scenario !== 'recorded' ? '<button type="button" data-action="recorded">Use recorded fixture</button>' : ''}`;
  }

  function emptyState(unsupported) {
    return `<section class="empty-state" aria-labelledby="empty-title"><h3 id="empty-title">${unsupported ? 'Objective unavailable' : 'No qualifying configuration'}</h3>
      <p>${unsupported ? escape(result.unsupportedReason || `${result.index} has no established matching task-cost basis for this objective.`) : 'No model meets the current selection in this preview fixture. This is not a statement about real-world provider coverage.'}</p>
      ${!unsupported && result.notice ? `<p>${escape(result.notice)}</p>` : ''}
      <p class="empty-constraints"><strong>${escape(result.role.label)}</strong>; ${escape(providerLabel())}; ${escape(ratings.objectives[state.objective])}; ${escape(filters[state.filter])}.</p>
      <div class="recovery-actions">${recoveries(unsupported)}</div></section>`;
  }

  function detailsButton(row, label = 'Details') {
    const expanded = state.selectedKey === row.key && state.detailOpen;
    return `<button type="button" id="model-details-${escape(row.key)}" class="detail-button" data-detail-key="${escape(row.key)}" aria-label="${escape(`${label} for ${row.name}, ${row.effort} effort`)}" ${state.variant === 'C' ? `aria-expanded="${expanded}"` : ''}>${label}</button>`;
  }

  function tableHeaders(picks = false) {
    return `<tr>${picks ? '<th scope="col" class="provider-column">Provider / pick</th>' : ''}<th scope="col" class="model-column">Model</th><th scope="col">Reasoning<br>effort</th><th scope="col" class="numeric">${escape(result.index)} score<span>Capability grade below</span></th>${intelligence() ? '<th scope="col" class="numeric">Benchmark<br>task cost<span>United States dollars</span></th><th scope="col" class="numeric">Capability<br>per dollar<span>Score ÷ task cost</span></th>' : ''}<th scope="col" class="numeric">Time to first<br>answer token<span>Seconds, including thinking</span></th>${state.variant !== 'B' ? '<th scope="col" class="numeric">Output tokens<br>per second</th>' : ''}<th scope="col"><span class="visually-hidden">Model details</span></th></tr>`;
  }

  function modelCells(row) {
    return `<th scope="row" class="model-name">${escape(row.name)}<span>${escape(row.provider)}</span></th><td class="effort-cell">${escape(row.effort)}</td><td class="numeric score-cell"><strong>${number(row.score)}</strong>${grade(row.grade)}</td>${intelligence() ? `<td class="numeric">${cost(row.cost)}</td><td class="numeric">${number(row.value, 1)}</td>` : ''}<td class="numeric">${number(row.firstAnswer)}</td>${state.variant !== 'B' ? `<td class="numeric">${number(row.outputSpeed)}</td>` : ''}<td>${detailsButton(row)}</td>`;
  }

  function inlineDetail() {
    if (!selectedDetail || !state.detailOpen) return '';
    return `<section class="inline-evidence" aria-label="Expanded model details"><div class="inline-toolbar"><span>Model evidence</span><button type="button" data-action="close-detail">Close details</button></div>${detailPanel(selectedDetail)}</section>`;
  }

  function comparisonColumns(picks = false) {
    if (state.variant !== 'B') return '';
    const widths = intelligence()
      ? picks ? [12, 20, 10, 12, 11, 11, 15, 9] : [24, 11, 14, 13, 13, 16, 9]
      : picks ? [14, 27, 13, 16, 20, 10] : [32, 15, 19, 24, 10];
    return `<colgroup>${widths.map(width => `<col style="width:${width}%">`).join('')}</colgroup>`;
  }

  function orderedPicks() {
    const priority = provider => {
      const index = shortcutProviders.indexOf(provider);
      return index < 0 ? shortcutProviders.length : index;
    };
    return result.picks.filter(pick => pick.primary).sort((a, b) => priority(a.provider) - priority(b.provider) || a.provider.localeCompare(b.provider));
  }

  function missingProviderDisclosure() {
    const missing = result.picks.filter(pick => !pick.primary);
    if (!missing.length) return '';
    return `<details id="missing-provider-data" class="missing-providers"><summary>No qualifying configuration for ${missing.length} ${missing.length === 1 ? 'creator' : 'creators'}</summary><p>These creators remain selectable. The reasons below describe the active role, objective and capability filter in this preview fixture, not real-world provider coverage.</p><dl>${missing.map(pick => `<div data-empty-provider="${escape(pick.provider)}"><dt>${escape(pick.provider)}</dt><dd>${escape(pick.reason || 'No matching scored model in this preview fixture.')}</dd></div>`).join('')}</dl></details>`;
  }

  function modelTable() {
    const columns = (intelligence() ? 8 : 6) - (state.variant === 'B' ? 1 : 0);
    return `<div class="table-scroll" tabindex="0" role="region" aria-label="Model comparison table, scroll horizontally for all metrics"><table class="model-table ${intelligence() ? 'has-cost' : ''} ${state.variant === 'B' ? 'canvas-table' : ''}">${comparisonColumns()}<thead>${tableHeaders()}</thead>${result.sections.map(section => `<tbody><tr class="section-row ${section.kind === 'frontier' ? 'frontier-section' : ''}"><th colspan="${columns}" scope="rowgroup">${escape(section.title)}<span>${section.rows.length} ${section.rows.length === 1 ? 'model' : 'models'}</span></th></tr>${section.rows.map(row => `<tr data-model-key="${escape(row.key)}" class="${state.selectedKey === row.key ? 'selected-row' : ''}">${modelCells(row)}</tr>${state.variant === 'C' && state.detailOpen && inlineInTable() && state.selectedKey === row.key ? `<tr class="expanded-row"><td colspan="${columns}">${inlineDetail()}</td></tr>` : ''}`).join('')}</tbody>`).join('')}</table></div>`;
  }

  function picksTable() {
    const columns = (intelligence() ? 9 : 7) - (state.variant === 'B' ? 1 : 0);
    return `<div class="table-scroll" tabindex="0" role="region" aria-label="Provider picks table, scroll horizontally for all metrics"><table class="model-table picks-table ${intelligence() ? 'has-cost' : ''} ${state.variant === 'B' ? 'canvas-table' : ''}">${comparisonColumns(true)}<thead>${tableHeaders(true)}</thead>${orderedPicks().map(pick => `<tbody data-pick-provider="${escape(pick.provider)}"><tr class="primary-pick ${state.selectedKey === pick.primary.key ? 'selected-row' : ''}"><td class="pick-provider"><strong>${escape(pick.provider)}</strong><span class="pick-priority">Primary</span></td>${modelCells(pick.primary)}</tr>${pick.runnerUp ? `<tr class="${state.selectedKey === pick.runnerUp.key ? 'selected-row' : ''}"><td class="pick-provider"><span>Runner-up</span></td>${modelCells(pick.runnerUp)}</tr>` : `<tr class="short-result"><td></td><td colspan="${columns - 1}">No runner-up. Only one distinct model qualifies for ${escape(pick.provider)} under the active constraints.</td></tr>`}</tbody>`).join('')}</table></div>`;
  }

  function shelfModel(row, priority) {
    if (!row) return '<td colspan="3" class="shelf-unavailable">No runner-up. Only one distinct model qualifies.</td>';
    const metric = intelligence() ? state.objective === 'ppi' ? number(row.value) : cost(row.cost) : number(row.firstAnswer);
    return `<td class="shelf-name ${priority === 'Primary' ? 'shelf-primary' : ''}"><div class="shelf-model-title"><strong>${escape(row.name)}</strong>${detailsButton(row)}</div><p>${escape(row.effort)} reasoning effort</p></td><td class="numeric shelf-score"><strong>${number(row.score)}</strong>${grade(row.grade)}</td><td class="numeric shelf-objective">${metric}</td>`;
  }

  function picksShelf() {
    const metricLabel = intelligence() ? state.objective === 'ppi' ? 'Capability per dollar' : 'Benchmark task cost' : 'Time to first answer token';
    const metricUnit = intelligence() ? state.objective === 'ppi' ? 'Score ÷ task cost' : 'United States dollars' : 'Seconds, including thinking';
    const metricHeaders = `<th scope="col">Model / reasoning effort</th><th scope="col" class="numeric">${escape(result.index)} score<span>Capability grade below</span></th><th scope="col" class="numeric">${metricLabel}<span>${metricUnit}</span></th>`;
    return `<div class="table-scroll" tabindex="0" role="region" aria-label="Primary and runner-up comparison shelf"><table class="pick-shelf"><colgroup><col style="width:10%"><col style="width:20%"><col style="width:11%"><col style="width:14%"><col style="width:20%"><col style="width:11%"><col style="width:14%"></colgroup><thead><tr><th scope="col" rowspan="2">Model creator</th><th scope="colgroup" colspan="3" class="primary-column-group">Primary</th><th scope="colgroup" colspan="3">Runner-up</th></tr><tr>${metricHeaders}${metricHeaders}</tr></thead><tbody>${orderedPicks().map(pick => `<tr data-pick-provider="${escape(pick.provider)}"><th scope="row">${escape(pick.provider)}</th>${shelfModel(pick.primary, 'Primary')}${shelfModel(pick.runnerUp, 'Runner-up')}</tr>${state.detailOpen && inlineInTable() && [pick.primary.key, pick.runnerUp?.key].includes(state.selectedKey) ? `<tr class="expanded-row"><td colspan="7">${inlineDetail()}</td></tr>` : ''}`).join('')}</tbody></table></div><p class="shelf-details-note">Open Details for independent ratings, published timing and the remaining task-cost or value metrics. No missing runner-up is substituted.</p>`;
  }

  function unrankedModels() {
    if (!result.unranked.length) return '';
    return `<section class="unranked-models" aria-labelledby="unranked-title"><h3 id="unranked-title">Unranked models <span>${result.unranked.length}</span></h3><p>Missing required source data is not a low score. These models are not included in the ranking.</p><ul>${result.unranked.map(row => `<li data-unranked-key="${escape(row.key)}"><div><strong>${escape(row.name)}</strong><span>${escape(row.provider)}; ${escape(row.effort)} reasoning effort</span><p>${escape(row.reason || 'Required matching benchmark data is unavailable.')}</p></div>${detailsButton(row)}${state.variant === 'C' && state.detailOpen && state.selectedKey === row.key ? inlineDetail() : ''}</li>`).join('')}</ul></section>`;
  }

  function resultsContent() {
    return `<section id="results" class="comparison-results" role="tabpanel" aria-labelledby="view-${state.view}">${comparisonHeading()}${sourceCaption()}${scenarioNotice()}${result.notice && result.supported && result.ranked.length ? `<p class="policy-notice">${escape(result.notice)}</p>` : ''}${!result.supported ? emptyState(true) : result.ranked.length === 0 ? emptyState(false) : state.view === 'table' ? modelTable() : state.variant === 'C' ? picksShelf() : picksTable()}${state.variant === 'C' && state.detailOpen && !inlineInTable() && result.ranked.some(row => row.key === state.selectedKey) ? inlineDetail() : ''}${state.view === 'picks' && result.supported && result.ranked.length ? missingProviderDisclosure() : ''}${result.supported && result.ranked.length ? `<p class="comparison-footnote">${intelligence() ? 'Cost-based advice compares all measured efforts in the selected provider scope, even efforts outside the capability filter.' : `Ordered by ${escape(result.index)} score. Cost and value advice are unavailable without a matching task-cost basis.`} First-answer time includes thinking. Timing is explanatory only; — means unavailable.${state.variant === 'B' ? ' Output tokens per second is shown separately in Model evidence.' : ''} <button type="button" class="text-button" data-open="policy-dialog">How picks work</button></p>` : ''}${unrankedModels()}<p class="visually-hidden" role="status">${escape(result.role.label)}, ${escape(providerLabel())}, ${escape(filters[state.filter])}. ${result.ranked.length} ranked models. ${result.unranked.length} unranked models.</p></section>`;
  }

  function detailMetric(label, value, note = '') {
    return `<div><dt>${label}</dt><dd>${value}</dd>${note ? `<p>${note}</p>` : ''}</div>`;
  }

  function detailPanel(detail, showTitle = true) {
    const row = detail.row;
    const isIntelligence = intelligence();
    const replacement = detail.replacement;
    const path = Array.isArray(detail.frontierPath) ? detail.frontierPath : [];
    const explanation = detail.explanation.split(/\n\n+/);
    return `<article class="model-evidence" data-evidence-key="${escape(row.key)}">
      ${showTitle ? `<header class="evidence-heading"><h2>${escape(row.name)}</h2><p>${escape(row.provider)}; ${escape(row.effort)} reasoning effort</p></header>` : `<p class="evidence-byline">${escape(row.provider)}; ${escape(row.effort)} reasoning effort</p>`}
      <dl class="evidence-metrics">${detailMetric(`${escape(result.index)} score`, number(row.score))}${detailMetric('Capability grade', grade(row.grade))}${isIntelligence ? `${detailMetric('Benchmark task cost', cost(row.cost), 'Matching Intelligence workload, in United States dollars.')}${detailMetric('Capability per dollar', number(row.value), 'Intelligence score divided by its matching task cost.')}` : ''}</dl>
      <p class="grade-definition">Grades run from 1 to 5; 5 is highest. The ${escape(result.index)} reference includes all scored configurations across efforts in this refresh, not only the selected provider or visible rows.</p>
      ${row.reason ? `<p class="evidence-warning">${escape(row.reason)}</p>` : ''}
      <section class="evidence-section"><h3>Why this configuration</h3>${explanation.slice(0, 2).map(paragraph => `<p>${escape(paragraph)}</p>`).join('')}
      ${isIntelligence ? `<p class="frontier-explanation">${row.frontier === true ? `<strong class="recommendation-text">On the Intelligence cost frontier.</strong> No measured configuration in this advice scope improves score at equal-or-lower task cost.` : row.frontier === false ? '<strong>A cost-based replacement exists.</strong> Frontier membership is scoped to the selected providers, not a global quality label.' : 'Cost-frontier status is unavailable for this configuration.'}</p>${replacement ? `<p class="replacement"><strong>Replacement:</strong> ${escape(replacement.name)}, ${escape(replacement.effort)} effort; Intelligence score ${number(replacement.score)}, task cost ${cost(replacement.cost)}. Same-effort replacements are preferred before cross-effort choices.</p>` : ''}` : `<p class="metric-unavailable">${escape(result.index)} has no established matching benchmark task cost. Intelligence costs are not reused for value, frontier, replacement or cheaper-alternative advice.</p>`}</section>
      <section class="evidence-section"><h3>Measured reasoning efforts</h3><p>The objective selects one measured effort per model. Missing values remain unavailable.</p><div class="detail-table-scroll"><table class="detail-table"><thead><tr><th scope="col">Reasoning effort</th><th scope="col" class="numeric">${escape(result.index)} score</th><th scope="col" class="numeric">Capability grade</th>${isIntelligence ? '<th scope="col" class="numeric">Benchmark task cost</th>' : ''}</tr></thead><tbody>${detail.configurations.map(configuration => `<tr class="${configuration.key === row.key ? 'chosen-configuration' : ''}"><th scope="row">${escape(configuration.effort)}${configuration.key === row.key ? '<span class="chosen-label">Selected</span>' : ''}</th><td class="numeric">${number(configuration.score)}</td><td class="numeric">${grade(configuration.grade)}</td>${isIntelligence ? `<td class="numeric">${cost(configuration.cost)}</td>` : ''}</tr>`).join('')}</tbody></table></div></section>
      <section class="evidence-section"><h3>Independent benchmark ratings</h3><p>Scores and grades stay separate for each source and index. A missing rating is not replaced with another benchmark.</p><div class="ratings-list">${detail.ratings.map(rating => `<div class="independent-rating"><div><strong>${externalLink(rating.sourceUrl, rating.source)}</strong><span>${escape(rating.label)}</span>${rating.agent ? `<span>Agent: ${escape(rating.agent)}</span>` : ''}</div><div class="rating-value">${rating.formattedValue ? escape(rating.formattedValue) : number(rating.value)}${grade(rating.grade)}</div>${rating.synthetic ? '<p class="rating-note">Synthesized preview data, not a live benchmark result.</p>' : ''}${rating.sourceUrl ? `<p class="source-address">${externalLink(rating.sourceUrl, sourceAddress(rating.sourceUrl))}</p>` : ''}</div>`).join('') || '<p>No independent source ratings are available at this effort.</p>'}</div></section>
      <section class="evidence-section"><h3>Published timing</h3><dl class="timing-metrics">${detailMetric('Time to first answer token', finite(row.firstAnswer) ? `${number(row.firstAnswer)} seconds` : number(null), 'Published median, including thinking.')}${detailMetric('Output tokens per second', number(row.outputSpeed), 'Answer-token throughput, not latency.')}${finite(row.firstToken) ? detailMetric('Time to first token', `${number(row.firstToken)} seconds`, 'A separate measure; not a substitute for first-answer time.') : ''}${finite(row.response500) ? detailMetric('Estimated response time for 500 answer tokens', `${number(row.response500)} seconds`, 'Published estimate, not whole-agent task duration.') : ''}</dl><p>— means unavailable. No timing is reconstructed, and none affects ranking, eligibility or ties.</p></section>
      ${isIntelligence ? `<section class="evidence-section"><h3>Cheaper near-equal alternatives</h3><p>Up to three configurations in ${escape(providerLabel())}, at lower matching task cost and no more than 5 Intelligence points below this score, ordered by cost. These are not provider runner-up picks.</p>${detail.alternatives.length ? `<div class="detail-table-scroll"><table class="detail-table alternatives-table"><thead><tr><th scope="col">Model / reasoning effort</th><th scope="col" class="numeric">Intelligence score</th><th scope="col" class="numeric">Benchmark task cost</th></tr></thead><tbody>${detail.alternatives.map(alternative => `<tr><th scope="row">${escape(alternative.name)}<span>${escape(alternative.effort)} effort</span></th><td class="numeric">${number(alternative.score)}</td><td class="numeric">${cost(alternative.cost)}</td></tr>`).join('')}</tbody></table></div>` : '<p class="no-alternatives">No cheaper qualifying alternative in this comparison scope.</p>'}${path.length ? `<details class="frontier-path"><summary>Measured Intelligence cost-frontier path</summary><p>All included efforts remain in this advisory comparison, even when the display filter or price floor excludes them from the main rows.</p><div class="detail-table-scroll"><table class="detail-table"><thead><tr><th scope="col">Model / effort</th><th scope="col" class="numeric">Intelligence score</th><th scope="col" class="numeric">Task cost</th></tr></thead><tbody>${path.map(point => `<tr><th scope="row">${escape(point.name)}<span>${escape(point.effort)} effort</span></th><td class="numeric">${number(point.score)}</td><td class="numeric">${cost(point.cost)}</td></tr>`).join('')}</tbody></table></div></details>` : ''}</section>` : ''}
      <section class="evidence-section secondary-data"><h3>Additional catalog data</h3><dl>${detailMetric('Vision input', row.vision === true ? 'Listed in preview catalog' : row.vision === false ? 'Not listed as supported' : number(null))}${detail.metadata ? `${detailMetric('Context window', finite(detail.metadata.contextLength) ? `${number(detail.metadata.contextLength, 0)} tokens` : number(null))}${detailMetric('Input modalities', Array.isArray(detail.metadata.inputModalities) ? escape(detail.metadata.inputModalities.join(', ')) : number(null))}${detailMetric('Output modalities', Array.isArray(detail.metadata.outputModalities) ? escape(detail.metadata.outputModalities.join(', ')) : number(null))}` : ''}${detailMetric('OpenRouter 30-day token share', finite(row.tokenShare) ? `${number(row.tokenShare)}%` : number(null), 'Unavailable in the recorded fixture. Display-only; never a ranking, eligibility, tie-break or grade input.')}</dl>${detail.metadata?.note ? `<p>${escape(detail.metadata.note)}</p>` : ''}</section>
      ${detail.pricing?.length ? `<details class="secondary-evidence"><summary>Token list prices, separate from task cost</summary><p>These prices are not the benchmark task-cost basis and do not affect selection, value, eligibility or ties.</p><dl class="list-prices">${detail.pricing.map(price => detailMetric(escape(price.label), cost(price.value), escape(price.unit))).join('')}</dl></details>` : ''}
      ${explanation.length > 2 ? `<details class="secondary-evidence"><summary>Full selection and comparison evidence</summary>${explanation.slice(2).map(paragraph => `<p>${escape(paragraph)}</p>`).join('')}</details>` : ''}
      ${detail.sourceUrl ? `<p class="detail-source">Configuration source: ${externalLink(detail.sourceUrl, sourceAddress(detail.sourceUrl))}</p>` : ''}
    </article>`;
  }

  function inspector() {
    return `<aside class="inspector-pane" aria-label="Selected model evidence"><details id="inspector-disclosure" ${matchMedia('(min-width: 1180px)').matches || state.detailOpen ? 'open' : ''}><summary id="inspector-summary">Model evidence${selectedDetail ? `<span>${escape(selectedDetail.row.name)}</span>` : ''}</summary>${selectedDetail ? detailPanel(selectedDetail) : '<div class="inspector-empty"><h2>Inspect a model</h2><p>Open model Details to see selected effort, independent source ratings, timing and applicable comparisons.</p></div>'}</details></aside>`;
  }

  function VariantA() {
    return `<div class="focus-desk"><aside class="role-rail-shell"><h2 class="control-heading">Choose a role</h2>${roleNavigation('role-rail')}<p class="role-purpose">${escape(result.role.description)}</p></aside><main id="main-content" tabindex="-1">${roleHeader()}${objectiveControls(false, true)}${providerControls(false, false)}${tabs()}${resultsContent()}</main></div>`;
  }

  function VariantB() {
    return `<main id="main-content" class="comparison-canvas" tabindex="-1">${roleNavigation('role-top')}${roleHeader()}<div class="canvas-controls">${objectiveControls(false, true)}${providerControls(false, false)}</div>${tabs()}<div class="canvas-evidence-layout">${resultsContent()}${inspector()}</div></main>`;
  }

  function VariantC() {
    return `<div class="provider-lens"><aside class="provider-rail">${providerControls(true)}</aside><main id="main-content" tabindex="-1"><div class="lens-heading"><h1>${state.provider === 'all' ? 'Models across providers' : `Models from ${escape(state.provider)}`}</h1>${objectiveControls(true)}<p class="lens-purpose">${escape(result.role.description)} <span>${escape(result.index)} index</span></p></div>${tabs()}${resultsContent()}</main></div>`;
  }

  function dateLabel() {
    if (!ratings.snapshot.fetchedAt) return 'Fetch date unavailable';
    const date = new Date(ratings.snapshot.fetchedAt);
    return Number.isNaN(date.getTime()) ? `Recorded fetch date: ${escape(ratings.snapshot.fetchedAt)}` : `Fetched ${new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(date)}`;
  }

  function provenance() {
    return `<footer class="provenance"><p>${externalLink(ratings.snapshot.sourceUrl, 'Recorded source endpoint')} <button type="button" class="text-button" data-open="policy-dialog">Sources, fixture provenance and metric definitions</button></p></footer>`;
  }

  function supportDialogs() {
    policyDialog.innerHTML = `<div class="dialog-heading"><h2 id="policy-dialog-title">How picks work</h2><button type="button" data-close="policy-dialog">Close</button></div><div class="support-content"><p>These are published-score proxies, not verified performance on your tasks. The selected role chooses a benchmark index and a default objective; it does not fix a reasoning effort.</p><details open><summary>Role defaults and objective order</summary><div class="detail-table-scroll"><table class="detail-table"><thead><tr><th scope="col">Role</th><th scope="col">Index</th><th scope="col">Default objective</th></tr></thead><tbody>${ratings.roles.map(role => `<tr><th scope="row">${escape(role.label)}</th><td>${escape(role.index)}</td><td>${escape(ratings.objectives[role.objective])}</td></tr>`).join('')}</tbody></table></div><ul><li><strong>Highest capability:</strong> highest selected-index score. Intelligence ties use lower matching task cost; Coding and Agentic do not use cost.</li><li><strong>Best value:</strong> highest Intelligence score divided by matching benchmark task cost, then higher score, then lower cost.</li><li><strong>Lowest qualifying price:</strong> lowest matching Intelligence task cost among configurations at capability grade 2 or higher, then higher score.</li></ul><p>The same order selects a model's effort and orders models. Remaining exact ties use lower effort, then canonical model identity. Timing never changes the order.</p><p>Coding and Agentic support Highest capability only. Unsupported overrides remain selected and show an unavailable state. Coding is not a measured review-accuracy score; Agentic is not proof of multi-agent coordination quality.</p></details><details><summary>Eligibility, grades and matching costs</summary><p>Intelligence requires a finite score and a finite, non-negative matching Intelligence task cost at the measured effort. Best value also requires positive cost. A zero cost does not provide a finite ratio. Token list prices and other benchmark-run costs are not substitutes.</p><p>Coding and Agentic require their own selected-index score only. No matching task-cost basis is established for either; Intelligence cost is not reused.</p><p>Capability grades use distinct score values, from 1 to 5. The reference includes all scored configurations across efforts for the selected index in the refresh, before provider selection, display filtering or the price floor. A provider selection never re-bins grades. Other sources retain independent grades.</p></details><details><summary>Provider picks, frontier and cheaper alternatives</summary><p>Provider picks take at most two distinct models per creator in direct objective order. A runner-up is not a second effort of the primary, not a specially selected cheaper alternative, and not necessarily on the cost frontier.</p><p>Only Intelligence supports cost-frontier advice. A configuration is dominated when another configuration in the selected provider scope has at least as much Intelligence at no greater matching cost, with one strict improvement. Replacements prefer the same effort before cross-effort fallback.</p><p>The advisory universe includes all measured efforts for the included creators. Neither the display filter nor the Lowest qualifying price floor removes advisory comparison points. All providers restores global comparisons.</p><p>Detail alternatives are the three cheapest configurations at lower matching cost and no more than 5 Intelligence points below the chosen score. No missing row, runner-up or creator is fabricated.</p></details><details><summary>Timing and secondary data</summary><dl class="definition-list"><div><dt>Time to first answer token</dt><dd>Published median in seconds, including thinking. This is the main latency measure.</dd></div><div><dt>Output tokens per second</dt><dd>Answer-token throughput, shown separately from latency.</dd></div><div><dt>Time to first token</dt><dd>A distinct optional published metric; never used to fill missing first-answer timing.</dd></div><div><dt>Estimated response time for 500 answer tokens</dt><dd>Shown only when published; never reconstructed. Not whole-agent task duration.</dd></div><div><dt>OpenRouter 30-day token share</dt><dd>Currently unavailable in this fixture. Display-only; never used in scores, eligibility, grades, ordering or ties.</dd></div></dl><p>— always means unavailable, not zero. Missing timing does not exclude a model.</p></details><details><summary>Sources and preview provenance</summary><p><strong>${escape(ratings.snapshot.label)}</strong></p><p>${escape(ratings.snapshot.note)}</p><p>${dateLabel()}. Fixture models are not live market recommendations. Terminal-Bench submissions and OpenRouter catalog rows are synthesized preview evidence; empty provider shortcuts describe fixture coverage only.</p><p class="source-address">${externalLink(ratings.snapshot.sourceUrl, ratings.snapshot.sourceUrl)}</p><p>Independent benchmark source links are attached to each rating in model Details. Those ratings are never blended.</p></details></div>`;
    previewDialog.innerHTML = `<div class="dialog-heading"><h2 id="preview-dialog-title">Preview states</h2><button type="button" data-close="preview-dialog">Close</button></div><div class="support-content"><p>Explore fixture limits without changing ranking rules. This selection is temporary and stays in memory only. Explicitly synthetic cases are labelled here and in the comparison.</p>${field('scenario', 'Fixture scenario', ratings.scenarios.map(scenario => `<option value="${escape(scenario.id)}" ${state.scenario === scenario.id ? 'selected' : ''}>${escape(scenario.label)}</option>`).join(''))}<p class="scenario-description">${escape(ratings.scenarios.find(scenario => scenario.id === state.scenario)?.description || '')}</p><details><summary>Reach states with the recorded fixture</summary><ul><li>Choose Google, DeepSeek or xAI for an empty provider result. This fixture does not measure real provider coverage.</li><li>Choose Kimi and Provider picks for one distinct model and no fabricated runner-up.</li><li>Open a source-only model under Unranked models for explicit missing-data reasons.</li><li>Choose Coder or Coordinator, then Best value, for an unavailable objective without a silent fallback.</li><li>Change the capability filter to explore constrained results. Recoveries change only their named constraint.</li></ul></details></div>`;
  }

  function renderSwitcher() {
    switcher.hidden = !localPreview;
    if (!localPreview) return;
    switcher.innerHTML = `<button type="button" id="variant-previous" data-action="previous-variant" aria-label="Previous layout variant">←</button><span id="variant-label"><strong>${state.variant}</strong> ${variants[state.variant]}<small>Visual prototype</small></span><button type="button" id="variant-next" data-action="next-variant" aria-label="Next layout variant">→</button>`;
  }

  function render(focusId) {
    result = ratings.evaluate(policyState());
    if (state.variant === 'B' && !state.selectedKey && result.ranked.length) state.selectedKey = result.ranked[0].key;
    selectedDetail = state.selectedKey ? ratings.details(state.selectedKey, policyState()) : null;
    app.dataset.variant = state.variant;
    document.title = `${result.role.label} model advice · LLM Ratings preview`;
    app.innerHTML = `<header class="site-header"><a class="brand" href="#main-content" aria-label="LLM Ratings model advice">LLM Ratings<span>Model advice</span></a><div class="support-actions"><button type="button" id="how-picks-work" class="text-button" data-open="policy-dialog">How picks work</button><button type="button" id="preview-states" class="text-button" data-open="preview-dialog">Preview states</button></div></header>${({ A: VariantA, B: VariantB, C: VariantC })[state.variant]()}${provenance()}`;
    supportDialogs();
    renderSwitcher();
    if (state.variant === 'A' && state.detailOpen && selectedDetail) {
      modelDialog.innerHTML = `<div class="dialog-heading"><h2 id="model-dialog-title">${escape(selectedDetail.row.name)}</h2><button type="button" data-close="model-dialog">Close details</button></div><div class="drawer-content">${detailPanel(selectedDetail, false)}</div>`;
      if (!modelDialog.open) modelDialog.showModal();
    } else if (modelDialog.open) modelDialog.close();
    if (focusId) document.getElementById(focusId)?.focus({ preventScroll: true });
  }

  function changeSelection(name, value, focusId) {
    if (name === 'role') {
      const role = ratings.roles.find(item => item.id === value);
      if (!role) return;
      state.role = role.id;
      state.objective = role.objective;
    } else state[name] = value;
    state.selectedKey = null;
    state.detailOpen = false;
    render(focusId);
  }

  function setVariant(direction, focusId) {
    const keys = Object.keys(variants);
    state.variant = keys[(keys.indexOf(state.variant) + direction + keys.length) % keys.length];
    state.detailOpen = false;
    const url = new URL(location.href);
    url.searchParams.set('variant', state.variant);
    history.replaceState(null, '', url);
    render(focusId);
    console.info('Provider selection visual prototype', {
      ...state, roleLabel: result.role.label, index: result.index,
      objectiveLabel: ratings.objectives[state.objective], comparisonScope: result.scope,
      supported: result.supported, rankedModels: result.ranked.map(row => ({ key: row.key, name: row.name, effort: row.effort })),
      unrankedModels: result.unranked.map(row => ({ key: row.key, name: row.name, reason: row.reason }))
    });
  }

  document.addEventListener('click', event => {
    const button = event.target.closest('button');
    if (!button) return;
    if (button.dataset.open) { document.getElementById(button.dataset.open).showModal(); return; }
    if (button.dataset.close) { document.getElementById(button.dataset.close).close(); return; }
    if (button.dataset.role) { changeSelection('role', button.dataset.role, button.id); return; }
    if (button.dataset.provider) { changeSelection('provider', button.dataset.provider, button.id); return; }
    if (button.dataset.view) { changeSelection('view', button.dataset.view, button.id); return; }
    if (button.dataset.detailKey) {
      const alreadyExpanded = state.variant === 'C' && state.detailOpen && state.selectedKey === button.dataset.detailKey;
      state.selectedKey = alreadyExpanded ? null : button.dataset.detailKey;
      state.detailOpen = Boolean(state.selectedKey);
      detailTriggerId = button.id;
      render(state.variant === 'A' ? undefined : button.id);
      if (state.variant === 'B' && !matchMedia('(min-width: 1180px)').matches) {
        document.getElementById('inspector-summary')?.focus();
        document.querySelector('.inspector-pane')?.scrollIntoView({ block: 'nearest' });
      }
      if (state.variant === 'C' && state.selectedKey) document.querySelector('.inline-evidence')?.scrollIntoView({ block: 'nearest' });
      return;
    }
    const action = button.dataset.action;
    if (action === 'previous-variant' || action === 'next-variant') setVariant(action === 'previous-variant' ? -1 : 1, button.id);
    if (action === 'all-providers') changeSelection('provider', 'all');
    if (action === 'clear-filter') changeSelection('filter', 'all');
    if (action === 'supported-objective') changeSelection('objective', 'cap');
    if (action === 'recorded') changeSelection('scenario', 'recorded');
    if (action === 'close-detail') { state.selectedKey = null; state.detailOpen = false; render(detailTriggerId); }
  });

  document.addEventListener('change', event => {
    const name = event.target.dataset.state;
    if (name) changeSelection(name, event.target.value, event.target.id);
  });

  document.addEventListener('keydown', event => {
    if (event.target.matches('[role="tab"]') && ['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
      event.preventDefault();
      const view = event.key === 'Home' ? 'table' : event.key === 'End' ? 'picks' : state.view === 'table' ? 'picks' : 'table';
      changeSelection('view', view, `view-${view}`);
      return;
    }
    if (!localPreview || !['ArrowLeft', 'ArrowRight'].includes(event.key) || event.altKey || event.ctrlKey || event.metaKey
      || event.target.closest('input, select, textarea, button, dialog, [contenteditable]:not([contenteditable="false"])')) return;
    event.preventDefault();
    setVariant(event.key === 'ArrowLeft' ? -1 : 1);
  });

  modelDialog.addEventListener('close', () => { state.detailOpen = false; document.getElementById(detailTriggerId)?.focus({ preventScroll: true }); });
  window.addEventListener('popstate', () => {
    const variant = new URL(location.href).searchParams.get('variant');
    if (Object.hasOwn(variants, variant)) { state.variant = variant; state.detailOpen = false; render(); }
  });
  // Read-only browser inspection; no storage, network request, or product mutation.
  window.RatingsPreview = { getState: () => ({ ...state }) };
  render();
})();
