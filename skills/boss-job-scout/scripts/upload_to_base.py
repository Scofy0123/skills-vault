import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


BASE_TOKEN = "Ll50bGx3saIBWEs4T0lca0mjniz"
TABLE_ID = "tbly2p4ZLmj6styh"
DEFAULT_VIEW_ID = "vew2JdAoKw"

TOPIC_RESULTS_FILE = "topic_results.json"
RAW_RESULTS_FILE = "topic_results_raw.json"
DETAILED_RESULTS_FILE = "topic_results_detailed.json"

DETAIL_FIELD_NAME = "详细JD"
STATUS_FIELD_NAME = "抓取状态"
URL_FIELD_NAME = "详情链接"
TITLE_FIELD_NAME = "岗位名称"
COMPANY_FIELD_NAME = "公司"
SCAN_DATE_FIELD_NAME = "抓取日期"

STATUS_JD_FILLED = "JD已回填"
STATUS_JD_FAILED = "JD抓取失败/需重试"

NETWORK_DELAY_MIN = 25
NETWORK_DELAY_MAX = 45
COFFEE_BREAK_EVERY = 5
COFFEE_BREAK_MIN = 60
COFFEE_BREAK_MAX = 120

BROWSER_WARMUP_URL = "https://www.zhipin.com/web/geek/job"
MIN_JD_LENGTH = 80

LOGIN_WALL_MARKERS = (
    "注册BOSS直聘",
    "发送验证码",
    "登录/注册",
    "微信极速注册",
    "请稍候",
    "正在加载中",
)

JD_START_MARKERS = (
    "职位描述",
    "岗位职责",
    "工作职责",
    "工作内容",
)

JD_END_MARKERS = (
    "公司介绍",
    "工商信息",
    "职位发布者",
    "工作地址",
    "公司地址",
    "相关推荐",
    "看过该职位的人还看了",
    "更多职位",
    "认证资质",
    "竞争力分析",
    "BOSS 安全提示",
)

JD_QUALITY_MARKERS = (
    "职责",
    "要求",
    "任职",
    "职位描述",
    "岗位职责",
    "工作职责",
    "工作内容",
    "任职资格",
    "我们在找什么样的人",
)

BROWSER_FETCH_JS = """
import { browserSession, getBrowserFactory } from '/Users/scofy/.nvm/versions/node/v22.19.0/lib/node_modules/@jackwener/opencli/dist/src/runtime.js';

const BrowserFactory = getBrowserFactory('boss');
const targetUrl = process.env.BOSS_DETAIL_URL;

const result = await browserSession(BrowserFactory, async (page) => {
  await page.goto(process.env.BOSS_WARMUP_URL || 'https://www.zhipin.com/web/geek/job');
  await page.wait({ time: 2 });
  await page.goto(targetUrl, { waitUntil: 'none' });

  let snapshot = null;
  for (const waitSeconds of [2, 2, 3]) {
    await page.wait({ time: waitSeconds });
    snapshot = await page.evaluate(`() => ({
      href: location.href,
      title: document.title,
      text: document.body ? document.body.innerText : ''
    })`);
    if (snapshot && snapshot.text && snapshot.text.length >= 300) {
      break;
    }
  }

  return snapshot;
}, { workspace: 'site:boss-detail-fallback' });

console.log(JSON.stringify(result));
""".strip()


@dataclass
class BackfillTask:
    url: str
    record_ids: list[str]
    source: str
    title: str = ""
    company: str = ""
    jd_text: str | None = None
    security_id: str | None = None


@dataclass
class TaskOutcome:
    success: bool
    catastrophic: bool = False
    jd_text: str | None = None
    error: str = ""


def run_cmd(cmd, env=None):
    shell = isinstance(cmd, str)
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"Error executing: {cmd}\nStderr: {result.stderr}")
        return None

    stdout = (result.stdout or "").strip()
    if not stdout:
        return ""

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout

    if isinstance(payload, dict) and payload.get("ok") is False:
        print(f"Lark API Error: {payload}")
    return payload


def load_json_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_optional_json_file(path):
    file_path = Path(path)
    if not file_path.exists():
        return None
    return load_json_file(file_path)


def choose_input_data(topic_results, detailed_results):
    if detailed_results and detailed_results.get("results"):
        return detailed_results
    return topic_results


def build_full_url(url):
    if not url:
        return ""
    return url if url.startswith("http") else "https://www.zhipin.com" + url


def normalize_multiline_text(text):
    if not text:
        return ""

    lines = []
    last_blank = False
    for raw_line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            if lines and not last_blank:
                lines.append("")
            last_blank = True
            continue
        lines.append(line)
        last_blank = False

    return "\n".join(lines).strip()


def is_valid_jd_text(text):
    normalized = normalize_multiline_text(text)
    if len(normalized) < MIN_JD_LENGTH:
        return False
    return any(marker in normalized for marker in JD_QUALITY_MARKERS)


def build_record_json(item, scan_date):
    record_json = {
        TITLE_FIELD_NAME: str(item.get("name", "Unknown")),
        "薪资": str(item.get("salary", "Unknown")),
        COMPANY_FIELD_NAME: str(item.get("company", "Unknown")),
        "关键词": str(item.get("_query", "Unknown")),
        STATUS_FIELD_NAME: "新数据",
        "标签/要求": str(item.get("summary", "Unknown")),
        URL_FIELD_NAME: build_full_url(item.get("url", "")),
    }

    if scan_date is not None:
        record_json[SCAN_DATE_FIELD_NAME] = str(scan_date)

    detailed_description = normalize_multiline_text(str(item.get("detailed_description", "")).strip())
    if detailed_description:
        record_json[DETAIL_FIELD_NAME] = detailed_description

    return record_json


def sort_results(results):
    return sorted(results, key=lambda x: (x.get("_query", ""), x.get("salary", ""), x.get("name", "")))


def list_fields():
    cmd = [
        "lark-cli",
        "base",
        "+field-list",
        "--base-token",
        BASE_TOKEN,
        "--table-id",
        TABLE_ID,
        "--as",
        "user",
    ]
    response = run_cmd(cmd)
    if not response or not response.get("ok"):
        return []
    return response.get("data", {}).get("fields", [])


def ensure_text_field(field_name):
    existing_field_names = {field.get("name") for field in list_fields()}
    if field_name in existing_field_names:
        return False

    field_json = {
        "name": field_name,
        "type": "text",
        "description": "Boss 职位详情 JD 正文",
    }
    cmd = [
        "lark-cli",
        "base",
        "+field-create",
        "--base-token",
        BASE_TOKEN,
        "--table-id",
        TABLE_ID,
        "--json",
        json.dumps(field_json, ensure_ascii=False),
        "--as",
        "user",
    ]
    response = run_cmd(cmd)
    return bool(response and response.get("ok"))


def parse_record_list_response(response):
    data = response.get("data", {})
    field_names = data.get("fields", [])
    rows = data.get("data", [])
    record_ids = data.get("record_id_list", [])

    parsed = []
    for record_id, row in zip(record_ids, rows):
        parsed.append(
            {
                "record_id": record_id,
                "fields": {
                    field_name: row[index] if index < len(row) else None
                    for index, field_name in enumerate(field_names)
                },
            }
        )
    return parsed, data.get("has_more", False)


def list_existing_records():
    offset = 0
    records = []

    while True:
        cmd = [
            "lark-cli",
            "base",
            "+record-list",
            "--base-token",
            BASE_TOKEN,
            "--table-id",
            TABLE_ID,
            "--limit",
            "200",
            "--offset",
            str(offset),
            "--as",
            "user",
        ]
        response = run_cmd(cmd)
        if not response or not response.get("ok"):
            break

        page_records, has_more = parse_record_list_response(response)
        records.extend(page_records)

        if not has_more or not page_records:
            break
        offset += len(page_records)

    return records


def list_view_records(view_id, field_names):
    offset = 0
    records = []

    while True:
        cmd = [
            "lark-cli",
            "base",
            "+record-list",
            "--base-token",
            BASE_TOKEN,
            "--table-id",
            TABLE_ID,
            "--view-id",
            view_id,
            "--offset",
            str(offset),
            "--limit",
            "200",
            "--as",
            "user",
        ]
        for field_name in field_names:
            cmd.extend(["--field-id", field_name])

        response = run_cmd(cmd)
        if not response or not response.get("ok"):
            break

        page_records, has_more = parse_record_list_response(response)
        records.extend(page_records)

        if not has_more or not page_records:
            break
        offset += len(page_records)

    return records


def find_matching_record_id(item, scan_date, existing_records):
    full_url = build_full_url(item.get("url", ""))
    for record in existing_records:
        fields = record.get("fields", {})
        if fields.get(URL_FIELD_NAME) == full_url and str(fields.get(SCAN_DATE_FIELD_NAME, "")) == str(scan_date):
            return record.get("record_id")
    return None


def upsert_record(record_json, record_id=None):
    cmd = [
        "lark-cli",
        "base",
        "+record-upsert",
        "--base-token",
        BASE_TOKEN,
        "--table-id",
        TABLE_ID,
        "--json",
        json.dumps(record_json, ensure_ascii=False),
        "--as",
        "user",
    ]
    if record_id:
        cmd.extend(["--record-id", record_id])
    return run_cmd(cmd)


def sequential_update_records(record_ids, patch):
    for record_id in record_ids:
        response = upsert_record(record_json=patch, record_id=record_id)
        if not response or not response.get("ok"):
            return False
        time.sleep(0.1)
    return True


def batch_update_records(record_ids, patch):
    payload = {
        "record_id_list": record_ids,
        "patch": patch,
    }
    cmd = [
        "lark-cli",
        "base",
        "+record-batch-update",
        "--base-token",
        BASE_TOKEN,
        "--table-id",
        TABLE_ID,
        "--json",
        json.dumps(payload, ensure_ascii=False),
        "--as",
        "user",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    combined = "\n".join(part for part in (stdout, stderr) if part)

    if result.returncode == 0:
        try:
            payload = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            payload = {}
        if payload.get("ok"):
            return True
        combined = "\n".join(part for part in (combined, json.dumps(payload, ensure_ascii=False)) if part)

    if "800004135" in combined or "OpenAPIBatchUpdateRecords limited" in combined:
        print("Batch update limited by Base API. Falling back to per-record upsert.")
        return sequential_update_records(record_ids=record_ids, patch=patch)

    if combined:
        print(f"Batch update failed for {record_ids}: {combined}")
    return False


def load_input_data():
    topic_results = load_json_file(TOPIC_RESULTS_FILE)
    detailed_results = load_optional_json_file(DETAILED_RESULTS_FILE)
    return choose_input_data(topic_results=topic_results, detailed_results=detailed_results)


def sync_records(data):
    scan_date = data.get("scan_date", "Unknown Date")
    sorted_results = sort_results(data.get("results", []))

    if any(str(item.get("detailed_description", "")).strip() for item in sorted_results):
        created_field = ensure_text_field(DETAIL_FIELD_NAME)
        if created_field:
            print(f"Created field: {DETAIL_FIELD_NAME}")

    existing_records = list_existing_records()

    print(f"Preparing to sync {len(sorted_results)} records...")
    for idx, item in enumerate(sorted_results):
        record_json = build_record_json(item=item, scan_date=scan_date)
        record_id = find_matching_record_id(item=item, scan_date=scan_date, existing_records=existing_records)
        res = upsert_record(record_json=record_json, record_id=record_id)
        if record_id and res and res.get("ok"):
            print(f"Updated {idx + 1}/{len(sorted_results)}")
        elif res and res.get("ok"):
            print(f"Inserted {idx + 1}/{len(sorted_results)}")
        else:
            print(f"Failed to sync {record_json.get(TITLE_FIELD_NAME)}")
        time.sleep(0.1)


def iter_result_items(payload):
    if not payload:
        return []
    results = payload.get("results")
    if isinstance(results, list):
        return results
    if isinstance(payload, list):
        return payload
    return []


def build_detailed_cache():
    cache = {}
    payload = load_optional_json_file(DETAILED_RESULTS_FILE)
    for item in iter_result_items(payload):
        url = build_full_url(item.get("url", ""))
        detailed_description = normalize_multiline_text(item.get("detailed_description", ""))
        if url and detailed_description:
            cache[url] = detailed_description
    return cache


def build_security_id_cache():
    cache = {}
    for payload in (
        load_optional_json_file(RAW_RESULTS_FILE),
        load_optional_json_file(DETAILED_RESULTS_FILE),
    ):
        for item in iter_result_items(payload):
            url = build_full_url(item.get("url", ""))
            security_id = str(item.get("security_id", "")).strip()
            if url and security_id:
                cache[url] = security_id
    return cache


def build_backfill_tasks(records, detailed_cache, security_id_cache, include_failed=False):
    grouped = defaultdict(list)
    for record in records:
        url = build_full_url(record["fields"].get(URL_FIELD_NAME, ""))
        if not url:
            continue
        grouped[url].append(record)

    tasks = []
    for url, group in grouped.items():
        missing_record_ids = []
        existing_jd = ""
        title = ""
        company = ""
        for record in group:
            fields = record["fields"]
            title = title or str(fields.get(TITLE_FIELD_NAME, "") or "")
            company = company or str(fields.get(COMPANY_FIELD_NAME, "") or "")
            current_jd = normalize_multiline_text(fields.get(DETAIL_FIELD_NAME, "") or "")
            current_status = str(fields.get(STATUS_FIELD_NAME, "") or "").strip()
            if current_jd and not existing_jd:
                existing_jd = current_jd
            if not include_failed and not current_jd and current_status == STATUS_JD_FAILED:
                continue
            if not current_jd:
                missing_record_ids.append(record["record_id"])

        if not missing_record_ids:
            continue

        if existing_jd:
            tasks.append(
                BackfillTask(
                    url=url,
                    record_ids=missing_record_ids,
                    source="copy",
                    title=title,
                    company=company,
                    jd_text=existing_jd,
                )
            )
            continue

        cached_jd = detailed_cache.get(url)
        if cached_jd:
            tasks.append(
                BackfillTask(
                    url=url,
                    record_ids=missing_record_ids,
                    source="cache",
                    title=title,
                    company=company,
                    jd_text=cached_jd,
                )
            )
            continue

        security_id = security_id_cache.get(url)
        tasks.append(
            BackfillTask(
                url=url,
                record_ids=missing_record_ids,
                source="security" if security_id else "browser",
                title=title,
                company=company,
                security_id=security_id,
            )
        )

    return tasks


def summarize_tasks(tasks):
    summary = defaultdict(int)
    for task in tasks:
        summary[task.source] += len(task.record_ids)
    return dict(summary)


def select_canary_tasks(tasks):
    selected = []
    seen_urls = set()
    for source in ("copy", "security", "browser"):
        task = next((item for item in tasks if item.source == source and item.url not in seen_urls), None)
        if task:
            selected.append(task)
            seen_urls.add(task.url)
    return selected


def extract_jd_from_page_text(text):
    normalized = normalize_multiline_text(text)
    if not normalized:
        return ""

    head = normalized[:500]
    if any(marker in head for marker in LOGIN_WALL_MARKERS):
        return ""

    start_positions = [normalized.find(marker) for marker in JD_START_MARKERS if normalized.find(marker) != -1]
    if not start_positions:
        return ""

    content = normalized[min(start_positions):]

    end_positions = [content.find(marker) for marker in JD_END_MARKERS if content.find(marker) > 0]
    if end_positions:
        content = content[: min(end_positions)]

    content = normalize_multiline_text(content)
    if not is_valid_jd_text(content):
        return ""
    return content


def classify_browser_failure(snapshot):
    href = str(snapshot.get("href", "") or "")
    title = str(snapshot.get("title", "") or "")
    text = normalize_multiline_text(snapshot.get("text", "") or "")
    head = "\n".join(part for part in (title, href, text[:800]) if part)

    if href == "about:blank":
        return True, "browser navigation landed on about:blank"
    if "security-check" in href or "请稍候" in title:
        return True, f"security page detected: {href or title}"
    if any(marker in head for marker in LOGIN_WALL_MARKERS):
        return True, "login wall or security page detected"
    return False, ""


def fetch_jd_via_security_id(task):
    if not task.security_id:
        return TaskOutcome(success=False, error="missing security_id")

    cmd = [
        "opencli",
        "boss",
        "detail",
        task.security_id,
        "--format",
        "json",
    ]
    payload = run_cmd(cmd)
    if payload is None:
        return TaskOutcome(success=False, catastrophic=True, error="opencli boss detail failed")
    if isinstance(payload, str):
        if "Network Error" in payload or "200404" in payload:
            return TaskOutcome(success=False, catastrophic=True, error=payload)
        return TaskOutcome(success=False, error="unexpected string payload from boss detail")
    if not isinstance(payload, list) or not payload:
        return TaskOutcome(success=False, error="empty boss detail payload")

    job = payload[0]
    returned_url = build_full_url(job.get("url", ""))
    if returned_url and returned_url != task.url:
        return TaskOutcome(success=False, error=f"url mismatch: expected {task.url}, got {returned_url}")

    jd_text = normalize_multiline_text(job.get("description", ""))
    if not is_valid_jd_text(jd_text):
        return TaskOutcome(success=False, error="boss detail returned invalid JD text")
    return TaskOutcome(success=True, jd_text=jd_text)


def fetch_browser_snapshot(url):
    env = os.environ.copy()
    env["BOSS_DETAIL_URL"] = url
    env["BOSS_WARMUP_URL"] = BROWSER_WARMUP_URL

    result = subprocess.run(
        ["node", "--input-type=module", "-e", BROWSER_FETCH_JS],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        combined = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        return None, combined or "node browser fallback failed"

    stdout = (result.stdout or "").strip()
    if not stdout:
        return None, "empty browser fallback payload"

    try:
        return json.loads(stdout), ""
    except json.JSONDecodeError:
        return None, stdout


def fetch_jd_via_browser(task):
    snapshot, error = fetch_browser_snapshot(task.url)
    if snapshot is None:
        catastrophic = "Network Error" in error or "200404" in error
        return TaskOutcome(success=False, catastrophic=catastrophic, error=error)

    catastrophic, reason = classify_browser_failure(snapshot)
    if catastrophic:
        return TaskOutcome(success=False, catastrophic=True, error=reason)

    jd_text = extract_jd_from_page_text(snapshot.get("text", ""))
    if not jd_text:
        return TaskOutcome(success=False, error="browser fallback extracted empty JD text")
    return TaskOutcome(success=True, jd_text=jd_text)


def mark_task_success(task, jd_text):
    patch = {
        DETAIL_FIELD_NAME: jd_text,
        STATUS_FIELD_NAME: STATUS_JD_FILLED,
    }
    return batch_update_records(task.record_ids, patch)


def mark_task_failed(task):
    patch = {
        STATUS_FIELD_NAME: STATUS_JD_FAILED,
    }
    return batch_update_records(task.record_ids, patch)


def confirm_session_ready(assume_ready):
    if assume_ready:
        print("Session precheck overridden via --assume-session-ready.")
        return True

    prompt = (
        "在正式下钻猎场之前，请确认：你今天已在 Chrome 中正常刷新过 BOSS 直聘，"
        "且如果刚触发过滑块验证码，已经等待了约 15 分钟冷却期。输入 yes 继续："
    )
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes", "ok", "ready", "是"}


def sleep_after_network_request(network_count):
    if network_count % COFFEE_BREAK_EVERY == 0:
        delay = random.randint(COFFEE_BREAK_MIN, COFFEE_BREAK_MAX)
        print(f" -> [咖啡防封机制] 已连续处理 {network_count} 个联网目标，强制休眠 {delay} 秒。")
    else:
        delay = random.randint(NETWORK_DELAY_MIN, NETWORK_DELAY_MAX)
        print(f" -> [大波浪避险机制] 联网目标间隔休眠 {delay} 秒。")
    time.sleep(delay)


def run_task(task, network_count):
    print(f"[{task.source}] {task.title or '未知岗位'} @ {task.company or '未知公司'}")
    print(f" -> URL: {task.url}")
    print(f" -> 待回填记录数: {len(task.record_ids)}")

    if task.source in {"copy", "cache"}:
        jd_text = normalize_multiline_text(task.jd_text or "")
        if not jd_text:
            return TaskOutcome(success=False, error=f"{task.source} source missing JD text")
        if mark_task_success(task, jd_text):
            return TaskOutcome(success=True, jd_text=jd_text)
        return TaskOutcome(success=False, error="failed to persist non-network backfill")

    if task.source == "security":
        outcome = fetch_jd_via_security_id(task)
    else:
        outcome = fetch_jd_via_browser(task)

    if outcome.success:
        if mark_task_success(task, outcome.jd_text or ""):
            return outcome
        return TaskOutcome(success=False, error="failed to persist successful network backfill")

    mark_task_failed(task)
    return outcome


def execute_backfill(tasks, canary_only=False):
    completed_urls = set()
    network_count = 0
    stop_reason = ""

    canary_tasks = select_canary_tasks(tasks)
    remaining_tasks = [task for task in tasks if task.url not in {item.url for item in canary_tasks}]

    if canary_tasks:
        print("Running canary tasks before full backfill...")
    for index, task in enumerate(canary_tasks):
        uses_network = task.source in {"security", "browser"}
        if uses_network:
            network_count += 1
        outcome = run_task(task, network_count)
        completed_urls.add(task.url)
        if not outcome.success:
            print(f" -> Canary failed: {outcome.error}")
            if outcome.catastrophic:
                stop_reason = outcome.error or "catastrophic failure during canary"
            else:
                stop_reason = outcome.error or "canary validation failed"
            break
        if uses_network:
            pending_network = any(
                item.source in {"security", "browser"}
                for item in canary_tasks[index + 1 :] + ([] if canary_only else remaining_tasks)
            )
            if pending_network:
                sleep_after_network_request(network_count)

    if stop_reason or canary_only:
        return {
            "completed_urls": completed_urls,
            "network_count": network_count,
            "stop_reason": stop_reason,
        }

    non_network_tasks = [task for task in remaining_tasks if task.source in {"copy", "cache"}]
    network_tasks = [task for task in remaining_tasks if task.source in {"security", "browser"}]

    for task in non_network_tasks:
        outcome = run_task(task, network_count)
        completed_urls.add(task.url)
        if not outcome.success:
            stop_reason = outcome.error or "non-network backfill failed"
            break

    if stop_reason:
        return {
            "completed_urls": completed_urls,
            "network_count": network_count,
            "stop_reason": stop_reason,
        }

    random.shuffle(network_tasks)
    for index, task in enumerate(network_tasks):
        network_count += 1
        outcome = run_task(task, network_count)
        completed_urls.add(task.url)

        if not outcome.success and outcome.catastrophic:
            stop_reason = outcome.error or "catastrophic network failure"
            break

        if index < len(network_tasks) - 1 and not stop_reason:
            sleep_after_network_request(network_count)

    return {
        "completed_urls": completed_urls,
        "network_count": network_count,
        "stop_reason": stop_reason,
    }


def backfill_missing_jd(view_id, assume_session_ready=False, canary_only=False, retry_failed=False):
    ensure_text_field(DETAIL_FIELD_NAME)

    field_names = [
        TITLE_FIELD_NAME,
        COMPANY_FIELD_NAME,
        URL_FIELD_NAME,
        DETAIL_FIELD_NAME,
        STATUS_FIELD_NAME,
    ]
    records = list_view_records(view_id=view_id, field_names=field_names)
    detailed_cache = build_detailed_cache()
    security_id_cache = build_security_id_cache()

    tasks = build_backfill_tasks(
        records=records,
        detailed_cache=detailed_cache,
        security_id_cache=security_id_cache,
        include_failed=retry_failed,
    )

    print(f"Found {len(records)} records in view {view_id}.")
    print(f"Missing-JD URL groups queued: {len(tasks)}")
    print(f"Task summary: {summarize_tasks(tasks)}")

    if not tasks:
        print("No missing JD records found. Nothing to backfill.")
        return

    needs_network = any(task.source in {"security", "browser"} for task in tasks)
    if needs_network and not confirm_session_ready(assume_ready=assume_session_ready):
        raise SystemExit("Session precheck not confirmed. Backfill paused.")

    result = execute_backfill(tasks=tasks, canary_only=canary_only)
    if result["stop_reason"]:
        print(f"Backfill stopped early: {result['stop_reason']}")

    print(
        "Backfill summary:",
        {
            "completed_urls": len(result["completed_urls"]),
            "network_requests": result["network_count"],
            "stopped": bool(result["stop_reason"]),
        },
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Sync BOSS scout outputs into Base or backfill missing JD rows.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("sync", help="Sync topic_results*.json into Base (default behavior).")

    backfill_parser = subparsers.add_parser("backfill-missing-jd", help="Backfill empty 详细JD rows in an existing Base view.")
    backfill_parser.add_argument("--view-id", default=DEFAULT_VIEW_ID, help="Target Base view ID.")
    backfill_parser.add_argument("--assume-session-ready", action="store_true", help="Skip the interactive BOSS session confirmation prompt.")
    backfill_parser.add_argument("--canary-only", action="store_true", help="Run only the canary subset.")
    backfill_parser.add_argument("--retry-failed", action="store_true", help="Include rows already marked as JD抓取失败/需重试.")

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.command == "backfill-missing-jd":
        backfill_missing_jd(
            view_id=args.view_id,
            assume_session_ready=args.assume_session_ready,
            canary_only=args.canary_only,
            retry_failed=args.retry_failed,
        )
        return

    data = load_input_data()
    sync_records(data)
    print("All Done!")


if __name__ == "__main__":
    main(sys.argv[1:])
