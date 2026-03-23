/**
 * 飞书测试用例集 - JSON → 用例集导入
 *
 * 流程：
 *  1. 读取 JSON 测试用例文件
 *  2. 用最小 xmind 占位文件调 xmind/import 创建用例集 → 拿到 work_item_id
 *  3. 将 JSON 按严格模式层级转为飞书 mind_content（带 nodeType）
 *  4. 调 mind/save 写入完整脑图
 *  5. 输出用例集链接
 *
 * 运行: npx tsx tests/feishuImportXmind.ts <json_file_path> [dir_id]
 *
 * 参数：
 *  - json_file_path  必填，符合 TestCaseJSON 结构的 JSON 文件
 *  - dir_id          可选，飞书用例管理导入目录 ID，默认为 LazzaAccount 目录
 *
 * 前置：
 *  - .env 中需配置 FEISHU_PROJECT_KEY
 *  - 首次运行需在弹出的浏览器中完成飞书登录，后续会复用 session
 *
 * 限制：飞书单次上传最多 500 条用例，超出需拆分
 *
 * 关键发现：xmind/import 接口会丢失每个节点的兄弟节点（只保留第一个子节点），
 * 因此必须先创建占位用例集，再通过 mind/save 写入完整树。
 */

import "dotenv/config";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import JSZip from "jszip";
import { chromium } from "playwright";

// ─── 配置 ────────────────────────────────────────────────────────────────────

const PROJECT_KEY = process.env.FEISHU_PROJECT_KEY!;
const CASE_SET_TYPE_KEY = "65f2fed3067c907f0466f016";
const INTERNAL_API_BASE = "https://project.feishu.cn/m-api/v1/builtin_app/test_management";
const CASE_MANAGEMENT_URL =
  "https://project.feishu.cn/research__development/meegoPlg/MII_642BBF6AC6C74001_test_management_use_case_set";
const BROWSER_PROFILE_DIR = path.join(os.homedir(), ".vibeflow", "browser_profile");
const DEFAULT_DIR_ID = "7577242005904542944";

const NODE_TYPE = { CASE_TITLE: 11, PRECONDITION: 12, STEP: 13, EXPECTED: 14 } as const;

// ─── JSON 输入结构 ───────────────────────────────────────────────────────────

interface TestCaseJSON {
  project: string;
  version: string;
  description?: string;
  test_cases: Array<{
    case_id: string;
    case_title: string;
    priority?: string;
    module: string;
    tags?: string[];
    precondition: string;
    test_steps: string[];
    expected_results: string[];
  }>;
}

// ─── 飞书脑图节点结构 ───────────────────────────────────────────────────────

interface MindNode {
  id: string;
  text: Array<{ type: number; text: string }>;
  children?: MindNode[];
  nodeType?: number;
  priority?: number;
}

function mkText(s: string): Array<{ type: number; text: string }> {
  return [{ type: 0, text: s }];
}

let idCounter = 0;
function nextId(): string {
  return `n_${Date.now()}_${idCounter++}`;
}

const PRIORITY_MAP: Record<string, number> = { P0: 1, P1: 2, P2: 3, P3: 4 };

// ─── JSON → 飞书 mind_content ───────────────────────────────────────────────

function jsonToMindContent(data: TestCaseJSON): MindNode[] {
  // 用嵌套 Map 表示多层模块树：key 是当前层名称，value 是 { node, childrenMap }
  interface TreeNode {
    node: MindNode;
    childrenMap: Map<string, TreeNode>;
  }

  const rootMap = new Map<string, TreeNode>();

  // 根据路径数组获取（或创建）最深层的 TreeNode，返回其 node.children（用例列表）
  function getOrCreatePath(parts: string[]): MindNode[] {
    let currentMap = rootMap;
    let parentChildren: MindNode[] | null = null;

    for (const part of parts) {
      if (!currentMap.has(part)) {
        const node: MindNode = { id: nextId(), text: mkText(part), children: [] };
        const treeNode: TreeNode = { node, childrenMap: new Map() };
        currentMap.set(part, treeNode);
        if (parentChildren) parentChildren.push(node);
      }
      const treeNode = currentMap.get(part)!;
      parentChildren = treeNode.node.children!;
      currentMap = treeNode.childrenMap;
    }

    return parentChildren!;
  }

  for (const tc of data.test_cases) {
    // 按 "/" 拆分模块路径为多层
    const parts = tc.module.split("/").map(s => s.trim()).filter(Boolean);

    // 步骤 → 预期结果（一一配对）
    const stepNodes: MindNode[] = tc.test_steps.map((step, i) => ({
      id: nextId(),
      text: mkText(step),
      nodeType: NODE_TYPE.STEP,
      children: [{
        id: nextId(),
        text: mkText(tc.expected_results[i] ?? ""),
        nodeType: NODE_TYPE.EXPECTED,
      }],
    }));

    // 前置条件节点
    const precondNode: MindNode = {
      id: nextId(),
      text: mkText(tc.precondition),
      nodeType: NODE_TYPE.PRECONDITION,
      children: stepNodes,
    };

    // 用例标题节点
    const caseNode: MindNode = {
      id: nextId(),
      text: mkText(tc.case_title),
      nodeType: NODE_TYPE.CASE_TITLE,
      children: [precondNode],
      ...(tc.priority && PRIORITY_MAP[tc.priority] ? { priority: PRIORITY_MAP[tc.priority] } : {}),
    };

    const leafChildren = getOrCreatePath(parts);
    leafChildren.push(caseNode);
  }

  // 返回根层节点列表
  return [...rootMap.values()].map(t => t.node);
}

// ─── 打包最小占位 .xmind ────────────────────────────────────────────────────

async function packPlaceholderXmind(title: string): Promise<Buffer> {
  const zip = new JSZip();
  const content = [{
    id: "sheet1",
    title: "Sheet 1",
    rootTopic: { id: "root", title },
  }];
  zip.file("content.json", JSON.stringify(content));
  zip.file("metadata.json", JSON.stringify({ creator: { name: "vibeflow", version: "1.0" } }));
  zip.file("manifest.json", JSON.stringify({ "file-entries": { "content.json": {}, "metadata.json": {} } }));
  return zip.generateAsync({ type: "nodebuffer" }) as Promise<Buffer>;
}

// ─── 浏览器获取 x-token ─────────────────────────────────────────────────────

async function captureToken(): Promise<string> {
  fs.mkdirSync(BROWSER_PROFILE_DIR, { recursive: true });

  const hasProfile = fs.existsSync(path.join(BROWSER_PROFILE_DIR, "Default"));
  console.log(`   浏览器配置: hasProfile=${hasProfile}, headless=${hasProfile}`);
  const context = await chromium.launchPersistentContext(BROWSER_PROFILE_DIR, {
    headless: hasProfile,
    channel: "chrome",
  });

  try {
    const page = context.pages()[0] || await context.newPage();
    let token = "";

    page.on("request", (req) => {
      const xToken = req.headers()["x-token"];
      if (xToken && !token) {
        token = xToken;
        console.log(`✅ 捕获 x-token: ${token.slice(0, 20)}...`);
      }
    });

    console.log("   导航到用例管理页面...");
    await page.goto(CASE_MANAGEMENT_URL, { waitUntil: "domcontentloaded", timeout: 60_000 });

    await page.waitForTimeout(3_000);
    if (page.url().includes("passport") || page.url().includes("login")) {
      console.log("⏳ 请在浏览器中完成飞书登录...");
    }

    await page.waitForURL(
      (u) => u.pathname.includes("test_management_use_case_set"),
      { timeout: 300_000, waitUntil: "domcontentloaded" },
    );

    await page.waitForTimeout(5_000);
    if (!token) {
      console.log("   等待 token（最多 30 秒）...");
      const deadline = Date.now() + 30_000;
      while (!token && Date.now() < deadline) await page.waitForTimeout(2_000);
    }

    return token;
  } finally {
    await context.close();
  }
}

// ─── 内部 API 封装 ──────────────────────────────────────────────────────────

async function internalGet(endpoint: string, params: Record<string, string>, token: string) {
  const url = new URL(`${INTERNAL_API_BASE}/${endpoint}`);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url.toString(), {
    headers: { "x-token": token, Referer: "https://project.feishu.cn/" },
  });
  return res.json() as Promise<any>;
}

async function internalPost(endpoint: string, body: Record<string, unknown>, token: string) {
  const res = await fetch(`${INTERNAL_API_BASE}/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-token": token, Referer: "https://project.feishu.cn/" },
    body: JSON.stringify(body),
  });
  return res.json() as Promise<any>;
}

// ─── xmind/import 创建占位用例集 ────────────────────────────────────────────

async function createCaseSet(
  title: string,
  token: string,
  dirId: string,
): Promise<number> {
  const xmindBuf = await packPlaceholderXmind(title);

  const url = new URL(`${INTERNAL_API_BASE}/xmind/import`);
  url.searchParams.set("project_key", PROJECT_KEY);
  url.searchParams.set("work_item_type_key", CASE_SET_TYPE_KEY);
  url.searchParams.set("mind_format", "standard");
  url.searchParams.set("target", "online_mind");
  url.searchParams.set("dir_id", dirId);

  const formData = new FormData();
  const fileName = `${title}.xmind`.replace(/\s+/g, "_");
  formData.append("file", new Blob([new Uint8Array(xmindBuf)], { type: "application/octet-stream" }), fileName);

  const res = await fetch(url.toString(), {
    method: "POST",
    headers: { "x-token": token, Referer: "https://project.feishu.cn/" },
    body: formData,
  });

  const json = await res.json() as any;
  if (json?.code !== 0) {
    throw new Error(`创建用例集失败: code=${json?.code} msg=${json?.msg ?? JSON.stringify(json)}`);
  }

  return json.data.case_set_work_item_id;
}

// ─── mind/save 写入完整脑图 ─────────────────────────────────────────────────

async function saveMindContent(
  workItemId: number,
  mindContent: MindNode[],
  token: string,
): Promise<void> {
  const params = {
    project_key: PROJECT_KEY,
    work_item_id: String(workItemId),
    work_item_type_key: CASE_SET_TYPE_KEY,
    mind_type: "1",
  };

  // 先获取 mind_version（乐观锁）
  const queryRes = await internalGet("mind/query", params, token);
  if (queryRes?.code !== 0) {
    throw new Error(`查询脑图失败: code=${queryRes?.code} msg=${queryRes?.msg ?? ""}`);
  }
  const mindVersion: number = queryRes.data.mind_updated_at;

  // 写入
  const saveRes = await internalPost("mind/save", {
    project_key: PROJECT_KEY,
    work_item_id: workItemId,
    work_item_type_key: CASE_SET_TYPE_KEY,
    mind_content: JSON.stringify(mindContent),
    mind_version: mindVersion,
    mind_type: 1,
  }, token);

  if (saveRes?.code !== 0) {
    throw new Error(`保存脑图失败: code=${saveRes?.code} msg=${saveRes?.msg ?? ""}`);
  }
}

// ─── 构建用例集 URL ─────────────────────────────────────────────────────────

function buildCaseSetUrl(workItemId: number): string {
  const parentUrl = encodeURIComponent(
    "/research__development/meegoPlg/MII_642BBF6AC6C74001_test_management_use_case_set",
  );
  return `https://project.feishu.cn/research__development/test_cases_set/detail/${workItemId}?parentUrl=${parentUrl}&openScene=6`;
}

// ─── 主函数 ──────────────────────────────────────────────────────────────────

async function main() {
  const jsonPath = process.argv[2];
  if (!jsonPath) {
    console.error("用法: npx tsx tests/feishuImportXmind.ts <json_file_path> [dir_id]");
    process.exit(1);
  }
  if (!PROJECT_KEY) {
    console.error("❌ 缺少环境变量 FEISHU_PROJECT_KEY");
    process.exit(1);
  }

  const dirId = process.argv[3] ?? DEFAULT_DIR_ID;

  console.log("=".repeat(60));
  console.log("飞书测试用例集 - JSON → 用例集导入");
  console.log("=".repeat(60));

  // ── 第一步：读取 JSON ──
  console.log("\n【第一步】读取 JSON...");
  const raw = JSON.parse(fs.readFileSync(jsonPath, "utf-8")) as TestCaseJSON;
  const rootTitle = raw.version ? `${raw.project} V${raw.version}` : raw.project;
  console.log(`   项目: ${rootTitle}`);
  console.log(`   用例数: ${raw.test_cases.length}`);

  // ── 第二步：获取 token ──
  console.log("\n【第二步】获取 x-token...");
  const token = await captureToken();
  if (!token) throw new Error("无法获取 token，请检查登录状态");

  // ── 第三步：创建占位用例集 ──
  console.log("\n【第三步】创建用例集...");
  const workItemId = await createCaseSet(rootTitle, token, dirId);
  console.log(`✅ 用例集已创建: work_item_id=${workItemId}`);

  // ── 第四步：构建并写入完整脑图 ──
  console.log("\n【第四步】构建严格模式脑图并写入...");
  const mindContent = jsonToMindContent(raw);

  const moduleCount = mindContent.length;
  const caseCount = mindContent.reduce((sum, m) => sum + (m.children?.length ?? 0), 0);
  console.log(`   模块: ${moduleCount}, 用例: ${caseCount}`);

  await saveMindContent(workItemId, mindContent, token);
  console.log("✅ 脑图写入成功");

  // ── 第五步：验证 ──
  console.log("\n【第五步】验证...");
  const verifyRes = await internalGet("mind/query", {
    project_key: PROJECT_KEY,
    work_item_id: String(workItemId),
    work_item_type_key: CASE_SET_TYPE_KEY,
    mind_type: "1",
  }, token);
  console.log(`   严格模式用例数: ${verifyRes.data?.case_cnt}`);

  // ── 输出链接 ──
  const url = buildCaseSetUrl(workItemId);
  console.log("\n" + "=".repeat(60));
  console.log("✅ 导入完成！用例集链接：");
  console.log(url);
  console.log("=".repeat(60));
}

main().catch(console.error);
