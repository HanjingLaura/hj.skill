#!/usr/bin/env node
/**
 * Validate a canonical AI-talent research dataset, create the fixed workbook,
 * round-trip inspect it, and render every sheet for visual QA.
 */

import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const SCHOOL_HEADERS = [
  "姓名",
  "人员状态",
  "学院 / 实验室",
  "当前或最新去向",
  "相关背景",
  "研究方向",
  "代表著作 / 项目",
  "Email",
  "其他联系方式",
  "联系方式可信度",
  "个人主页 / Scholar / GitHub",
  "Reference",
  "备注",
  "核验日期",
];

const BACKGROUND_STATUSES = new Set([
  "公开证据明确",
  "大陆经历明确",
  "港澳台经历明确",
  "姓名线索待核验",
  "背景未确认",
]);
const EMAIL_CONFIDENCES = new Set(["已核验", "较可信", "待复查"]);
const COVERAGE_STATUSES = new Set(["完成", "进行中", "受阻"]);
const MISSING_EMAIL = "未找到公开Email";
const URL_RE = /^https?:\/\//i;
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

class DatasetError extends Error {}

function required(object, key, context) {
  if (!(key in object)) throw new DatasetError(`${context}: missing required key '${key}'`);
  return object[key];
}

function uniqueStrings(values = []) {
  return [...new Set(values.map((value) => String(value ?? "").trim()).filter(Boolean))];
}

function joinLines(values = []) {
  return uniqueStrings(values).join("\n");
}

function urlsFrom(items = []) {
  const urls = [];
  for (const item of items) {
    const url = typeof item === "string" ? item.trim() : String(item?.url ?? "").trim();
    if (url) urls.push(url);
  }
  return uniqueStrings(urls);
}

function labelledItems(items = []) {
  const lines = [];
  for (const item of items) {
    if (typeof item === "string") {
      if (item.trim()) lines.push(item.trim());
      continue;
    }
    if (!item || typeof item !== "object") continue;
    const parts = [item.type, item.url, item.note, item.reason]
      .map((part) => String(part ?? "").trim())
      .filter(Boolean);
    if (parts.length) lines.push(parts.join(" | "));
  }
  return joinLines(lines);
}

function validateUrls(items, context) {
  for (const url of urlsFrom(items)) {
    if (!URL_RE.test(url)) throw new DatasetError(`${context}: not an http(s) URL: ${url}`);
  }
}

function safeSheetName(name, used) {
  let base = String(name ?? "").replace(/[\[\]:*?/\\]/g, " ").trim().replace(/^'+|'+$/g, "") || "学校";
  if (base.length > 31) {
    const digest = crypto.createHash("sha1").update(base, "utf8").digest("hex").slice(0, 5);
    base = `${base.slice(0, 25)}-${digest}`;
  }
  let candidate = base;
  let suffix = 2;
  while (used.has(candidate.toLocaleLowerCase())) {
    const tail = `-${suffix}`;
    candidate = `${base.slice(0, 31 - tail.length)}${tail}`;
    suffix += 1;
  }
  used.add(candidate.toLocaleLowerCase());
  return candidate;
}

function validateDataset(data) {
  const project = required(data, "project", "dataset");
  const schools = required(data, "schools", "dataset");
  const people = required(data, "people", "dataset");
  if (!project || typeof project !== "object" || Array.isArray(project)) {
    throw new DatasetError("project must be an object");
  }
  if (!Array.isArray(schools) || !Array.isArray(people)) {
    throw new DatasetError("schools and people must be arrays");
  }
  for (const key of ["target_region", "as_of_date"]) {
    if (!String(required(project, key, "project")).trim()) {
      throw new DatasetError(`project.${key} must not be blank`);
    }
  }
  if (!schools.length) throw new DatasetError("schools must not be empty");

  const schoolNames = new Set();
  schools.forEach((school, index) => {
    const context = `schools[${index + 1}]`;
    const name = String(required(school, "name", context)).trim();
    if (!name) throw new DatasetError(`${context}.name must not be blank`);
    if (schoolNames.has(name)) throw new DatasetError(`duplicate school name: ${name}`);
    schoolNames.add(name);
    const status = String(required(school, "coverage_status", context)).trim();
    if (!COVERAGE_STATUSES.has(status)) {
      throw new DatasetError(`${context}.coverage_status invalid: ${status}`);
    }
    validateUrls(school.selection_references ?? [], `${context}.selection_references`);
    validateUrls(school.blocked_pages ?? [], `${context}.blocked_pages`);
    const rounds = school.expansion_round_new_counts ?? [];
    if (!Array.isArray(rounds) || rounds.some((value) => !Number.isInteger(value) || value < 0)) {
      throw new DatasetError(`${context}.expansion_round_new_counts must be non-negative integers`);
    }
    if (status === "完成") {
      const gates = [
        "faculty_checked",
        "doctoral_checked",
        "postdoc_checked",
        "alumni_checked",
        "paper_expansion_completed",
      ];
      const falseGates = gates.filter((gate) => school[gate] !== true);
      if (falseGates.length) {
        throw new DatasetError(`${context} marked 完成 but gates are false: ${falseGates.join(", ")}`);
      }
      if (rounds.length < 2 || rounds.at(-1) !== 0 || rounds.at(-2) !== 0) {
        throw new DatasetError(`${context} marked 完成 without two final zero-new expansion rounds`);
      }
    }
  });

  const personIds = new Set();
  people.forEach((person, index) => {
    const context = `people[${index + 1}]`;
    for (const key of [
      "person_id",
      "name",
      "status",
      "school_affiliations",
      "background_status",
      "email",
      "email_confidence",
      "verified_date",
    ]) {
      required(person, key, context);
    }
    const personId = String(person.person_id).trim();
    if (!personId) throw new DatasetError(`${context}.person_id must not be blank`);
    if (personIds.has(personId)) throw new DatasetError(`duplicate person_id: ${personId}`);
    personIds.add(personId);
    if (!String(person.name).trim() || !String(person.status).trim()) {
      throw new DatasetError(`${context}: name and status must not be blank`);
    }
    if (!Array.isArray(person.school_affiliations) || !person.school_affiliations.length) {
      throw new DatasetError(`${context}.school_affiliations must be a non-empty array`);
    }
    for (const affiliation of person.school_affiliations) {
      const school = String(affiliation?.school ?? "").trim();
      if (!schoolNames.has(school)) throw new DatasetError(`${context}: unknown affiliated school '${school}'`);
    }
    const background = String(person.background_status).trim();
    if (!BACKGROUND_STATUSES.has(background)) {
      throw new DatasetError(`${context}.background_status invalid: ${background}`);
    }
    const email = String(person.email).trim();
    const confidence = String(person.email_confidence).trim();
    if (!email) throw new DatasetError(`${context}.email must be an address or '${MISSING_EMAIL}'`);
    if (!EMAIL_CONFIDENCES.has(confidence)) {
      throw new DatasetError(`${context}.email_confidence invalid: ${confidence}`);
    }
    validateUrls(person.email_sources ?? [], `${context}.email_sources`);
    if (email !== MISSING_EMAIL) {
      const addresses = email.split(/[;,\n]+/).map((value) => value.trim()).filter(Boolean);
      if (!addresses.length || addresses.some((value) => !EMAIL_RE.test(value))) {
        throw new DatasetError(`${context}: email must contain only complete public email address(es)`);
      }
      if (!urlsFrom(person.email_sources ?? []).length) {
        throw new DatasetError(`${context}: public email lacks email_sources`);
      }
    }
    if (email === MISSING_EMAIL && confidence !== "待复查") {
      throw new DatasetError(`${context}: missing email must use 待复查`);
    }
    validateUrls(person.profiles ?? [], `${context}.profiles`);
    validateUrls(person.references ?? [], `${context}.references`);
    if (!(person.research_areas ?? []).length && email === MISSING_EMAIL && !urlsFrom(person.profiles ?? []).length) {
      throw new DatasetError(`${context}: needs research, a public email, or a trackable profile`);
    }
    if (["公开证据明确", "大陆经历明确", "港澳台经历明确"].includes(background)) {
      if (!String(person.background_evidence ?? "").trim() || !urlsFrom(person.references ?? []).length) {
        throw new DatasetError(`${context}: ${background} requires evidence note and reference`);
      }
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(person.verified_date).trim())) {
      throw new DatasetError(`${context}.verified_date must be YYYY-MM-DD`);
    }
  });
  return { project, schools, people };
}

function affiliationMap(person) {
  const grouped = new Map();
  for (const affiliation of person.school_affiliations) {
    const school = String(affiliation.school).trim();
    if (!grouped.has(school)) grouped.set(school, []);
    grouped.get(school).push(affiliation);
  }
  return grouped;
}

function profileText(person) {
  return labelledItems(person.profiles ?? []);
}

function referenceText(person) {
  const emailItems = urlsFrom(person.email_sources ?? []).map((url) => ({ type: "Email来源", url }));
  return labelledItems([...emailItems, ...(person.references ?? [])]);
}

function notesText(person, affiliations) {
  const parts = [
    String(person.notes ?? "").trim(),
    String(person.background_evidence ?? "").trim(),
    ...affiliations.map((item) => String(item.association_note ?? "").trim()),
  ];
  if ((person.review_reasons ?? []).length) {
    parts.push(`待复查：${uniqueStrings(person.review_reasons).join("；")}`);
  }
  return joinLines(parts);
}

function reviewReasons(person) {
  const reasons = [...(person.review_reasons ?? [])];
  if (person.email === MISSING_EMAIL) reasons.push("未找到公开Email");
  if (person.email_confidence === "待复查" && person.email !== MISSING_EMAIL) reasons.push("Email待复查");
  if (person.background_status === "姓名线索待核验") reasons.push("姓名线索待核验");
  return uniqueStrings(reasons);
}

function inspectionHasMatches(ndjson) {
  return /"kind"\s*:\s*"match"/.test(String(ndjson ?? ""));
}

function writeTableSheet(workbook, name, headers, rows, widths, tableName, previewSpecs) {
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
  const matrix = [headers, ...rows].map((row) => row.map((value) => value ?? ""));
  const usedRange = sheet.getRangeByIndexes(0, 0, matrix.length, headers.length);
  usedRange.values = matrix;
  usedRange.format = {
    font: { name: "Aptos", size: 10, color: "#1F2937" },
    verticalAlignment: "top",
    wrapText: true,
  };
  const header = sheet.getRangeByIndexes(0, 0, 1, headers.length);
  header.format = {
    fill: "#17365D",
    font: { name: "Aptos Display", size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    rowHeight: 28,
    borders: { preset: "outside", style: "thin", color: "#17365D" },
  };
  if (matrix.length > 1) {
    const body = sheet.getRangeByIndexes(1, 0, matrix.length - 1, headers.length);
    body.format.borders = {
      insideHorizontal: { style: "thin", color: "#E5E7EB" },
      bottom: { style: "thin", color: "#CBD5E1" },
    };
  }
  widths.forEach((width, columnIndex) => {
    sheet.getRangeByIndexes(0, columnIndex, matrix.length, 1).format.columnWidth = width;
  });
  usedRange.format.autofitRows();
  header.format.rowHeight = 28;
  if (matrix.length > 1) {
    sheet.getRangeByIndexes(1, 0, matrix.length - 1, headers.length).format.rowHeight =
      headers.length >= 10 ? 72 : 34;
  }
  sheet.freezePanes.freezeRows(1);
  const table = sheet.tables.add(usedRange, true, tableName);
  table.style = "TableStyleMedium2";
  table.showBandedRows = true;
  table.showFilterButton = true;
  previewSpecs.push({ name, rowCount: matrix.length, columnCount: headers.length });
  return sheet;
}

async function buildWorkbook(data, outputPath, previewDir) {
  const { project, schools, people } = validateDataset(data);
  const usedNames = new Set(["总览", "学校覆盖", "跨校去重", "待复查"].map((value) => value.toLocaleLowerCase()));
  const sheetNames = new Map();
  schools.forEach((school) => {
    const requested = String(school.sheet_name ?? "").trim() || school.name;
    sheetNames.set(school.name, safeSheetName(requested, usedNames));
  });

  const emailCounts = new Map(EMAIL_CONFIDENCES.values().map((value) => [value, 0]));
  let missingCount = 0;
  people.forEach((person) => {
    if (person.email === MISSING_EMAIL) missingCount += 1;
    else emailCounts.set(person.email_confidence, emailCounts.get(person.email_confidence) + 1);
  });
  const reviewPeople = people.filter((person) =>
    person.email === MISSING_EMAIL ||
    person.email_confidence === "待复查" ||
    person.background_status === "姓名线索待核验" ||
    (person.review_reasons ?? []).length
  );

  const workbook = Workbook.create();
  const previewSpecs = [];
  writeTableSheet(
    workbook,
    "总览",
    ["指标", "值", "说明 / Reference"],
    [
      ["目标地区", project.target_region, "项目变量"],
      ["核验日期", project.as_of_date, "当前数据快照日期"],
      ["排名快照", project.ranking_snapshot ?? "", project.ranking_reference ?? ""],
      ["纳入学校数", schools.length, "不含空白学校"],
      ["全局唯一人数", people.length, "按 person_id 去重"],
      ["已核验Email人数", emailCounts.get("已核验"), "非缺失Email"],
      ["较可信Email人数", emailCounts.get("较可信"), "非缺失Email"],
      ["待复查Email人数", emailCounts.get("待复查"), "非缺失Email"],
      ["未找到公开Email人数", missingCount, "保留可追踪主页/论文"],
      ["待复查记录数", reviewPeople.length, "按人员记录去重"],
      ["完成学校数", schools.filter((school) => school.coverage_status === "完成").length, ""],
      ["进行中学校数", schools.filter((school) => school.coverage_status === "进行中").length, ""],
      ["受阻学校数", schools.filter((school) => school.coverage_status === "受阻").length, ""],
      ["项目备注", project.notes ?? "", ""],
    ],
    [24, 22, 70],
    "Table_Overview",
    previewSpecs,
  );

  writeTableSheet(
    workbook,
    "学校覆盖",
    [
      "学校", "Sheet名称", "覆盖状态", "纳入依据", "官网", "已检查学院 / 目录", "已检查实验室",
      "教师", "博士生", "博士后", "Alumni", "论文扩散", "各轮新增人数", "选择Reference", "受阻页面", "备注",
    ],
    schools.map((school) => [
      school.name,
      sheetNames.get(school.name),
      school.coverage_status,
      school.inclusion_basis ?? "",
      school.official_url ?? "",
      joinLines(school.units_checked ?? []),
      joinLines(school.labs_checked ?? []),
      school.faculty_checked ? "是" : "否",
      school.doctoral_checked ? "是" : "否",
      school.postdoc_checked ? "是" : "否",
      school.alumni_checked ? "是" : "否",
      school.paper_expansion_completed ? "是" : "否",
      (school.expansion_round_new_counts ?? []).join(", "),
      labelledItems(school.selection_references ?? []),
      labelledItems(school.blocked_pages ?? []),
      school.coverage_notes ?? "",
    ]),
    [28, 24, 12, 34, 34, 36, 36, 10, 10, 10, 10, 12, 18, 46, 46, 36],
    "Table_SchoolCoverage",
    previewSpecs,
  );

  writeTableSheet(
    workbook,
    "跨校去重",
    [
      "统一身份ID", "姓名", "关联学校", "人员状态", "当前或最新去向", "Email", "联系方式可信度",
      "身份主页", "去重依据", "相关 / 待比较ID", "Reference", "备注", "核验日期",
    ],
    people.map((person) => [
      person.person_id,
      person.name,
      joinLines(person.school_affiliations.map((item) => item.school)),
      person.status,
      person.current_destination ?? "",
      person.email,
      person.email_confidence,
      profileText(person),
      person.identity_match_basis ?? "",
      joinLines(person.related_person_ids ?? []),
      referenceText(person),
      person.notes ?? "",
      person.verified_date,
    ]),
    [16, 20, 34, 18, 30, 30, 16, 46, 34, 22, 55, 40, 14],
    "Table_CrossSchoolDedupe",
    previewSpecs,
  );

  writeTableSheet(
    workbook,
    "待复查",
    [
      "统一身份ID", "姓名", "关联学校", "人员状态", "当前或最新去向", "相关背景", "Email",
      "联系方式可信度", "待复查原因", "可追踪主页", "Reference", "备注", "核验日期",
    ],
    reviewPeople.map((person) => [
      person.person_id,
      person.name,
      joinLines(person.school_affiliations.map((item) => item.school)),
      person.status,
      person.current_destination ?? "",
      person.background_status,
      person.email,
      person.email_confidence,
      joinLines(reviewReasons(person)),
      profileText(person),
      referenceText(person),
      person.notes ?? "",
      person.verified_date,
    ]),
    [16, 20, 32, 18, 30, 18, 30, 16, 36, 44, 55, 40, 14],
    "Table_ReviewQueue",
    previewSpecs,
  );

  schools.forEach((school, schoolIndex) => {
    const rows = [];
    people.forEach((person) => {
      const affiliations = affiliationMap(person).get(school.name);
      if (!affiliations) return;
      rows.push([
        person.name,
        person.status,
        joinLines(affiliations.map((item) => item.unit_lab ?? "")),
        person.current_destination ?? "",
        person.background_status,
        joinLines(person.research_areas ?? []),
        joinLines(person.representative_works ?? []),
        person.email,
        person.other_contacts ?? "",
        person.email_confidence,
        profileText(person),
        referenceText(person),
        notesText(person, affiliations),
        person.verified_date,
      ]);
    });
    const sheet = writeTableSheet(
      workbook,
      sheetNames.get(school.name),
      SCHOOL_HEADERS,
      rows,
      [20, 17, 34, 30, 18, 34, 42, 30, 28, 17, 50, 60, 44, 14],
      `Table_School_${String(schoolIndex + 1).padStart(3, "0")}`,
      previewSpecs,
    );
    if (rows.length) {
      sheet.getRange(`E2:E${rows.length + 1}`).dataValidation = {
        rule: { type: "list", values: [...BACKGROUND_STATUSES] },
      };
      sheet.getRange(`J2:J${rows.length + 1}`).dataValidation = {
        rule: { type: "list", values: [...EMAIL_CONFIDENCES] },
      };
    }
  });

  const preExportErrors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 300 },
    summary: "pre-export formula error scan",
  });
  if (inspectionHasMatches(preExportErrors.ndjson)) {
    throw new DatasetError(`pre-export formula error scan returned results:\n${preExportErrors.ndjson}`);
  }

  if (previewDir) {
    await fs.mkdir(previewDir, { recursive: true });
    const maxPreviewRows = 50;
    const maxPreviewColumns = 7;
    const columnName = (zeroBasedIndex) => {
      let value = zeroBasedIndex + 1;
      let result = "";
      while (value > 0) {
        value -= 1;
        result = String.fromCharCode(65 + (value % 26)) + result;
        value = Math.floor(value / 26);
      }
      return result;
    };
    for (const spec of previewSpecs) {
      const safeFile = spec.name.replace(/[<>:"/\\|?*]/g, "_");
      const lastRow = Math.min(spec.rowCount, maxPreviewRows);
      for (let firstColumn = 0, part = 1; firstColumn < spec.columnCount; firstColumn += maxPreviewColumns, part += 1) {
        const lastColumn = Math.min(firstColumn + maxPreviewColumns - 1, spec.columnCount - 1);
        const range = `${columnName(firstColumn)}1:${columnName(lastColumn)}${lastRow}`;
        const preview = await workbook.render({ sheetName: spec.name, range, scale: 1, format: "png" });
        const suffix = spec.columnCount > maxPreviewColumns ? `__part${part}` : "";
        await fs.writeFile(
          path.join(previewDir, `${safeFile}${suffix}.png`),
          new Uint8Array(await preview.arrayBuffer()),
        );
      }
    }
  }

  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  const xlsx = await SpreadsheetFile.exportXlsx(workbook);
  await xlsx.save(outputPath);

  const imported = await SpreadsheetFile.importXlsx(await FileBlob.load(outputPath));
  const roundTrip = await imported.inspect({
    kind: "sheet",
    include: "id,name",
    maxChars: 20000,
  });
  const expectedNames = ["总览", "学校覆盖", "跨校去重", "待复查", ...schools.map((s) => sheetNames.get(s.name))];
  for (const name of expectedNames) {
    if (!roundTrip.ndjson.includes(`"name":"${name}"`) && !roundTrip.ndjson.includes(`"name": "${name}"`)) {
      throw new DatasetError(`round-trip workbook is missing sheet: ${name}`);
    }
  }
  const roundTripErrors = await imported.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 300 },
    summary: "round-trip formula error scan",
  });
  if (inspectionHasMatches(roundTripErrors.ndjson)) {
    throw new DatasetError(`round-trip formula error scan returned results:\n${roundTripErrors.ndjson}`);
  }

  return {
    output: outputPath,
    previews: previewDir ?? "",
    schools: schools.length,
    people: people.length,
    emails: people.length - missingCount,
    missing_emails: missingCount,
    review: reviewPeople.length,
  };
}

function parseArgs(argv) {
  const args = { dataset: null, output: null, previewDir: null, validateOnly: false };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--output") args.output = argv[++index];
    else if (value === "--preview-dir") args.previewDir = argv[++index];
    else if (value === "--validate-only") args.validateOnly = true;
    else if (!args.dataset) args.dataset = value;
    else throw new DatasetError(`unexpected argument: ${value}`);
  }
  if (!args.dataset) throw new DatasetError("usage: build_workbook.mjs <dataset.json> [--output file.xlsx] [--preview-dir dir] [--validate-only]");
  return args;
}

async function main() {
  try {
    const args = parseArgs(process.argv.slice(2));
    const datasetPath = path.resolve(args.dataset);
    const data = JSON.parse((await fs.readFile(datasetPath, "utf8")).replace(/^\uFEFF/, ""));
    const { project, schools, people } = validateDataset(data);
    if (args.validateOnly) {
      console.log(JSON.stringify({ valid: true, schools: schools.length, people: people.length }));
      return;
    }
    const outputPath = path.resolve(
      args.output ?? path.join(path.dirname(datasetPath), `${project.target_region}高校_AI人才及联系方式_${project.as_of_date}.xlsx`),
    );
    if (path.extname(outputPath).toLowerCase() !== ".xlsx") {
      throw new DatasetError("--output must end in .xlsx");
    }
    const summary = await buildWorkbook(data, outputPath, args.previewDir ? path.resolve(args.previewDir) : null);
    console.log(JSON.stringify({ valid: true, ...summary }));
  } catch (error) {
    console.error(`ERROR: ${error instanceof Error ? error.message : String(error)}`);
    process.exitCode = 2;
  }
}

await main();
