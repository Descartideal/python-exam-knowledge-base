// Run the production rendering functions against a controlled scroll viewport.
// Browser verification also covers real layout changes and delayed image loads.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const names = new Set(['message', 'scrollDown', 'preserveView', 'sources', 'files',
  'trace', 'setBusy', 'pollJob', 'approval']);
const functions = html.split('\n').filter(line => {
  const match = line.match(/^(?:async )?function (\w+)\(/);
  return match && names.has(match[1]);
}).join('\n');
let height = 5000, top = 320;
const viewport = {
  clientHeight: 600,
  get scrollHeight() { return height; },
  get scrollTop() { return top; },
  set scrollTop(value) { top = Math.max(0, Math.min(value, height - this.clientHeight)); }
};
class Element {
  constructor() {
    this.children = [];
    this.selectors = new Map();
    this.classList = {add() {}, remove() {}, toggle() {}};
  }
  appendChild(child) { this.children.push(child); height += 24; }
  append(...children) { children.forEach(child => this.appendChild(child)); }
  replaceChildren(...children) { this.children = children; height += 12; }
  querySelector(selector) {
    if (!this.selectors.has(selector)) this.selectors.set(selector, new Element());
    return this.selectors.get(selector);
  }
  querySelectorAll() { return []; }
  remove() { height -= 12; }
}
const elements = new Map([['scroll', viewport]]);
const sandbox = {
  $: id => {
    if (!elements.has(id)) elements.set(id, new Element());
    return elements.get(id);
  },
  document: {createElement: () => new Element()},
  markdown: text => String(text),
  history: [], active: null, current: null, polling: false,
  save() {}, notify() {}, api: async () => ({ok: true}),
  setTimeout() {},
  fetch: async () => ({json: async () => sandbox.response})
};
vm.createContext(sandbox);
vm.runInContext(functions, sandbox);
async function update(response) {
  sandbox.response = {cursor: 1, sources: [], files: [], metrics: {}, ...response};
  await sandbox.pollJob();
  assert.equal(top, 320, 'Rendering must preserve the reader position');
}
(async () => {
  for (let i = 0; i < 5; i++) sandbox.message('assistant', 'Saved conversation ' + i);
  assert.equal(top, 320, 'Restoring and adding messages must not jump to the bottom');
  sandbox.current = sandbox.message('assistant', '');
  sandbox.active = {id: 'test', cursor: 0, text: ''};
  await update({status: 'running', events: [
    {kind: 'token', text: 'A streamed reply. '.repeat(300)},
    {kind: 'tool_start', name: 'read_file', arguments: {path: 'test.csv'}},
    {kind: 'tool_result', name: 'read_file', result: {output: 'Test data'}}
  ]});
  await update({status: 'waiting', events: [
    {kind: 'approval', name: 'run_python', arguments: {path: 'test.py'}}
  ]});
  await update({status: 'done', events: [], answer: 'Completed.', files: ['result.png']});
  assert.equal(sandbox.active, null);
  sandbox.scrollDown();
  assert.equal(top, height - viewport.clientHeight, 'Explicit navigation must reach the latest result');
  console.log('Scroll regression checks passed: history, streaming, tools, approval, completion, manual navigation.');
})().catch(error => { console.error(error); process.exitCode = 1; });
