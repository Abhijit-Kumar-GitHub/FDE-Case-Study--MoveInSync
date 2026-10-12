// Recommendation deck for MoveInSync, built from data/processed/metrics.json.
// Run: npm install pptxgenjs@3, then PPTX_SKILL=<pptx skill dir> node src/deck.js
// (the skill's apply_theme.js writes the theme colours; any copy of it works).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "docs", "deck.pptx");
const M = JSON.parse(fs.readFileSync(path.join(ROOT, "data/processed/metrics.json"), "utf8"));
const T = M.themes;

const THEME = {
  name: "MoveInSync Ratings",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "14213D", lt1: "FFFFFF", dk2: "3D4A5C", lt2: "F3F4F6",
    accent1: "F2A541", accent2: "2A6F97", accent3: "E76F51", accent4: "2A9D8F", accent5: "9AA5B1", accent6: "C0392B",
    hlink: "2A6F97", folHlink: "6B7280",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.author = "Abhijit Kumar";
pres.title = "Play Store ratings: what is actually wrong, and what to fix first";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.05, w: 8.8, h: 1.7, fontSize: 36, bold: true, color: C.background1, valign: "bottom", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "subtitle", type: "body", x: 0.6, y: 2.95, w: 8.8, h: 0.5, fontSize: 16, color: C.background2, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: HEX.lt1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.32, w: 9.0, h: 0.7, fontSize: 30, bold: true, color: C.text1, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "MoveInSync · Play Store ratings · October 2026", options: { x: 0.5, y: 5.22, w: 6, h: 0.25, fontSize: 10, color: C.accent5, margin: 0 } } },
  ],
  slideNumber: { x: 9.0, y: 5.22, w: 0.5, h: 0.25, fontSize: 10, color: C.accent5, align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSE_DARK",
  background: { color: HEX.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.32, w: 9.0, h: 0.7, fontSize: 30, bold: true, color: C.background1, valign: "middle", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 9.0, y: 5.22, w: 0.5, h: 0.25, fontSize: 10, color: C.accent5, align: "right" },
});

// ---------- helpers ----------
const card = (s, x, y, w, h, name) =>
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: C.background2 }, line: { type: "none" }, objectName: name });
const badge = (s, x, y, label, name, fill = C.accent1, color = C.text1, d = 0.42) => {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" }, objectName: name });
  s.addText(label, { x, y, w: d, h: d, fontSize: 14, bold: true, color, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: name + " label" });
};
const stat = (s, x, y, w, value, label, name, opts = {}) => {
  s.addText(value, { x, y, w, h: 0.55, fontSize: opts.size || 32, bold: true, color: opts.color || C.text1, margin: 0, valign: "bottom", isTextBox: true, objectName: name + " value", fontFace: THEME.headFontFace });
  s.addText(label, { x, y: y + 0.58, w, h: opts.labelH || 0.5, fontSize: 14, color: opts.labelColor || C.text2, margin: 0, valign: "top", isTextBox: true, objectName: name + " label" });
};
const chartText = { catAxisLabelColor: HEX.dk2, valAxisLabelColor: HEX.dk2, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, titleFontFace: "+mn-lt", titleFontSize: 12, titleColor: HEX.dk2,
  dataLabelFontFace: "+mn-lt", dataLabelFontSize: 10, dataLabelColor: HEX.dk1, legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: HEX.dk2,
  valGridLine: { color: "E5E7EB", size: 0.75 }, catGridLine: { style: "none" } };

// ---------- 1. title ----------
pres.addSection({ title: "Answer" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Answer" });
s.addText("Play Store ratings: what's actually wrong, and what to fix first", { placeholder: "title" });
s.addText("Recommendation for MoveInSync  ·  Abhijit Kumar  ·  13 October 2026", { placeholder: "subtitle" });
[["4.64★", "store rating, India"], ["24,315", "written reviews analysed"], ["1,400", "AI-labelled, 94% right in a human audit"]].forEach(([v, l], i) => {
  const x = 0.6 + i * 3.0;
  s.addText(v, { x, y: 3.9, w: 2.8, h: 0.6, fontSize: 30, bold: true, color: C.accent1, margin: 0, isTextBox: true, objectName: `title stat ${i}`, fontFace: THEME.headFontFace });
  s.addText(l, { x, y: 4.5, w: 2.8, h: 0.5, fontSize: 14, color: C.background2, margin: 0, valign: "top", isTextBox: true, objectName: `title stat label ${i}` });
});
s.addNotes("Hi, I'm Abhijit Kumar, and this is my recommendation for MoveInSync's Play Store ratings. The short version: the store number isn't really the problem. What people read is, and it's mostly the app, not the cabs. I'll show the evidence, then exactly what I'd fix first.");

// ---------- 2. the answer ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Answer" });
s.addText("The answer in four points", { placeholder: "title" });
const pts = [
  ["Not behind the market", "#2 of 8 commute apps benchmarked, and 0.011 stars from showing 4.7."],
  ["What people read is harsh", "Written reviews average 3.84★; 9 of the first 10 a visitor sees are 1–2★."],
  ["It's the app, not the cabs", "73% of specific complaints are about the app; late or missed cabs, under 5%."],
  ["It's getting worse now", "Stability complaints reached 25% of negative reviews in Q3 2026."],
];
pts.forEach(([h, b], i) => {
  const x = 0.5 + (i % 2) * 4.6, y = 1.2 + Math.floor(i / 2) * 1.75;
  card(s, x, y, 4.4, 1.55, `answer card ${i + 1}`);
  badge(s, x + 0.25, y + 0.25, String(i + 1), `answer badge ${i + 1}`);
  s.addText(h, { x: x + 0.85, y: y + 0.22, w: 3.35, h: 0.45, fontSize: 18, bold: true, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: `answer head ${i + 1}`, fontFace: THEME.headFontFace });
  s.addText(b, { x: x + 0.85, y: y + 0.7, w: 3.35, h: 0.7, fontSize: 14, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: `answer body ${i + 1}` });
});
s.addText([{ text: "Do first: ", options: { bold: true, color: C.text1 } }, { text: "fix the false install lock-out, gate releases, restart replies, drop the rating wall.", options: { color: C.text2 } }],
  { x: 0.5, y: 4.75, w: 9.0, h: 0.35, fontSize: 14, margin: 0, isTextBox: true, objectName: "do first" });
s.addNotes("Four points. One: against the market, MoveInSync isn't behind. It's second of eight, and 0.011 stars from showing 4.7. Two: the problem is what people read. Written reviews average 3.84, and nine of the first ten a visitor sees are one or two stars. Three: it's the app, not the cabs. Seventy-three percent of specific complaints are about the app itself. Four: it's getting worse right now, with a stability regression in the current releases.");

// ---------- 3. where it stands ----------
pres.addSection({ title: "Diagnosis" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Diagnosis" });
s.addText("Not behind the market", { placeholder: "title" });
const bench = M.benchmark.filter((b) => b.score != null).sort((a, b) => a.score - b.score);
const fmtK = (n) => (n >= 10000 ? Math.round(n / 1000) + "K" : n >= 1000 ? (n / 1000).toFixed(1) + "K" : String(n));
s.addChart(pres.charts.BAR, [{ name: "Rating", labels: bench.map((b) => `${b.name.replace(/ \((.+)\)/, ", $1")} (${fmtK(b.ratings)})`), values: bench.map((b) => b.score) }], {
  x: 0.4, y: 1.1, w: 5.6, h: 3.95, barDir: "bar", barGapWidthPct: 60,
  chartColors: bench.map((b) => (b.role === "employee" ? HEX.accent1 : HEX.accent5)),
  valAxisMinVal: 0, valAxisMaxVal: 5, valAxisMajorUnit: 1, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00",
  showTitle: true, title: "Play Store rating, India storefront (number of ratings)", showLegend: false, objectName: "benchmark chart", ...chartText,
});
stat(s, 6.4, 1.15, 3.1, "0.011", "stars from showing 4.7 — Play rounds 4.639 down to 4.6", "gap", { labelH: 0.55 });
stat(s, 6.4, 2.45, 3.1, "114,880", "ratings: nearly 5× Safetrax's, and more than the other seven combined", "volume", { labelH: 0.55 });
stat(s, 6.4, 3.75, 3.1, "4.3★", "what the same app shows in the US; ratings are per country", "country", { labelH: 0.55 });
s.addNotes("Here's the benchmark against seven other employee-commute apps. MoveInSync is second, 0.08 behind Safetrax Commuter, but on nearly five times the ratings: 115 thousand against 24 thousand. Safetrax had just 114 written reviews last year; MoveInSync had 2,848. MoveInSync has more ratings than the other seven combined. The Play Store rounds to one decimal, so 4.639 shows as 4.6. Crossing 4.65 flips the display to 4.7. One trap worth knowing: ratings are per country. The same app shows 4.3 in the US.");

// ---------- 4. what people read ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Diagnosis" });
s.addText("The problem is what people read", { placeholder: "title" });
stat(s, 0.5, 1.15, 3.5, M.windows.last_365d.mean.toFixed(2) + "★", "average of written reviews, last 12 months (store shows 4.64)", "written avg", { labelH: 0.55 });
stat(s, 0.5, 2.45, 3.5, Math.round(M.windows.last_365d.share_1star * 100) + "%", "of those written reviews are 1★", "one star", { labelH: 0.55 });
stat(s, 0.5, 3.75, 3.5, Math.round(M.visitor_view.share_1_2star_top10 * 10) + " of 10", "first reviews a visitor sees are 1–2★ — and 9 are unanswered", "visitor", { labelH: 0.55 });
const q = {};
M.monthly.filter((m) => m.month >= "2022-01" && !m.partial).forEach((m) => {
  const k = m.month.slice(0, 4) + " Q" + (Math.floor((+m.month.slice(5, 7) - 1) / 3) + 1);
  (q[k] = q[k] || []).push(m.reply_rate);
});
const qk = Object.keys(q);
s.addChart(pres.charts.LINE, [{ name: "Reply rate", labels: qk.map((k) => (k.endsWith("Q1") ? k.slice(0, 4) : "")), values: qk.map((k) => q[k].reduce((a, b) => a + b, 0) / q[k].length) }], {
  x: 4.3, y: 1.1, w: 5.2, h: 3.35, lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 5, chartColors: [HEX.accent2],
  valAxisMinVal: 0, valAxisMaxVal: 1, valAxisMajorUnit: 0.25, valAxisLabelFormatCode: "0%", showTitle: true, title: "Share of reviews with a developer reply, by quarter",
  showLegend: false, objectName: "reply chart", ...chartText,
});
s.addText("Replies stopped in mid-2024. Safetrax answers 100%, Routematic 92%.", { x: 4.3, y: 4.55, w: 5.2, h: 0.5, fontSize: 14, color: C.text2, margin: 0, isTextBox: true, objectName: "reply note" });
s.addNotes("The store number is carried by silent ratings: about four in five new ratings have no text. But the written reviews, the ones people actually read, average 3.84, and a quarter are one star. Nine of the first ten reviews a visitor sees are one or two stars, and nine of them have no reply. Replies stopped in mid-2024. Competitors answer almost every review.");

// ---------- 5. why ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Diagnosis" });
s.addText("It's the app, not the cabs", { placeholder: "title" });
const fams = T.families.filter((r) => !["U", "P", "J2", "X3"].includes(r.family)).sort((a, b) => a.mentions - b.mentions);
const kinds = [["app", "App"], ["mixed", "App + operations"], ["ops", "Transport service"], ["policy", "Employer rules"]];
s.addChart(pres.charts.BAR, kinds.map(([k, name]) => ({ name, labels: fams.map((r) => r.label), values: fams.map((r) => Math.round(r.mentions * (r.attribution[k] || 0))) })), {
  x: 0.4, y: 1.1, w: 6.0, h: 3.95, barDir: "bar", barGrouping: "stacked", barGapWidthPct: 55,
  chartColors: [HEX.accent2, HEX.accent5, HEX.accent3, HEX.accent4], showLegend: true, legendPos: "b",
  showTitle: true, title: "1–2★ reviews mentioning each stage, last 12 months", objectName: "journey chart", ...chartText,
});
const spec = T.attribution_1_2star_specific;
stat(s, 6.8, 1.1, 2.7, Math.round(spec.app * 100) + "%", "about the app itself", "app share", { size: 28, labelH: 0.3 });
stat(s, 6.8, 2.05, 2.7, Math.round(spec.mixed * 100) + "%", "app + operations (mostly routing)", "mixed share", { size: 28, labelH: 0.5 });
stat(s, 6.8, 3.0, 2.7, Math.round(spec.ops * 100) + "%", "purely the transport service", "ops share", { size: 28, labelH: 0.3 });
stat(s, 6.8, 3.95, 2.7, "<5%", "late, unassigned or missed cabs", "cab share", { size: 28, labelH: 0.5 });
s.addNotes("Why? I labelled every one- and two-star review from the last year by stage of the rider's journey and by who would have to fix it. Seventy-three percent of specific complaints are about the app itself: crashes, logins and OTPs, booking, and interruptions. Late, unassigned or missed cabs, the obvious suspect, come up in under five percent.");

// ---------- 6. regression ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Diagnosis" });
s.addText("A stability regression is live now", { placeholder: "title" });
const qt = T.quarterly_trend;
s.addChart(pres.charts.LINE, [
  { name: "App stability & speed", labels: qt.map((r) => r.quarter.replace("Q", " Q")), values: qt.map((r) => r.X1) },
  { name: "Login & home address", labels: qt.map((r) => r.quarter.replace("Q", " Q")), values: qt.map((r) => r.J1) },
], {
  x: 0.4, y: 1.1, w: 5.4, h: 3.95, lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 7, chartColors: [HEX.accent6, HEX.accent2],
  valAxisMinVal: 0, valAxisMaxVal: 0.3, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0%", showValue: true, dataLabelFormatCode: "0%", dataLabelPosition: "t",
  showLegend: true, legendPos: "b", showTitle: true, title: "Share of ≤3★ reviews about each theme, by quarter", objectName: "regression chart", ...chartText,
});
s.addText([
  { text: "Stability: 16% → 25% of negative reviews in Q3 2026 (p ≈ 0.01)", options: { bullet: true, breakLine: true } },
  { text: "Concentrated in versions 12.16, 12.17 and 12.19 (current)", options: { bullet: true, breakLine: true } },
  { text: "False \"not installed from Play Store\" lock-out: 9 of 12 ever reported came in Jul–Sep 2026", options: { bullet: true, breakLine: true } },
  { text: "Same failure in Q4 2023: 43 false \"rooted device\" blocks", options: { bullet: true, breakLine: true } },
  { text: "Login complaints fell 22% → 9%: fixes do show up in reviews", options: { bullet: true } },
], { x: 6.1, y: 1.15, w: 3.4, h: 3.9, fontSize: 14, color: C.text2, paraSpaceAfter: 8, margin: 0, valign: "top", isTextBox: true, objectName: "regression facts" });
s.addNotes("And it's getting worse. Stability complaints jumped from about sixteen to twenty-five percent of negative reviews in the third quarter, and that's statistically significant. It's concentrated in versions 12.16 to 12.19, including a false 'not installed from Play Store' error that locks riders out until they reinstall. The same kind of bug hit in 2023 as a false rooted-device block. The good news: login complaints fell from 22 to 9 percent after a fix, so fixes do show up in reviews.");

// ---------- 7. day-1 checks ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Diagnosis" });
s.addText("Two things to check on day 1", { placeholder: "title" });
[["The rating prompt", [
  `${T.rating_prompt.complaints_forced_or_repeated_12m} complaints in 12 months about forced or repeated rating requests`,
  "\"I have to mandatorily give a review of the previous ride before I can access current ride details\"",
  "3 reviews say it accepts only 4–5 stars. If it filters who reaches the Play prompt, that is review gating, which Google Play prohibits",
]], ["Safety reports", [
  `${T.safety.flagged_12m} reviews in 12 months flagged as possible safety risks`,
  "Human audit: 28 of 30 flags genuine; 18 describe a specific incident",
  "Today they sit unanswered on a public page. Route them to the safety desk within 24 hours",
]]].forEach(([h, items], i) => {
  const x = 0.5 + i * 4.6;
  card(s, x, 1.15, 4.4, 3.45, `check card ${i + 1}`);
  badge(s, x + 0.25, 1.38, "!", `check badge ${i + 1}`, i === 0 ? C.accent1 : C.accent6, i === 0 ? C.text1 : C.background1);
  s.addText(h, { x: x + 0.85, y: 1.35, w: 3.35, h: 0.45, fontSize: 18, bold: true, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: `check head ${i + 1}`, fontFace: THEME.headFontFace });
  s.addText(items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < items.length - 1, italic: t.startsWith("\"") } })),
    { x: x + 0.3, y: 2.0, w: 3.85, h: 2.5, fontSize: 14, color: C.text2, paraSpaceAfter: 8, margin: 0, valign: "top", isTextBox: true, objectName: `check body ${i + 1}` });
});
s.addNotes("Two things to check on day one. First, the rating prompt. Riders complain about being forced to rate every trip before they can see their current ride, and three reviews say the rating step only accepts four or five stars. If any step filters who gets sent to the Play Store, that's review gating, which Google prohibits. It takes an hour to check. Second, safety. Twenty-three reviews in the past year describe safety risks, and they sit unanswered on a public page.");

// ---------- 8. plan ----------
pres.addSection({ title: "Plan" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Plan" });
s.addText("What to do, in order", { placeholder: "title" });
const plan = [
  ["This week", ["Fix the false install lock-out", "Staged rollouts that halt on regressions", "Reply to 1–3★ in 48h (20 drafts ready)", "Skippable trip rating, no star filter", "Safety reports to the safety desk"]],
  ["Next 30 days", ["Keep riders signed in", "Reliable OTP, clear login errors", "Unambiguous booking, self-serve address", "Show employer rules when they apply", "Terms once, no blocking pop-ups"]],
  ["Next 90 days", ["Honest tracking and ETAs", "In-app complaints with status", "Service complaints to transport desks", "Ask happy riders at the right moment"]],
];
plan.forEach(([h, items], i) => {
  const x = 0.5 + i * 3.05;
  card(s, x, 1.15, 2.9, 3.35, `plan card ${i + 1}`);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.2, y: 1.32, w: 1.7, h: 0.4, rectRadius: 0.2, fill: { color: i === 0 ? C.text1 : C.background1 }, line: { color: C.text1, width: 1 }, objectName: `plan chip ${i + 1}` });
  s.addText(h, { x: x + 0.2, y: 1.32, w: 1.7, h: 0.4, fontSize: 14, bold: true, color: i === 0 ? C.background1 : C.text1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `plan chip label ${i + 1}` });
  s.addText(items.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < items.length - 1 } })),
    { x: x + 0.2, y: 1.9, w: 2.55, h: 2.6, fontSize: 14, color: C.text2, paraSpaceAfter: 6, margin: 0, valign: "top", isTextBox: true, objectName: `plan items ${i + 1}` });
});
s.addText([{ text: "Expected: ", options: { bold: true, color: C.text1 } }, { text: "halve the top four themes and written reviews rise from 3.84 to ~4.0; 1★ share falls ~5 points.", options: { color: C.text2 } }],
  { x: 0.5, y: 4.68, w: 9.0, h: 0.4, fontSize: 14, margin: 0, isTextBox: true, objectName: "expected impact" });
s.addNotes("What to do, in order. This week, stop the damage, with no new features needed: fix the false lock-out, gate releases on crash and review signals, restart replying, and I've already drafted replies to the twenty reviews visitors see first. Make trip rating skippable, and route safety reports. In thirty days, fix the top themes: logins, OTP, booking clarity and interruptions. In ninety days, tracking, complaint handling, and only then ask happy riders for ratings. Every item is a ticket with acceptance criteria in backlog.csv.");

// ---------- 9. monitor ----------
s = pres.addSlide({ masterName: "CLOSE_DARK", sectionTitle: "Plan" });
s.addText("How we'll know it worked", { placeholder: "title" });
[["Daily", "store rating snapshot; new reviews labelled; dashboard refreshed"],
 ["Weekly", "the answer posted as a GitHub Issue, with a release-watch alert"],
 ["Always", "a queue for safety reports, contradicting stars and unclear reviews"],
 ["Cost", "free on keyword rules; about $0.02 a week with Claude Sonnet 5.5"]].forEach(([h, b], i) => {
  const y = 1.2 + i * 0.9;
  badge(s, 0.5, y, String(i + 1), `monitor badge ${i + 1}`);
  s.addText([{ text: h + ": ", options: { bold: true, color: C.accent1 } }, { text: b, options: { color: C.background1 } }],
    { x: 1.1, y: y - 0.06, w: 5.0, h: 0.6, fontSize: 14, margin: 0, valign: "middle", isTextBox: true, objectName: `monitor row ${i + 1}` });
});
s.addText("94%", { x: 6.6, y: 1.2, w: 2.9, h: 0.8, fontSize: 44, bold: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "accuracy value", fontFace: THEME.headFontFace });
s.addText("of AI labels right in a human audit; every correction recorded", { x: 6.6, y: 2.0, w: 2.9, h: 0.7, fontSize: 14, color: C.background2, margin: 0, valign: "top", isTextBox: true, objectName: "accuracy label" });
s.addText([
  { text: "Dashboard", options: { bold: true, color: C.background1, breakLine: true } },
  { text: "abhijit-kumar-github.github.io/FDE-Case-Study--MoveInSync", options: { color: C.background2, breakLine: true, hyperlink: { url: "https://abhijit-kumar-github.github.io/FDE-Case-Study--MoveInSync/" } } },
  { text: "Code, data, method", options: { bold: true, color: C.background1, breakLine: true } },
  { text: "github.com/Abhijit-Kumar-GitHub/FDE-Case-Study--MoveInSync", options: { color: C.background2, hyperlink: { url: "https://github.com/Abhijit-Kumar-GitHub/FDE-Case-Study--MoveInSync" } } },
], { x: 6.6, y: 3.0, w: 2.9, h: 1.9, fontSize: 11, paraSpaceAfter: 4, margin: 0, valign: "top", isTextBox: true, objectName: "links" });
s.addNotes("Finally, 'how are our ratings?' is now answered automatically. Every day a scheduled job records the store rating, labels new reviews and refreshes the dashboard. Every week the answer is posted as a GitHub Issue, with an alert if a release regresses. Safety reports and unclear reviews go to a person. It runs free on keyword rules, or for about two cents a week with Claude Sonnet. Behind all of this: 24,315 public reviews, 1,400 labelled with AI, and a human audit that found the labels 94 percent right. Everything is in the repository. Thank you.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
