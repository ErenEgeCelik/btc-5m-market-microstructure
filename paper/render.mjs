/** Render the working manuscript to standalone print HTML. No network requests. */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const paper = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
function option(name, fallback) {
  const i = args.indexOf(name);
  return i < 0 ? fallback : args[i + 1];
}
const input = path.resolve(option('--input', path.join(paper, 'manuscript.md')));
const output = path.resolve(option('--output', path.join(paper, 'manuscript.html')));
const modulesRoot = path.resolve(option('--modules-root', paper));
const require = createRequire(path.join(modulesRoot, 'package.json'));
async function module(name) { return import(pathToFileURL(require.resolve(name)).href); }
const { default: React } = await module('react');
const { renderToStaticMarkup } = await module('react-dom/server');
const { default: Markdown } = await module('react-markdown');
const { default: gfm } = await module('remark-gfm');
const { default: math } = await module('remark-math');
const { default: katex } = await module('rehype-katex');
const cssPath = require.resolve('katex/dist/katex.min.css');
const mathCss = fs.readFileSync(cssPath, 'utf8').replace(/url\(([^)]+)\)/g,
  (_, relative) => `url("${pathToFileURL(path.resolve(path.dirname(cssPath), relative.replace(/["']/g, ''))).href}")`);
const source = fs.readFileSync(input, 'utf8');
const evidenceRevision = '6db010205b3aa3b8b4ee1d5715e06c47de8023b7';
const root = path.resolve(paper, '..');
const components = {
  a({ href, children }) {
    if (href && !/^(https?:|mailto:|#)/.test(href)) {
      const target = path.resolve(path.dirname(input), href.split('#')[0]);
      const rel = path.relative(root, target).split(path.sep).join('/');
      // Technical references pin the evidence release; paper references follow its own revision.
      const revision = rel.startsWith('paper/') ? 'main' : evidenceRevision;
      href = `https://github.com/ErenEgeCelik/btc-5m-market-microstructure/blob/${revision}/${rel}`;
    }
    return React.createElement('a', { href }, children);
  },
  img({ src, alt }) {
    if (/^https?:/i.test(src || '')) throw new Error('Paper figures must be local.');
    const target = path.resolve(path.dirname(input), src);
    if (!fs.existsSync(target)) throw new Error(`Missing figure: ${src}`);
    return React.createElement('img', { src: pathToFileURL(target).href, alt });
  },
};
const body = renderToStaticMarkup(React.createElement(Markdown,
  { remarkPlugins: [gfm, math], rehypePlugins: [[katex, { strict: 'error', throwOnError: true }]], components }, source));
if (body.includes('katex-error')) {
  const errors = [...body.matchAll(/<span class="katex-error"[^>]*title="([^"]*)"[^>]*>(.*?)<\/span>/gs)]
    .map(match => ({ error:match[1], equation:match[2] }));
  throw new Error('Unrendered equations: ' + JSON.stringify(errors));
}
const style = `
@page { size:A4; margin:19mm 19mm 20mm; }
* { box-sizing:border-box; }
html { color:#17202a; background:white; }
body { font:10.4pt/1.43 Georgia,'Times New Roman',serif; margin:0; }
main { max-width:172mm; margin:auto; }
h1 { font-size:23pt; line-height:1.18; text-align:center; margin:0 0 16pt; }
h1 + p { text-align:center; font-size:10.6pt; line-height:1.65; margin-bottom:21pt; }
h2 { font-size:14pt; line-height:1.25; margin:21pt 0 8pt; break-after:avoid; }
h3 { font-size:11.3pt; margin:14pt 0 6pt; break-after:avoid; }
p { margin:6pt 0 8pt; orphans:3; widows:3; }
a { color:#203f59; text-decoration:none; overflow-wrap:anywhere; }
table { width:100%; border-collapse:collapse; font-size:8.8pt; line-height:1.33; margin:10pt 0 13pt; break-inside:avoid; }
thead { display:table-header-group; }
th { text-align:left; border-top:1.2pt solid #34495e; border-bottom:.7pt solid #778899; padding:6pt 5pt; }
td { border-bottom:.35pt solid #d7dce1; padding:5pt; vertical-align:top; }
tr { break-inside:avoid; }
code { font:8.4pt/1.4 Consolas,'Courier New',monospace; overflow-wrap:anywhere; }
pre { background:#f4f6f7; border:1px solid #e0e5e8; padding:9pt; white-space:pre-wrap; break-inside:avoid; }
img { width:100%; height:auto; display:block; margin:14pt auto 5pt; }
p:has(> img) { break-inside:avoid; break-after:avoid; }
p:has(> em:only-child) { font-size:9pt; line-height:1.35; margin:5pt 0 13pt; }
p:has(> strong:only-child) { font-size:9.2pt; break-after:avoid; margin-top:11pt; }
p:has(+ .katex-display) { break-after:avoid; }
.katex { font-size:1.03em; }
.katex-display { font-size:10pt; margin:12pt 0; overflow:visible; break-inside:avoid; }
.katex-display .tag { font-size:.92em; }
li { margin:4pt 0; }
ul { padding-left:17pt; break-inside:avoid; }
@media screen { body { padding:30px 24px; } }
`;
fs.mkdirSync(path.dirname(output), { recursive:true });
fs.writeFileSync(output, `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Pricing and Market Making in BTC Five-Minute Prediction Markets</title><style>${mathCss}\n${style}</style></head><body><main>${body}</main></body></html>`);
console.log(JSON.stringify({ html:output, displayEquations:(body.match(/class="katex-display"/g)||[]).length,
  images:(body.match(/<img /g)||[]).length }));
