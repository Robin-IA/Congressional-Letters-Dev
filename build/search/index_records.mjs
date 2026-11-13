// Write a Pagefind index from a file of records, one JSON object a line.
//
//   node build/search/index_records.mjs <records.jsonl> <output dir>
//
// Each record is Pagefind's CustomRecord: {url, content, language, meta, sort}.
// build/build_search.py writes the records; this only hands them to Pagefind,
// so the choice of what is indexed stays in Python beside the rest of the build.
import { createReadStream } from "node:fs";
import { createInterface } from "node:readline";
import * as pagefind from "pagefind";

const [recordsPath, outputPath] = process.argv.slice(2);
if (!recordsPath || !outputPath) {
  console.error("usage: node index_records.mjs <records.jsonl> <output dir>");
  process.exit(2);
}

const { index, errors } = await pagefind.createIndex({ forceLanguage: "en" });
if (errors.length) { console.error(errors.join("\n")); process.exit(1); }

let added = 0, failed = 0;
const lines = createInterface({ input: createReadStream(recordsPath, "utf8"), crlfDelay: Infinity });
for await (const line of lines) {
  if (!line.trim()) continue;
  const { errors: e } = await index.addCustomRecord(JSON.parse(line));
  if (e.length) { failed += 1; if (failed <= 5) console.error(e.join("\n")); } else added += 1;
}

const written = await index.writeFiles({ outputPath });
if (written.errors.length) { console.error(written.errors.join("\n")); process.exit(1); }
await pagefind.close();
console.log(`${added} records indexed, ${failed} failed -> ${written.outputPath}`);
process.exit(failed ? 1 : 0);
