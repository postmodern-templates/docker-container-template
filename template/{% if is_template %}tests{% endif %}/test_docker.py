"""Checks the Docker workflows this template adds to its Standard GitHub projects."""

import re
import tomllib
from pathlib import Path

import pytest
from conftest import RENDERABLE_ANSWERS, _render

STANDARD_GITHUB_ANSWERS = [
    a
    for a in RENDERABLE_ANSWERS
    if a.get("project_type", "Standard") == "Standard"
    and a.get("developer_platform") == "GitHub"
]
TEMPLATE_ANSWERS = [
    a for a in RENDERABLE_ANSWERS if a.get("project_type") == "Template"
]


@pytest.mark.parametrize("answers", STANDARD_GITHUB_ANSWERS, ids=lambda a: a["id"])
def test_release_dispatches_docker_image(template_source, tmp_path: Path, answers):
    """Publishing a release has to dispatch the Docker release image workflow.

    The tag Knope creates with GITHUB_TOKEN fires no `push` event, so nothing else
    builds the image. The publish job also needs `actions: write` to dispatch it.
    """
    dest = tmp_path / "out"
    _render(template_source, dest, answers)
    workflows = dest / ".github" / "workflows"
    assert (workflows / "docker-auto-publishci.yml").is_file()  # noqa: S101
    assert (workflows / "docker-auto-publishrelease.yml").is_file()  # noqa: S101
    publish = (workflows / "release-auto-publishrelease.yml").read_text(
        encoding="utf-8"
    )
    assert "gh workflow run docker-auto-publishrelease.yml" in publish  # noqa: S101
    assert "actions: write" in publish  # noqa: S101


@pytest.mark.parametrize("answers", TEMPLATE_ANSWERS, ids=lambda a: a["id"])
def test_docker_tasks_pass_only_known_flags(template_source, tmp_path: Path, answers):
    """Every flag the Docker tasks pass has to be one the script's parser accepts.

    mise.toml.jinja's tasks vary by answer, such as for a leaf template, and an unknown
    flag only fails when someone runs the task.
    """
    dest = tmp_path / "out"
    _render(template_source, dest, answers)
    tasks = tomllib.loads((dest / "mise.toml").read_text(encoding="utf-8"))["tasks"]
    script = (dest / "scripts" / "integration_test_docker.py").read_text(
        encoding="utf-8"
    )
    for name in ("integration-test-docker", "integration-test-docker-cleanup"):
        for flag in re.findall(r"(?<!\S)--[a-z-]+", tasks[name]["run"]):
            assert f'"{flag}"' in script, f"{name} passes unknown {flag}"  # noqa: S101


@pytest.mark.parametrize("answers", STANDARD_GITHUB_ANSWERS, ids=lambda a: a["id"])
def test_dockerfile_makes_entrypoint_executable(
    template_source, tmp_path: Path, answers
):
    """The image has to set the entrypoint's mode, which a Windows copy drops."""
    dest = tmp_path / "out"
    _render(template_source, dest, answers)
    dockerfile = (dest / "src" / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY --chmod=755 entrypoint.sh" in dockerfile  # noqa: S101
