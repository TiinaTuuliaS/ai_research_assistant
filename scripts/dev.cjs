// Run both services in this terminal; stop only processes started by this script.
const { spawn } = require("node:child_process");
const net = require("node:net");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const children = [];
let stopping = false;

function checkPort(port) {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", () => reject(new Error(`Portti ${port} on jo käytössä. Pysäytä aiempi palvelin sen terminaalissa (Ctrl+C).`)));
    server.listen(port, () => server.close(resolve));
  });
}

function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  process.exitCode = code;
  for (const child of children) {
    if (!child.pid || child.exitCode !== null) continue;
    if (process.platform === "win32") {
      spawn("taskkill", ["/pid", String(child.pid), "/t", "/f"], { windowsHide: true, stdio: "ignore" });
    } else {
      try { process.kill(-child.pid, "SIGTERM"); } catch { /* Already stopped. */ }
    }
  }
}

function start(script) {
  const child = process.platform === "win32"
    ? spawn("cmd.exe", ["/d", "/s", "/c", `npm run ${script}`], { cwd: root, stdio: "inherit", windowsHide: true })
    : spawn("npm", ["run", script], { cwd: root, stdio: "inherit", detached: true });
  children.push(child);
  child.on("error", error => { console.error(error.message); stop(1); });
  child.on("exit", code => { if (!stopping) stop(code || 0); });
}

process.on("SIGINT", () => stop());
process.on("SIGTERM", () => stop());

async function main() {
  await Promise.all([checkPort(3000), checkPort(8000)]);
  console.log("Frontti: http://localhost:3000\nBackend: http://127.0.0.1:8000/docs\nPysäytä molemmat: Ctrl+C");
  start("backend");
  start("front");
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
