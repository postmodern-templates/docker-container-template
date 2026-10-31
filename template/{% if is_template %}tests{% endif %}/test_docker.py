"""Checks the Docker workflows this template adds to its Standard GitHub projects."""

from pathlib import Path

import pytest
from conftest import RENDERABLE_ANSWERS, _render

STANDARD_GITHUB_ANSWERS = [
    a
    for a in RENDERABLE_ANSWERS
    if a.get("project_type", "Standard") == "Standard"
    and a.get("developer_platform") == "GitHub"
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
