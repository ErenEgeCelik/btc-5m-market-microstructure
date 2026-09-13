"""Build the paper PDF from its Markdown source using local math assets.

Adapted from the publication site's existing Playwright print workflow.
Requires the paper's npm dependencies and Python Playwright with Chromium.
"""
import argparse
import json
from pathlib import Path
import subprocess

from playwright.sync_api import sync_playwright

PAPER = Path(__file__).resolve().parent


def build(output, modules_root=None, browser_executable=None):
    html = output.with_suffix('.html')
    command = ['node', str(PAPER / 'render.mjs'), '--output', str(html)]
    if modules_root:
        command += ['--modules-root', str(modules_root)]
    subprocess.run(command, check=True)
    report = {'pdf': str(output), 'html': str(html), 'page_errors': [], 'failed_resources': []}
    with sync_playwright() as runtime:
        options = {'headless': True, 'args': ['--allow-file-access-from-files']}
        if browser_executable:
            options['executable_path'] = str(browser_executable)
        browser = runtime.chromium.launch(**options)
        page = browser.new_page(viewport={'width': 900, 'height': 1200})
        page.on('pageerror', lambda error: report['page_errors'].append(str(error)))
        page.on('requestfailed', lambda request: report['failed_resources'].append(request.url))
        page.goto(html.as_uri(), wait_until='networkidle')
        page.evaluate('document.fonts.ready')
        page.emulate_media(media='print')
        report['equation_errors'] = page.locator('.katex-error').count()
        report['broken_images'] = page.locator('img').evaluate_all('(xs)=>xs.filter(x=>!x.complete||!x.naturalWidth).map(x=>x.src)')
        report['horizontal_overflow'] = page.evaluate('document.documentElement.scrollWidth > innerWidth')
        report['equation_count'] = page.locator('.katex-display').count()
        if any(report[key] for key in ['page_errors', 'failed_resources', 'equation_errors', 'broken_images', 'horizontal_overflow']):
            raise RuntimeError(json.dumps(report))
        page.pdf(path=str(output), format='A4', print_background=True, display_header_footer=True,
                 header_template='<span></span>',
                 footer_template='<div style="font-size:8px;color:#5c6570;width:100%;text-align:center">Eren Ege Celik - Working paper v0.2 - <span class="pageNumber"></span></div>',
                 prefer_css_page_size=True,
                 margin={'top':'19mm', 'bottom':'20mm', 'left':'19mm', 'right':'19mm'})
        browser.close()
    output.with_suffix('.build.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=PAPER / 'crypto-working-paper.pdf')
    parser.add_argument('--modules-root', type=Path, help='Use an existing compatible npm dependency directory.')
    parser.add_argument('--browser-executable', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    build(output, args.modules_root, args.browser_executable)
