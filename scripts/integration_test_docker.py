"""Create a throwaway Standard repo from this template and verify its Docker images.

Run it with `mise run integration-test-docker`. integration_test_github.py's repos are
Template projects, which don't render the Docker workflows, so this makes its own. It
always runs against HEAD, to verify a release candidate on main before a release.

It merges a change under src/, checks that the CI image is published and attested,
runs the release flow, checks the same for the release image, and runs that image to
check that the entrypoint maps the UID and GID it's given. The repo and its package
stay for inspection; delete them with `mise run integration-test-docker-cleanup`.
"""

import argparse
import json
import re
import sys
import tempfile
import time
from pathlib import Path

from console import (
    RepoResult,
    check,
    heading,
    run,
    save_log,
    say,
    start_log,
    step,
    summary,
)
from integration_test_github import (
    SCRATCH_FILE_CONTENT,
    check_gh_installed,
    check_release_flow,
    confirm,
    create,
    gh_value,
    latest_run_id,
    open_pr_wait_and_merge,
    provision_test_secrets,
    wait_for_new_run,
    wait_for_run,
)
from repo_edits import local_clone_dir, local_clones, prepare_repo_b, remove_clones

# Beyond integration_test_github.py's scopes: read:packages reads the package and pulls
# its image. Only cleanup needs delete:packages and delete_repo.
REQUIRED_SCOPES = ("repo", "workflow", "read:packages")
CLEANUP_SCOPES = ("delete_repo", "delete:packages")

CI_WORKFLOW = "docker-auto-publishci.yml"
RELEASE_WORKFLOW = "docker-auto-publishrelease.yml"

TEST_UID = "12345"
TEST_GID = "23456"


def test_repo_pattern(repo_prefix: str) -> re.Pattern[str]:
    """Match the names main() gives its test repos, and nothing else.

    Returns:
        A pattern for `<repo_prefix>-integration-test-docker-<timestamp>`.

    """
    return re.compile(rf"{re.escape(repo_prefix)}-integration-test-docker-\d+")


def missing_scopes(scopes: tuple[str, ...]) -> list[str]:
    """Find which of `scopes` the active gh token lacks.

    Returns:
        The missing scopes, from `gh auth status`'s "Token scopes" line.

    """
    status = run("gh", "auth", "status", check=False, capture=True, echo=False)
    output = status.stdout + status.stderr
    return [scope for scope in scopes if f"'{scope}'" not in output]


def check_prerequisites() -> None:
    """Verify gh, its scopes, and a running Docker daemon before creating anything.

    Raises:
        SystemExit: if any of them is missing, with the command that fixes it.

    """
    check_gh_installed()
    if missing := missing_scopes(REQUIRED_SCOPES):
        raise SystemExit(
            f"Token is missing required scope(s): {', '.join(missing)}. Add them with "
            f"`gh auth refresh -h github.com -s {','.join(missing)}`, then rerun."
        )
    try:
        daemon = run("docker", "version", check=False, capture=True, echo=False)
    except FileNotFoundError:
        raise SystemExit("Docker isn't installed. Install it, then rerun.") from None
    if daemon.returncode:
        raise SystemExit("Docker isn't running. Start it, then rerun.")


def image_tags(package: str) -> set[str]:
    """List the tags published in the account's container package.

    Returns:
        Every tag on every version, or an empty set if the package doesn't exist.

    """
    result = run(
        "gh", "api", "--paginate", f"user/packages/container/{package}/versions",
        "--jq", ".[].metadata.container.tags[]",
        check=False, capture=True,
    )  # fmt: skip
    return set(result.stdout.split()) if result.returncode == 0 else set()


def check_workflow_run(repo: str, run_id: int, name: str, failures: list[str]) -> None:
    """Wait for a Docker workflow run and check that it succeeded."""
    conclusion = wait_for_run(repo, run_id, timeout=3600)
    check(failures, f"{name} succeeds", conclusion == "success", conclusion)


def check_image(
    repo: str,
    tag: str,
    expected_tags: set[str],
    env: dict[str, str],
    failures: list[str],
) -> None:
    """Check that the expected tags exist and that `tag` has a valid attestation."""
    package = repo.rsplit("/", 1)[-1]
    tags = image_tags(package)
    check(
        failures,
        f"the package has tags {sorted(expected_tags)}",
        expected_tags <= tags,
        f"found {sorted(tags)}",
    )
    verify = run(
        "gh", "attestation", "verify", f"oci://ghcr.io/{repo.lower()}:{tag}",
        "--repo", repo,
        check=False, capture=True, env=env,
    )  # fmt: skip
    check(
        failures,
        f"the {tag} image has a valid build attestation",
        verify.returncode == 0,
        verify.stderr.strip(),
    )


def check_entrypoint(
    repo: str, tag: str, env: dict[str, str], failures: list[str]
) -> None:
    """Run the image and check its UID and GID mapping and default command."""
    result = run(
        "docker", "run", "--rm", "--pull", "always",
        "-e", f"HOST_UID={TEST_UID}", "-e", f"HOST_GID={TEST_GID}",
        f"ghcr.io/{repo.lower()}:{tag}",
        check=False, capture=True, env=env,
    )  # fmt: skip
    output = result.stdout + result.stderr
    save_log("docker-run.log", output)
    check(failures, "the image runs", result.returncode == 0, output.strip())
    check(
        failures,
        "the entrypoint maps the given UID and GID",
        f"UID: {TEST_UID}" in output and f"GID: {TEST_GID}" in output,
        output.strip(),
    )
    check(
        failures,
        "the image's default command runs",
        "GNU nano" in output,
        output.strip(),
    )


def verify_docker(repo: str, dest: str, source: str, failures: list[str]) -> None:
    """Exercise both workflows and the published images, against a real repo."""
    package = repo.rsplit("/", 1)[-1]
    if setup := prepare_repo_b(source):
        step("Merging the setup PR")
        open_pr_wait_and_merge(
            repo,
            dest,
            "integration-test/setup",
            "chore: set up the repo for the integration test",
            edit=setup,
        )

    with tempfile.TemporaryDirectory() as docker_config:
        # A throwaway config, so the login below leaves the user's own untouched.
        env = {"DOCKER_CONFIG": docker_config}
        token = gh_value("auth", "token", echo=False)
        owner = repo.split("/", 1)[0]
        run(
            "docker", "login", "ghcr.io", "-u", owner, "--password-stdin",
            capture=True, env=env, stdin=token, secret=True,
        )  # fmt: skip

        step("Checking Docker (Auto): Publish CI Image")
        before = latest_run_id(repo, CI_WORKFLOW, event="push")

        def edit_src(root: Path) -> None:
            with (root / "src" / "Dockerfile").open(
                "a", encoding="utf-8", newline="\n"
            ) as f:
                f.write(SCRATCH_FILE_CONTENT.splitlines()[0] + "\n")

        open_pr_wait_and_merge(
            repo,
            dest,
            "integration-test/image-change",
            "chore: integration test image change",
            edit=edit_src,
        )
        run_id = wait_for_new_run(repo, CI_WORKFLOW, before, event="push")
        check_workflow_run(repo, run_id, "a merge under src/'s CI image run", failures)
        check_image(repo, "ci", {"ci"}, env, failures)

        check_release_flow(repo, dest, failures)

        step("Checking Docker (Auto): Publish Release Image")
        release = run(
            "gh", "release", "view", "--repo", repo,
            "--json", "tagName", "-q", ".tagName",
            check=False, capture=True,
        )  # fmt: skip
        check(failures, "the repo has a release", release.returncode == 0)
        if release.returncode:
            return
        version = release.stdout.strip().removeprefix("v")
        major, minor, _ = version.split(".", 2)
        # Raises SystemExit, naming the workflow, if Publish Release didn't dispatch it.
        run_id = wait_for_new_run(repo, RELEASE_WORKFLOW, "", event="workflow_dispatch")
        check_workflow_run(repo, run_id, "the release image run", failures)
        # metadata-action leaves out the bare major tag for a 0.x version.
        expected = {"latest", version, f"{major}.{minor}"}
        if major != "0":
            expected.add(major)
        check_image(repo, version, expected, env, failures)
        check_entrypoint(repo, version, env, failures)
    say(f"Package: https://github.com/users/{owner}/packages/container/{package}")


def cleanup(owner: str, repo_prefix: str, *, yes: bool) -> None:
    """Delete every test repo main() created, its package, and its local clone.

    It finds them by name, so it covers runs that stopped partway. Deleting a repo
    doesn't delete its package, so this deletes both. It lists everything, then asks.

    Raises:
        SystemExit: if the token lacks a scope cleanup needs, or a local clone can't
            be deleted.

    """
    pattern = test_repo_pattern(repo_prefix)
    if missing := missing_scopes(CLEANUP_SCOPES):
        raise SystemExit(
            f"Cleanup needs the {', '.join(missing)} scope(s). Add them with "
            f"`gh auth refresh -h github.com -s {','.join(missing)}`, then rerun."
        )
    repos = json.loads(
        gh_value("repo", "list", owner, "--limit", "1000", "--json", "name")
    )
    names = sorted(r["name"] for r in repos if pattern.fullmatch(r["name"]))
    packages = json.loads(
        gh_value("api", "--paginate", "user/packages?package_type=container") or "[]"
    )
    package_names = sorted(p["name"] for p in packages if pattern.fullmatch(p["name"]))
    clones = local_clones(pattern, "github.com")
    if not names and not package_names and not clones:
        say(f"No Docker integration-test repos, packages, or clones under {owner}.")
        return
    say("Docker integration-test repos, packages, and local clones to delete:")
    for name in names:
        say(f"  repo {owner}/{name}")
    for name in package_names:
        say(f"  package {name}")
    for clone in clones:
        say(f"  clone {clone}")
    if not confirm("Delete all of these?", yes=yes):
        say("Nothing deleted.")
        return
    for name in package_names:
        run("gh", "api", "-X", "DELETE", f"user/packages/container/{name}")
    for name in names:
        run("gh", "repo", "delete", f"{owner}/{name}", "--yes")
    deleted = remove_clones(clones)
    say(
        f"Deleted {len(names)} repo(s), {len(package_names)} package(s), and "
        f"{deleted} local clone(s)."
    )
    if deleted < len(clones):
        raise SystemExit(1)


def main() -> None:
    """Create and verify one throwaway Standard repo, or clean up past runs.

    Raises:
        SystemExit: if required arguments are missing, or if any check failed (after
            printing every check's result; see check()).

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="Copier template source URL")
    parser.add_argument("--repo-prefix", required=True, help="This repo's own name")
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Skip creating a repo; delete every repo and package a run made.",
    )
    parser.add_argument(
        "--yes", action="store_true", help="Don't ask before --cleanup deletes."
    )
    args = parser.parse_args()
    log_dir = start_log("docker")
    say(f"Logging this run to {log_dir}")

    if args.cleanup:
        check_gh_installed()
        owner = gh_value("api", "user", "--jq", ".login")
        cleanup(owner, args.repo_prefix, yes=args.yes)
        return
    if not args.source:
        raise SystemExit("--source is required.")
    check_prerequisites()

    owner = gh_value("api", "user", "--jq", ".login")
    repo_name = f"{args.repo_prefix}-integration-test-docker-{int(time.time())}"
    repo = f"{owner}/{repo_name}"
    dest = local_clone_dir(repo_name)
    heading(
        "A Standard copy at HEAD (zensical_target: GitHub Pages, code_coverage: off)"
    )
    step(f"Creating {repo} at HEAD")
    # leaf=True leaves out the Template answers, so this copy is Standard by default.
    create(
        args.source,
        "HEAD",
        repo_name,
        dest,
        owner,
        "GitHub Pages",
        code_coverage=False,
        leaf=True,
    )
    step("Setting test secrets")
    provision_test_secrets(repo)
    failures: list[str] = []
    verify_docker(repo, dest, args.source, failures)
    summary(
        [
            RepoResult(
                "Docker repo", repo, dest, failures, url=f"https://github.com/{repo}"
            )
        ]
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit("\nStopped. Run the cleanup task to delete what this run created.")
