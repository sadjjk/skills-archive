#!/usr/bin/env node
/**
 * 逐页渲染 + 质量检查：截图每一页、拼总览图、输出问题报告。
 *
 * 用法：node check_deck.mjs out/deck.html [--out out/check] [--strict]
 * 依赖：playwright（npm i -g playwright && npx playwright install chromium）
 *
 * 检查项（对应 references/quality-check.md）：
 *   overflow   文本实际渲染高度/宽度超出文本框 → 断行或字号需要调整
 *   bounds     文本框超出画布
 *   safe-area  文本进入安全边距（页眉页脚这类 name 以 header/footer/page/top/bottom 开头的除外）
 *   overlap    两个文本框实际内容重叠
 *   orphan     中文段落最后一行只剩 1 个字（孤字）
 *   font       首选字体缺失、回退到备选字体（提示，不算错误）
 */
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

// 优先用本地依赖，找不到时回退到全局 npm 目录，免得每个项目都装一遍 playwright
function loadPlaywright() {
  const require = createRequire(import.meta.url);
  try { return require('playwright'); } catch {}
  const globalRoot = execSync('npm root -g').toString().trim();
  return require(path.join(globalRoot, 'playwright'));
}

const args = process.argv.slice(2);
const htmlPath = args.find(a => !a.startsWith('--'));
if (!htmlPath) { console.error('用法：node check_deck.mjs deck.html [--out dir] [--strict]'); process.exit(2); }
const outIdx = args.indexOf('--out');
const outDir = path.resolve(outIdx >= 0 ? args[outIdx + 1] : path.join(path.dirname(htmlPath), 'check', path.basename(htmlPath, '.html')));
const strict = args.includes('--strict');
fs.mkdirSync(outDir, { recursive: true });

const { chromium } = loadPlaywright();
const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.resolve(htmlPath)).href + '?mode=print');
await page.evaluate(() => document.fonts.ready);
await page.waitForLoadState('networkidle');

const { meta, report } = await page.evaluate(() => {
  const meta = window.DECK_META;
  const EXEMPT = /^(header|footer|page|top|bottom|section|chrome|foot|index)/i;
  const issues = [];
  const fontCache = new Map();
  // 用 canvas 测宽判断字体是否真实可用：与 generic 回退字体宽度一致即视为缺失
  const fontAvailable = (family) => {
    if (['serif', 'sans-serif', 'monospace', 'cursive'].includes(family)) return true;
    if (fontCache.has(family)) return fontCache.get(family);
    const c = document.createElement('canvas').getContext('2d');
    const probe = '永和九年 Quality 0123';
    const ok = ['monospace', 'serif', 'sans-serif'].some(base => {
      c.font = `40px ${base}`; const w0 = c.measureText(probe).width;
      c.font = `40px "${family}", ${base}`; return c.measureText(probe).width !== w0;
    });
    fontCache.set(family, ok); return ok;
  };
  const slides = [...document.querySelectorAll('.slide')];
  slides.forEach((slide, si) => {
    const page = si + 1;
    const sr = slide.getBoundingClientRect();
    const boxes = [];
    slide.querySelectorAll('.t').forEach(el => {
      const name = el.dataset.name || '(unnamed)';
      const r = el.getBoundingClientRect();
      const box = { x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height };
      // 用 Range 量出文字真实占位（不受 div 固定宽高影响）
      const range = document.createRange(); range.selectNodeContents(el);
      const rects = [...range.getClientRects()];
      const cs = getComputedStyle(el);
      // 旋转文字：getClientRects 返回的是旋转后的包围盒，行数/孤字/重叠判断不再成立，只检查框内是否折行与越界
      const rotated = parseFloat(el.dataset.rotate || '0') !== 0;
      // bleed：刻意出血的装饰大字（如瑞士风超大数字），跳过越界与安全区检查
      const bleed = el.dataset.bleed === '1';
      const lineH = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.25;
      // 内容区按行盒高度收窄（Range 矩形含字体 ascent/descent，比行高大，直接用会误报重叠）
      const vis = rects.map(q => { const c = (q.top + q.bottom) / 2, hh = Math.min(q.height, lineH) / 2; return { left: q.left, right: q.right, top: c - hh, bottom: c + hh }; });
      const content = vis.length ? {
        x: Math.min(...vis.map(q => q.left)) - sr.left, y: Math.min(...vis.map(q => q.top)) - sr.top,
        r: Math.max(...vis.map(q => q.right)) - sr.left, b: Math.max(...vis.map(q => q.bottom)) - sr.top,
      } : null;
      const tol = 2;
      // 溢出用「实际行数 × 行高」与框高比较，和 PowerPoint 的排版口径一致
      const lineCount = rotated ? Math.round(el.scrollHeight / lineH) : new Set(rects.map(q => Math.round(q.top))).size;
      const needH = lineCount * lineH;
      const boxH = rotated ? el.offsetHeight : box.h;
      if (needH > boxH + tol)
        issues.push({ page, level: 'error', type: 'overflow', name, msg: `${lineCount} 行需要 ${Math.round(needH)}px，框高只有 ${Math.round(box.h)}px：调大 h、减小字号或改断行` });
      if (el.scrollWidth > el.clientWidth + tol)
        issues.push({ page, level: 'error', type: 'overflow', name, msg: '单词/长串横向溢出，手动加换行' });
      if (!bleed && (box.x < -tol || box.y < -tol || box.x + box.w > meta.width + tol || box.y + box.h > meta.height + tol))
        issues.push({ page, level: 'error', type: 'bounds', name, msg: '文本框超出画布' });
      const m = meta.safe_margin;
      if (content && !bleed && !EXEMPT.test(name) && (content.x < m - tol || content.y < m - tol || content.r > meta.width - m + tol || content.b > meta.height - m + tol))
        issues.push({ page, level: 'warn', type: 'safe-area', name, msg: `文字进入 ${m}px 安全边距` });
      // 孤字：中文最后一行只剩 1 个字符（标点不计）
      const lines = new Map();
      for (const q of rects) { const k = Math.round(q.top); lines.set(k, (lines.get(k) || 0) + q.width); }
      const text = el.textContent.trim();
      if (!rotated && lines.size >= 2 && /[\u4e00-\u9fff]/.test(text) && !text.includes('\n')) {
        const last = [...lines.entries()].sort((a, b) => a[0] - b[0]).at(-1)[1];
        const fs = parseFloat(cs.fontSize);
        if (last < fs * 1.6) issues.push({ page, level: 'warn', type: 'orphan', name, msg: '末行只剩一个字，手动断行或微调宽度' });
      }
      const fams = cs.fontFamily.split(',').map(s => s.trim().replace(/^["']|["']$/g, ''));
      const used = fams.find(fontAvailable);
      if (used && used !== fams[0]) issues.push({ page, level: 'info', type: 'font', name, msg: `「${fams[0]}」未安装，回退为「${used}」` });
      if (content && !rotated && !bleed) boxes.push({ name, ...content });
    });
    for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j];
      const ox = Math.min(a.r, b.r) - Math.max(a.x, b.x), oy = Math.min(a.b, b.b) - Math.max(a.y, b.y);
      if (ox > 3 && oy > 3) issues.push({ page, level: 'warn', type: 'overlap', name: `${a.name} × ${b.name}`, msg: `文字重叠 ${Math.round(ox)}×${Math.round(oy)}px` });
    }
  });
  return { meta, report: { pages: slides.length, issues } };
});

// 逐页截图
const slideEls = await page.$$('.slide');
const shots = [];
for (let i = 0; i < slideEls.length; i++) {
  const f = path.join(outDir, `slide-${String(i + 1).padStart(2, '0')}.png`);
  await slideEls[i].screenshot({ path: f });
  shots.push(f);
}

// 总览图：4 列缩略图，带页码，用于整套节奏检查
const cols = 4, tw = 400, th = Math.round(tw * meta.height / meta.width), gap = 16;
const rows = Math.ceil(shots.length / cols);
const sheet = await browser.newPage({ viewport: { width: cols * tw + (cols + 1) * gap, height: rows * (th + 26) + (rows + 1) * gap } });
const cells = shots.map((f, i) => `<figure><img src="${path.basename(f)}"><figcaption>${String(i + 1).padStart(2, '0')}</figcaption></figure>`).join('');
// 写成同目录的临时 HTML 再 goto：setContent 的页面是 about:blank，Chromium 会拦截其中的 file:// 图片，导致总览空白
const sheetHtml = path.join(outDir, '.overview.html');
fs.writeFileSync(sheetHtml, `<!DOCTYPE html><meta charset="utf-8"><style>body{margin:0;background:#1b1b1b;display:grid;grid-template-columns:repeat(${cols},${tw}px);gap:${gap}px;padding:${gap}px}
figure{margin:0}img{width:${tw}px;height:${th}px;display:block}figcaption{color:#aaa;font:12px Menlo;padding-top:6px}</style>${cells}`);
await sheet.goto(pathToFileURL(sheetHtml).href);
await sheet.waitForLoadState('networkidle');
const overview = path.join(outDir, 'overview.png');
await sheet.screenshot({ path: overview, fullPage: true });
fs.unlinkSync(sheetHtml);
await browser.close();

fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2));
const count = lv => report.issues.filter(x => x.level === lv).length;
console.log(`页数 ${report.pages} · error ${count('error')} · warn ${count('warn')} · info ${count('info')}`);
const fontNotes = new Set();
for (const it of report.issues) {
  if (it.type === 'font') { fontNotes.add(it.msg); continue; }
  console.log(`  [${it.level}] P${it.page} ${it.type} ${it.name}：${it.msg}`);
}
if (fontNotes.size) console.log('  字体回退：' + [...fontNotes].join('；'));
console.log(`截图：${outDir}/slide-NN.png\n总览：${overview}\n报告：${path.join(outDir, 'report.json')}`);
process.exit(count('error') > 0 || (strict && count('warn') > 0) ? 1 : 0);
