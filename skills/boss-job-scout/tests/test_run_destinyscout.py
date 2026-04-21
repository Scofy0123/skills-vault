import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest import mock


MODULE_PATH = Path("/Users/scofy/.agents/skills/boss-job-scout/scripts/run_destinyscout.py")


def load_module():
    spec = importlib.util.spec_from_file_location("run_destinyscout", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RunDestinyScoutPersistenceTests(unittest.TestCase):
    def test_persists_raw_results_before_filtering_when_later_query_fails(self):
        module = load_module()

        config = {
            "name": "BOSS岗位监控",
            "global_settings": {
                "city": "上海",
                "experience": "",
                "degree": "本科",
                "opencli_salary": "50K以上",
                "min_salary_k": 50,
            },
            "channels": {
                "boss_track_01": {
                    "enabled": True,
                    "query": "AI Agent",
                    "limit": 15,
                },
                "boss_track_02": {
                    "enabled": True,
                    "query": "AI产品经理",
                    "limit": 15,
                },
            },
        }

        first_query_result = [
            {
                "name": "资深 AI Agent 工程师",
                "salary": "30-40K",
                "company": "测试公司",
                "url": "https://example.com/job/1",
                "skills": "Python,Agent,LLM",
            }
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            config_path = os.path.join(tempdir, "config.json")
            filtered_path = os.path.join(tempdir, "topic_results.json")
            raw_path = os.path.join(tempdir, "topic_results_raw.json")

            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump(config, handle, ensure_ascii=False)

            module.CONFIG_FILE = config_path
            module.OUTPUT_FILE = filtered_path

            current_dir = os.getcwd()
            os.chdir(tempdir)
            try:
                with mock.patch.object(module.random, "shuffle", side_effect=lambda items: None):
                    with mock.patch.object(module.time, "sleep", return_value=None):
                        with mock.patch.object(
                            module.subprocess,
                            "run",
                            side_effect=[
                                CompletedProcess(
                                    args="opencli boss search 'AI Agent'",
                                    returncode=0,
                                    stdout=json.dumps(first_query_result, ensure_ascii=False),
                                    stderr="",
                                ),
                                CompletedProcess(
                                    args="opencli boss search 'AI产品经理'",
                                    returncode=1,
                                    stdout="",
                                    stderr="Error: Network Error",
                                ),
                            ],
                        ):
                            module.run_scout()
            finally:
                os.chdir(current_dir)

            with open(filtered_path, "r", encoding="utf-8") as handle:
                filtered_data = json.load(handle)

            self.assertEqual(filtered_data["results"], [])

            with open(raw_path, "r", encoding="utf-8") as handle:
                raw_data = json.load(handle)

            self.assertEqual(len(raw_data["results"]), 1)
            self.assertEqual(raw_data["results"][0]["name"], "资深 AI Agent 工程师")
            self.assertEqual(raw_data["results"][0]["_query"], "AI Agent")

    def test_keeps_high_salary_roles_in_filtered_results(self):
        module = load_module()

        config = {
            "name": "BOSS岗位监控",
            "global_settings": {
                "city": "上海",
                "experience": "",
                "degree": "本科",
                "opencli_salary": "50K以上",
                "min_salary_k": 50,
            },
            "channels": {
                "boss_track_01": {
                    "enabled": True,
                    "query": "AI产品经理",
                    "limit": 15,
                }
            },
        }

        high_salary_result = [
            {
                "name": "AI产品经理",
                "salary": "50-60K",
                "company": "测试公司",
                "url": "https://example.com/job/2",
                "skills": "AI产品,C端产品",
            }
        ]

        with tempfile.TemporaryDirectory() as tempdir:
            config_path = os.path.join(tempdir, "config.json")
            filtered_path = os.path.join(tempdir, "topic_results.json")

            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump(config, handle, ensure_ascii=False)

            module.CONFIG_FILE = config_path
            module.OUTPUT_FILE = filtered_path

            current_dir = os.getcwd()
            os.chdir(tempdir)
            try:
                with mock.patch.object(module.random, "shuffle", side_effect=lambda items: None):
                    with mock.patch.object(
                        module.subprocess,
                        "run",
                        return_value=CompletedProcess(
                            args="opencli boss search 'AI产品经理'",
                            returncode=0,
                            stdout=json.dumps(high_salary_result, ensure_ascii=False),
                            stderr="",
                        ),
                    ):
                        module.run_scout()
            finally:
                os.chdir(current_dir)

            with open(filtered_path, "r", encoding="utf-8") as handle:
                filtered_data = json.load(handle)

            self.assertEqual(len(filtered_data["results"]), 1)
            self.assertEqual(filtered_data["results"][0]["salary"], "50-60K")


if __name__ == "__main__":
    unittest.main()
