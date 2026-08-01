
// Install esbuild's JS transform hook so we can require() TypeScript directly.
const esbuild = require(process.argv[2]); // esbuild package path
esbuild.install && esbuild.install();
if (typeof require.extensions !== "undefined" && !require.extensions[".ts"]) {
  // Fallback shim
  const fs2 = require("fs");
  require.extensions[".ts"] = function (mod, filename) {
    const src = fs2.readFileSync(filename, "utf8");
    const out = esbuild.transformSync(src, { loader: "ts", format: "cjs" });
    // eslint-disable-next-line @typescript-eslint/no-implied-eval
    mod._compile(out.code, filename);
  };
  require.extensions[".tsx"] = require.extensions[".ts"];
}
const path = require("path");
// The IntentClassifier is a pure-TS file with no imports other than its own
// type file — safe to require once the ts loader is shimmed.
// Some Next.js TypeScript path-mapping imports may fail to resolve when
// required from Node directly; try a couple of strategies.
let classifyIntent;
try {
  const cls = require(process.argv[3]); // absolute path to IntentClassifier.ts
  classifyIntent = (cls && cls.classifyIntent) || (cls && cls.default && cls.default.classifyIntent);
} catch (err) {
  // Fallback: transform and evaluate inline
  const fs = require("fs");
  const src = fs.readFileSync(process.argv[3], "utf8");
  const out = esbuild.transformSync(src, { loader: "ts", format: "cjs" });
  const mod = { exports: {} };
  const fn = new Function("module", "exports", "require", "__dirname", "__filename", out.code + "\n; return module.exports;");
  const exp = fn(mod, mod.exports, require, path.dirname(process.argv[3]), process.argv[3]);
  classifyIntent = (exp && exp.classifyIntent) || (mod.exports && mod.exports.classifyIntent);
}
if (typeof classifyIntent !== "function") {
  process.stderr.write("FAIL: classifyIntent could not be loaded; typeof=" + typeof classifyIntent + "\n");
  process.exit(2);
}
const cases = JSON.parse(process.argv[4]);
const out = [];
for (const [q] of cases) {
  const r = classifyIntent(q);
  out.push({ q, chartType: r.chartType, comparisonType: r.comparisonType, confidence: r.confidence });
}
process.stdout.write("__QA_JSON__" + JSON.stringify(out) + "\n");
