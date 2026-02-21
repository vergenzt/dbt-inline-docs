import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest
import tinypg
from pytest import fixture

DBT_PROFILES_DIR = Path(__file__).parent
DBT_PROFILE = "test_profile"
DBT_PROJECT_NAME = "test_" + re.sub(
    r"[^\w]", "_", os.getenv("ENV_NAME", DBT_PROFILES_DIR.parent.name).lower()
)
DBT_PROJECT_YML: str = json.dumps(
    {
        "name": DBT_PROJECT_NAME,
        "version": "0.0.1",
        "profile": DBT_PROFILE,
        "model-paths": ["models"],
        "target-path": "target",
    }
)


@fixture(autouse=True)
def dbt_project(tmp_path, monkeypatch):
    dbt_project_path = tmp_path / DBT_PROJECT_NAME
    dbt_project_path.mkdir()
    dbt_project_path.joinpath("dbt_project.yml").write_text(DBT_PROJECT_YML)
    dbt_project_path.joinpath("models").mkdir()
    dbt_project_path.joinpath("target").mkdir()

    monkeypatch.setenv("DBT_PROFILES_DIR", str(DBT_PROFILES_DIR))
    monkeypatch.setenv("DBT_PROJECT_DIR", str(dbt_project_path))

    with tinypg.database() as dburl_str:
        dburl = urlparse(dburl_str)
        monkeypatch.setenv("DB_HOST", dburl.hostname or "")
        monkeypatch.setenv("DB_USERNAME", dburl.username or "")
        monkeypatch.setenv("DB_PASSWORD", dburl.password or "")
        monkeypatch.setenv("DB_PORT", str(dburl.port))
        monkeypatch.setenv("DB_NAME", dburl.path[1:] or "")
        monkeypatch.setenv("DB_SCHEMA", "public")
        monkeypatch.chdir(dbt_project_path)

        yield dbt_project_path


@pytest.mark.parametrize(
    ("model_name", "model_sql", "expected_node_dict"),
    [
        (
            "model_description",
            """
                /** @moddoc
                This is my cool model. I can write a description in-line!
                */
                select 1
            """,
            {
                "description": "This is my cool model. I can write a description in-line!",
            },
        ),
        (
            "model_description_with_yaml",
            """
                /** @moddoc
                A cool model -- with yaml!
                ---
                config:
                  docs:
                    show: false
                */
                select 1
            """,
            {
                "description": "A cool model -- with yaml!",
                "unrendered_config": {
                    "docs": {
                        "show": False,
                    },
                },
            },
        ),
    ],
)
def test_single_model(dbt_project: Path, model_name: str, model_sql: str, expected_node_dict: dict):
    model_path = dbt_project / "models" / f"{model_name}.sql"
    model_path.write_text(model_sql)

    from dbt.cli.main import cli

    cli(["compile"], standalone_mode=False)

    manifest = json.loads(dbt_project.joinpath("target/manifest.json").read_text())
    node = manifest["nodes"][f"model.{DBT_PROJECT_NAME}.{model_name}"]
    assert {k: v for k, v in node.items() if k in expected_node_dict} == expected_node_dict
