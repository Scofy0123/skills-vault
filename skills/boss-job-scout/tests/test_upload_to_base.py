import importlib.util
import json
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest import mock


MODULE_PATH = Path("/Users/scofy/.agents/skills/boss-job-scout/scripts/upload_to_base.py")


def load_module():
    spec = importlib.util.spec_from_file_location("upload_to_base", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None

    fake_topic_results = json.dumps({"scan_date": "2026-04-22 09:06", "results": []}, ensure_ascii=False)

    with mock.patch("builtins.open", mock.mock_open(read_data=fake_topic_results)):
        with mock.patch("time.sleep", return_value=None):
            with mock.patch(
                "subprocess.run",
                return_value=CompletedProcess(args="noop", returncode=0, stdout='{"ok": true}', stderr=""),
            ):
                spec.loader.exec_module(module)
    return module


class UploadToBaseBehaviorTests(unittest.TestCase):
    def test_choose_input_data_prefers_detailed_results_when_present(self):
        module = load_module()

        topic_results = {"scan_date": "2026-04-22 09:06", "results": [{"name": "浅层结果"}]}
        detailed_results = {"scan_date": "2026-04-22 09:06", "results": [{"name": "深度结果", "detailed_description": "完整JD"}]}

        chosen = module.choose_input_data(topic_results=topic_results, detailed_results=detailed_results)

        self.assertEqual(chosen["results"][0]["name"], "深度结果")

    def test_build_record_json_includes_detailed_jd(self):
        module = load_module()

        item = {
            "name": "AI产品经理-Claw",
            "salary": "60-90K·24薪",
            "company": "某大型知名互联网公司",
            "_query": "AI产品经理",
            "summary": "需要掌握 Agent 与增长设计",
            "url": "https://www.zhipin.com/job_detail/test.html",
            "detailed_description": "这里是完整 JD 正文",
        }

        record = module.build_record_json(item=item, scan_date="2026-04-22 09:06")

        self.assertEqual(record["岗位名称"], "AI产品经理-Claw")
        self.assertEqual(record["详情链接"], "https://www.zhipin.com/job_detail/test.html")
        self.assertEqual(record["详细JD"], "这里是完整 JD 正文")

    def test_find_matching_record_id_prefers_same_scan_date(self):
        module = load_module()

        item = {"url": "https://www.zhipin.com/job_detail/test.html"}
        existing_records = [
            {
                "record_id": "rec_old",
                "fields": {
                    "详情链接": "https://www.zhipin.com/job_detail/test.html",
                    "抓取日期": "2026-04-15 10:18",
                },
            },
            {
                "record_id": "rec_latest",
                "fields": {
                    "详情链接": "https://www.zhipin.com/job_detail/test.html",
                    "抓取日期": "2026-04-22 09:06",
                },
            },
        ]

        record_id = module.find_matching_record_id(item=item, scan_date="2026-04-22 09:06", existing_records=existing_records)

        self.assertEqual(record_id, "rec_latest")

    def test_build_backfill_tasks_prefers_copy_then_cache_then_security_then_browser(self):
        module = load_module()

        records = [
            {
                "record_id": "rec_copy_missing",
                "fields": {
                    "岗位名称": "AI Agent产品经理",
                    "公司": "测试公司A",
                    "详情链接": "https://www.zhipin.com/job_detail/copy.html",
                    "详细JD": None,
                    "抓取状态": "新数据",
                },
            },
            {
                "record_id": "rec_copy_filled",
                "fields": {
                    "岗位名称": "AI Agent产品经理",
                    "公司": "测试公司A",
                    "详情链接": "https://www.zhipin.com/job_detail/copy.html",
                    "详细JD": "岗位职责\n1. 负责 Agent 方案设计\n任职要求\n1. 熟悉 LLM。",
                    "抓取状态": "新数据",
                },
            },
            {
                "record_id": "rec_cache",
                "fields": {
                    "岗位名称": "AI产品经理",
                    "公司": "测试公司B",
                    "详情链接": "https://www.zhipin.com/job_detail/cache.html",
                    "详细JD": "",
                    "抓取状态": "新数据",
                },
            },
            {
                "record_id": "rec_security",
                "fields": {
                    "岗位名称": "AI产品运营",
                    "公司": "测试公司C",
                    "详情链接": "https://www.zhipin.com/job_detail/security.html",
                    "详细JD": "",
                    "抓取状态": "新数据",
                },
            },
            {
                "record_id": "rec_browser",
                "fields": {
                    "岗位名称": "AI Agent工程师",
                    "公司": "测试公司D",
                    "详情链接": "https://www.zhipin.com/job_detail/browser.html",
                    "详细JD": "",
                    "抓取状态": "新数据",
                },
            },
        ]

        tasks = module.build_backfill_tasks(
            records=records,
            detailed_cache={
                "https://www.zhipin.com/job_detail/cache.html": "职位描述\n负责缓存命中的 JD。\n任职要求\n了解 Agent。",
            },
            security_id_cache={
                "https://www.zhipin.com/job_detail/security.html": "sec-123",
            },
        )

        source_by_url = {task.url: task.source for task in tasks}

        self.assertEqual(source_by_url["https://www.zhipin.com/job_detail/copy.html"], "copy")
        self.assertEqual(source_by_url["https://www.zhipin.com/job_detail/cache.html"], "cache")
        self.assertEqual(source_by_url["https://www.zhipin.com/job_detail/security.html"], "security")
        self.assertEqual(source_by_url["https://www.zhipin.com/job_detail/browser.html"], "browser")

    def test_build_backfill_tasks_skips_failed_rows_unless_retry_requested(self):
        module = load_module()

        records = [
            {
                "record_id": "rec_failed",
                "fields": {
                    "岗位名称": "AI agent产品负责人",
                    "公司": "测试公司E",
                    "详情链接": "https://www.zhipin.com/job_detail/failed.html",
                    "详细JD": "",
                    "抓取状态": "JD抓取失败/需重试",
                },
            },
            {
                "record_id": "rec_browser",
                "fields": {
                    "岗位名称": "AI Agent工程师",
                    "公司": "测试公司D",
                    "详情链接": "https://www.zhipin.com/job_detail/browser.html",
                    "详细JD": "",
                    "抓取状态": "新数据",
                },
            },
        ]

        default_tasks = module.build_backfill_tasks(
            records=records,
            detailed_cache={},
            security_id_cache={},
        )
        retry_tasks = module.build_backfill_tasks(
            records=records,
            detailed_cache={},
            security_id_cache={},
            include_failed=True,
        )

        self.assertEqual([task.url for task in default_tasks], ["https://www.zhipin.com/job_detail/browser.html"])
        self.assertEqual(
            sorted(task.url for task in retry_tasks),
            sorted(
                [
                    "https://www.zhipin.com/job_detail/browser.html",
                    "https://www.zhipin.com/job_detail/failed.html",
                ]
            ),
        )

    def test_extract_jd_from_page_text_trims_noise_sections(self):
        module = load_module()

        page_text = """
        首页
        搜索
        职位描述
        负责 AI Agent 工作流设计与交付，推动复杂业务场景中的任务拆解、工具调用、记忆策略与评测闭环。
        需要结合真实业务流程设计可观测、可验证、可持续优化的智能体执行路径。
        任职要求
        1. 熟悉大模型应用。
        2. 有产品落地经验。
        3. 能独立推进跨团队协作，并对效果、成本与稳定性负责。
        认证资质
        人力资源服务许可证
        看过该职位的人还看了
        其它岗位
        """

        extracted = module.extract_jd_from_page_text(page_text)

        self.assertIn("职位描述", extracted)
        self.assertIn("任职要求", extracted)
        self.assertNotIn("认证资质", extracted)
        self.assertNotIn("看过该职位的人还看了", extracted)

    def test_sleep_after_network_request_uses_expected_ranges(self):
        module = load_module()

        with mock.patch.object(module.random, "randint", side_effect=[33, 88]) as randint_mock:
            with mock.patch.object(module.time, "sleep", return_value=None) as sleep_mock:
                module.sleep_after_network_request(1)
                module.sleep_after_network_request(5)

        self.assertEqual(randint_mock.call_args_list[0].args, (module.NETWORK_DELAY_MIN, module.NETWORK_DELAY_MAX))
        self.assertEqual(randint_mock.call_args_list[1].args, (module.COFFEE_BREAK_MIN, module.COFFEE_BREAK_MAX))
        self.assertEqual(sleep_mock.call_args_list[0].args, (33,))
        self.assertEqual(sleep_mock.call_args_list[1].args, (88,))

    def test_execute_backfill_stops_after_catastrophic_network_failure(self):
        module = load_module()

        tasks = [
            module.BackfillTask(
                url="https://www.zhipin.com/job_detail/security.html",
                record_ids=["rec_security"],
                source="security",
                title="AI产品运营",
                company="测试公司C",
                security_id="sec-123",
            ),
            module.BackfillTask(
                url="https://www.zhipin.com/job_detail/browser.html",
                record_ids=["rec_browser"],
                source="browser",
                title="AI Agent工程师",
                company="测试公司D",
            ),
        ]

        with mock.patch.object(
            module,
            "run_task",
            return_value=module.TaskOutcome(success=False, catastrophic=True, error="Network Error"),
        ) as run_task_mock:
            with mock.patch.object(module, "sleep_after_network_request", return_value=None):
                result = module.execute_backfill(tasks=tasks, canary_only=False)

        self.assertEqual(run_task_mock.call_count, 1)
        self.assertEqual(result["stop_reason"], "Network Error")
        self.assertEqual(result["completed_urls"], {"https://www.zhipin.com/job_detail/security.html"})

    def test_batch_update_records_falls_back_to_sequential_upsert_when_limited(self):
        module = load_module()

        limited_result = CompletedProcess(
            args="lark-cli base +record-batch-update",
            returncode=1,
            stdout="",
            stderr='{"ok": false, "error": {"code": 800004135, "message": "the method：OpenAPIBatchUpdateRecords limited"}}',
        )

        with mock.patch.object(module.subprocess, "run", return_value=limited_result):
            with mock.patch.object(module, "upsert_record", return_value={"ok": True}) as upsert_mock:
                with mock.patch.object(module.time, "sleep", return_value=None):
                    ok = module.batch_update_records(["rec1", "rec2"], {"抓取状态": "JD已回填"})

        self.assertTrue(ok)
        self.assertEqual(upsert_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
