#!/usr/bin/env node
/**
 * 构建后处理：把 _site 里 HTML 页面中的 LaTeX 公式就地替换成 MathML。
 * 产物是纯静态的 <math> 标记，读者端不需要 JavaScript，也不需要 KaTeX 的 CSS 和字体。
 *
 * 用法：node tools/render-math.js _site
 */
"use strict";

const fs = require("fs");
const path = require("path");
const katex = require("./katex.min.js");

const root = path.resolve(process.argv[2] || "_site");

// kramdown 会把公式里的 & < > 转义，渲染前要还原成 LaTeX 原文
const ENTITY = { amp: "&", lt: "<", gt: ">", quot: '"', "#39": "'", nbsp: "\u00a0" };
const decode = (s) => s.replace(/&(amp|lt|gt|quot|#39|nbsp);/g, (m, k) => ENTITY[k]);

function renderMath(tex, displayMode) {
  const html = katex.renderToString(decode(tex), {
    output: "mathml",
    displayMode: displayMode,
    throwOnError: true,
    strict: "ignore", // 中文变量名在数学模式下只是 KaTeX 的告警，不是错误
  });
  // 去掉 KaTeX 自己的 <span class="katex"> 外壳，只留 <math>
  return html.replace(/^<span class="katex">/, "").replace(/<\/span>$/, "");
}

const RULES = [
  { re: /\\\[([\s\S]+?)\\\]/g, display: true },    // kramdown 输出的块级公式
  { re: /\$\$([\s\S]+?)\$\$/g, display: true },     // 手写的 $$...$$
  { re: /\\\(([\s\S]+?)\\\)/g, display: false },    // \( ... \)
  { re: /\$(?![\s$])([^$\n]{1,500}?)(?<![\s$])\$/g, display: false }, // 行内 $...$
];

function convert(html) {
  // 代码块、脚本、样式以及 no-katex 标记里的 $ 不是公式，先整体挪走
  const stash = [];
  const keep = (s) => `\u0000STASH${stash.push(s) - 1}\u0000`;

  let out = html
    .replace(/<script\b[\s\S]*?<\/script>/gi, keep)
    .replace(/<style\b[\s\S]*?<\/style>/gi, keep)
    .replace(/<pre\b[\s\S]*?<\/pre>/gi, keep)
    .replace(/<code\b[\s\S]*?<\/code>/gi, keep)
    .replace(/<span[^>]*class="[^"]*\bno-katex\b[^"]*"[^>]*>[\s\S]*?<\/span>/gi, keep);

  let count = 0;
  for (const rule of RULES) {
    out = out.replace(rule.re, (match, tex) => {
      try {
        const mathml = renderMath(tex, rule.display);
        count += 1;
        return mathml;
      } catch (e) {
        return match; // 解析失败就原样保留，宁可露出 LaTeX 也不吞掉原文
      }
    });
  }

  return { html: out.replace(/\u0000STASH(\d+)\u0000/g, (m, i) => stash[Number(i)]), count };
}

function htmlFiles(dir, acc) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      htmlFiles(full, acc);
    } else if (entry.name.endsWith(".html")) {
      acc.push(full);
    }
  }
  return acc;
}

let files = 0;
let formulas = 0;
for (const file of htmlFiles(root, [])) {
  const html = fs.readFileSync(file, "utf8");
  if (!/\\\[|\\\(|\$/.test(html)) continue;

  const { html: out, count } = convert(html);
  if (count === 0) continue;

  fs.writeFileSync(file, out);
  files += 1;
  formulas += count;
}

console.log(`MathML：${files} 个页面，共 ${formulas} 个公式`);
