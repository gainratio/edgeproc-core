"""Behavioral contracts for EdgeProc Core's composed Dagger release graph."""

from __future__ import annotations

import asyncio
import inspect
import json
from pathlib import Path
from typing import cast

import dagger
import pytest

from edgeproc_core import main
from edgeproc_core.main import EdgeprocCore

ROOT = Path(__file__).parents[2]
COMMIT_SHA = "a" * 40
EXPECTED_CENTRAL_SHA = "a88866232e679b6353d2b75bceb01969be739f67"

#: The repository as GitHub reports it since the org transfer, and its pre-transfer name.
CANONICAL = "gainratio/edgeproc-core"
ALLOWED = (CANONICAL, "hseshadr/edgeproc-core")

#: A fork, a sibling repository, a look-alike name, a look-alike owner, and nothing.
REFUSED = (
    "attacker/edgeproc-core",
    "gainratio/edge-proc",
    "hseshadr/edgeproc-core-evil",
    "gainratio-evil/edgeproc-core",
    "",
)


class RecordingWorkspace:
    """Record the explicit source directory selected by the constructor."""

    def __init__(self) -> None:
        self.path = ""

    def directory(self, path: str, **_options: object) -> dagger.Directory:
        self.path = path
        return cast(dagger.Directory, object())


class RecordingContainer:
    """Record when one lazy Dagger security or audit graph is evaluated."""

    def __init__(self) -> None:
        self.synced = False

    async def sync(self) -> RecordingContainer:
        self.synced = True
        return self


class RecordingDirectory:
    """Record the exact Git metadata overlay applied to one bound snapshot."""

    def __init__(self, guard: RecordingContainer) -> None:
        self.guard = guard
        self.includes: list[str] = []
        self.overlay: tuple[str, object] | None = None
        self.guard_synced_when_filtered = False

    def filter(self, *, include: list[str]) -> RecordingDirectory:
        self.includes = include
        self.guard_synced_when_filtered = self.guard.synced
        return self

    def with_directory(self, path: str, directory: object) -> RecordingDirectory:
        self.overlay = (path, directory)
        return self


class RecordingFoundation:
    """Record exact Foundation source and guard identities."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, object, str, str]] = []
        self.bound = cast(dagger.Directory, object())
        self.security = RecordingContainer()

    def source(
        self, source: dagger.Directory, repository: str, commit_sha: str
    ) -> dagger.Directory:
        self.calls.append(("source", source, repository, commit_sha))
        return self.bound

    def guard(self, source: dagger.Directory, repository: str, commit_sha: str) -> dagger.Container:
        self.calls.append(("guard", source, repository, commit_sha))
        return cast(dagger.Container, self.security)


class RecordingCandidate:
    """Expose one verified envelope in the generated candidate shape."""

    def __init__(self, envelope: dagger.Directory) -> None:
        self._envelope = envelope

    def envelope(self) -> dagger.Directory:
        return self._envelope


class RecordingArtifactEnvelope:
    """Record projection of one authenticated Foundation artifact subtree."""

    def __init__(self) -> None:
        self.artifact = cast(dagger.Directory, object())
        self.requested: list[str] = []

    def directory(self, path: str) -> dagger.Directory:
        self.requested.append(path)
        return self.artifact


class RecordingPythonPackage:
    """Record the closed reusable package operations selected by the adapter."""

    def __init__(self) -> None:
        self.audit = RecordingContainer()
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.created = cast(dagger.Directory, object())
        self.verified = cast(dagger.Directory, object())

    def dependency_audit(
        self, source: dagger.Directory, repository: str, commit_sha: str
    ) -> dagger.Container:
        self.calls.append(("dependency_audit", (source, repository, commit_sha)))
        return cast(dagger.Container, self.audit)

    def candidate(self, *arguments: object) -> RecordingCandidate:
        self.calls.append(("candidate", arguments))
        return RecordingCandidate(self.created)

    def verify_candidate(self, *arguments: object) -> RecordingCandidate:
        self.calls.append(("verify_candidate", arguments))
        return RecordingCandidate(self.verified)


def test_should_select_explicit_root_when_constructing_release_graph() -> None:
    # Given
    workspace = RecordingWorkspace()

    # When
    EdgeprocCore.create(cast(dagger.Workspace, workspace))

    # Then
    assert workspace.path == "/"


def test_should_require_typed_workspace_when_constructing_release_graph() -> None:
    # Given
    signature = inspect.signature(EdgeprocCore.create, eval_str=True)

    # When
    workspace = signature.parameters.get("workspace")

    # Then
    assert workspace is not None
    assert workspace.annotation is dagger.Workspace


def test_should_expose_only_composed_quality_and_release_boundaries() -> None:
    # Given
    expected = {"ci", "quality", "dependency_audit", "release_candidate"}

    # When
    available = {name for name in expected if hasattr(EdgeprocCore, name)}

    # Then
    assert available == expected
    assert not hasattr(EdgeprocCore, "secret_scan")
    assert not hasattr(EdgeprocCore, "workflow_security")


def test_should_require_bound_sha_for_every_unprivileged_entrypoint() -> None:
    # Given / When
    names = ("ci", "quality", "dependency_audit")
    signatures = [inspect.signature(getattr(EdgeprocCore, name), eval_str=True) for name in names]

    # Then
    assert all(
        item.parameters["commit_sha"].default is inspect.Parameter.empty for item in signatures
    )


@pytest.mark.parametrize("repository", ALLOWED)
def test_should_bind_snapshot_before_product_quality(
    monkeypatch: pytest.MonkeyPatch, repository: str
) -> None:
    # Given
    foundation = RecordingFoundation()
    history = RecordingDirectory(foundation.security)
    requested_history: list[tuple[str, str]] = []
    source = cast(dagger.Directory, object())
    monkeypatch.setattr(main, "_foundation", lambda: foundation)
    monkeypatch.setattr(
        main,
        "_history",
        lambda commit_sha, repo: requested_history.append((commit_sha, repo)) or history,
    )

    # When
    actual = asyncio.run(EdgeprocCore._verified_source(source, COMMIT_SHA, repository))

    # Then
    assert actual is history
    assert foundation.security.synced
    assert requested_history == [(COMMIT_SHA, repository)]
    assert history.guard_synced_when_filtered
    assert history.includes == [".git", ".git/**"]
    assert history.overlay == ("/", foundation.bound)
    assert foundation.calls == [
        ("source", source, repository, COMMIT_SHA),
        ("guard", source, repository, COMMIT_SHA),
    ]


def test_should_delegate_dependency_audit_to_shared_python_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    package = RecordingPythonPackage()
    source = cast(dagger.Directory, object())
    graph = EdgeprocCore.__new__(EdgeprocCore)
    graph.source = source
    monkeypatch.setattr(main, "_python_package", lambda: package)

    # When
    actual = graph.dependency_audit(COMMIT_SHA, CANONICAL)

    # Then
    assert actual is package.audit
    assert package.calls == [("dependency_audit", (source, CANONICAL, COMMIT_SHA))]


@pytest.mark.parametrize("repository", ALLOWED)
def test_should_create_then_verify_closed_candidate_with_same_identity(
    monkeypatch: pytest.MonkeyPatch, repository: str
) -> None:
    # Given
    package = RecordingPythonPackage()
    source = cast(dagger.Directory, object())
    token = cast(dagger.Secret, object())
    monkeypatch.setattr(main, "_python_package", lambda: package)

    # When
    lineage = main._Lineage(repository, COMMIT_SHA, "6100", 2)
    actual = EdgeprocCore._candidate_envelope(source, token, lineage)

    # Then
    identity = (
        source,
        token,
        repository,
        COMMIT_SHA,
        "edgeproc-core",
        EXPECTED_CENTRAL_SHA,
        "6100",
        2,
    )
    assert package.calls == [
        ("candidate", identity),
        ("verify_candidate", (package.created, *identity[2:])),
    ]
    assert actual is package.verified


def test_should_project_authenticated_artifact_into_existing_publisher_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    graph = EdgeprocCore.__new__(EdgeprocCore)
    graph.source = cast(dagger.Directory, object())
    envelope = RecordingArtifactEnvelope()
    checked_tags: list[str] = []

    async def verified(source: dagger.Directory, _sha: str, _repo: str) -> dagger.Directory:
        return source

    async def product_gate(_graph: EdgeprocCore, _source: dagger.Directory) -> None:
        return None

    async def green_identity(_token: dagger.Secret, _repository: str) -> tuple[str, int]:
        return "6100", 2

    monkeypatch.setattr(EdgeprocCore, "_verified_source", staticmethod(verified))
    monkeypatch.setattr(EdgeprocCore, "_run_product_gate", product_gate)
    monkeypatch.setattr(EdgeprocCore, "_green_identity", staticmethod(green_identity))
    monkeypatch.setattr(
        EdgeprocCore,
        "_candidate_envelope",
        staticmethod(lambda *_arguments: cast(dagger.Directory, envelope)),
    )
    monkeypatch.setattr(
        EdgeprocCore,
        "_require_requested_tag",
        staticmethod(lambda value, tag: checked_tags.append(tag) or value),
    )

    # When
    actual = asyncio.run(
        graph.release_candidate("v0.4.2", COMMIT_SHA, cast(dagger.Secret, object()), CANONICAL)
    )

    # Then
    assert checked_tags == ["v0.4.2"]
    assert envelope.requested == ["artifact"]
    assert actual is envelope.artifact


def test_should_pin_both_shared_modules_to_same_reviewed_commit() -> None:
    # Given / When
    config = json.loads((ROOT / "dagger.json").read_text(encoding="utf-8"))
    dependencies = {item["name"]: item for item in config["dependencies"]}

    # Then
    assert set(dependencies) == {"foundation", "python-package"}
    assert main.CENTRAL_MODULE_SHA == EXPECTED_CENTRAL_SHA
    assert {item["pin"] for item in dependencies.values()} == {EXPECTED_CENTRAL_SHA}
    assert dependencies["foundation"]["source"].endswith(
        f"/modules/portfolio-foundation@{EXPECTED_CENTRAL_SHA}"
    )
    assert dependencies["python-package"]["source"].endswith(
        f"/modules/python-package@{EXPECTED_CENTRAL_SHA}"
    )


def test_should_require_typed_secret_for_hosted_release_eligibility() -> None:
    # Given
    signature = inspect.signature(EdgeprocCore.release_candidate, eval_str=True)

    # When
    token = signature.parameters.get("github_token")
    result = signature.return_annotation

    # Then
    assert token is not None
    assert token.annotation is dagger.Secret
    assert result is dagger.Directory


def test_should_have_no_default_identity_to_fall_back_on() -> None:
    # Given
    names = ("ci", "quality", "dependency_audit", "release_candidate")

    # When
    defaults = {
        inspect.signature(getattr(EdgeprocCore, name)).parameters["repository"].default
        for name in names
    }

    # Then every gate must be told the run's own repository
    assert defaults == {inspect.Parameter.empty}
    assert not hasattr(main, "DEFAULT_REPOSITORY")
    assert main.ALLOWED_REPOSITORIES == ALLOWED


class RecordingGreenFoundation(RecordingFoundation):
    """Add the green-main evidence the release path reads."""

    def __init__(self) -> None:
        super().__init__()
        self.green_calls: list[str] = []

    def green_main(self, _token: dagger.Secret, repository: str) -> RecordingGreenEvidence:
        self.green_calls.append(repository)
        return RecordingGreenEvidence()


class RecordingGreenEvidence:
    """Return one fixed successful workflow identity."""

    async def workflow_run_id(self) -> str:
        return "6100"

    async def run_attempt(self) -> int:
        return 2


def _recording_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[EdgeprocCore, RecordingGreenFoundation, RecordingPythonPackage, list[str]]:
    foundation = RecordingGreenFoundation()
    package = RecordingPythonPackage()
    history: list[str] = []
    overlay = RecordingDirectory(foundation.security)
    monkeypatch.setattr(main, "_foundation", lambda: foundation)
    monkeypatch.setattr(main, "_python_package", lambda: package)
    monkeypatch.setattr(main, "_history", lambda _sha, repo: history.append(repo) or overlay)
    monkeypatch.setattr(EdgeprocCore, "_run_product_gate", lambda _graph, _source: _done())
    monkeypatch.setattr(EdgeprocCore, "_quality", lambda _graph, source: source)
    monkeypatch.setattr(
        EdgeprocCore, "_require_requested_tag", staticmethod(lambda *_: RecordingArtifactEnvelope())
    )
    graph = EdgeprocCore.__new__(EdgeprocCore)
    graph.source = cast(dagger.Directory, object())
    return graph, foundation, package, history


async def _done() -> None:
    return None


@pytest.mark.parametrize("repository", ALLOWED)
def test_should_bind_ci_and_release_to_the_runs_own_allowed_repository(
    monkeypatch: pytest.MonkeyPatch, repository: str
) -> None:
    # Given
    graph, foundation, package, history = _recording_graph(monkeypatch)
    token = cast(dagger.Secret, object())

    # When
    asyncio.run(graph.ci(COMMIT_SHA, repository))
    asyncio.run(graph.release_candidate("v0.4.2", COMMIT_SHA, token, repository))

    # Then
    assert {call[2] for call in foundation.calls} == {repository}
    assert history == [repository, repository]
    assert foundation.green_calls == [repository]
    assert {arguments[1] for name, arguments in package.calls if name == "dependency_audit"} == {
        repository
    }
    assert {arguments[2] for name, arguments in package.calls if name == "candidate"} == {
        repository
    }
    assert {arguments[1] for name, arguments in package.calls if name == "verify_candidate"} == {
        repository
    }


def _refused_entrypoints(graph: EdgeprocCore, repository: str) -> dict[str, object]:
    token = cast(dagger.Secret, object())
    return {
        "ci": lambda: asyncio.run(graph.ci(COMMIT_SHA, repository)),
        "quality": lambda: asyncio.run(graph.quality(COMMIT_SHA, repository)),
        "audit": lambda: graph.dependency_audit(COMMIT_SHA, repository),
        "release": lambda: asyncio.run(
            graph.release_candidate("v0.4.2", COMMIT_SHA, token, repository)
        ),
    }


@pytest.mark.parametrize("entrypoint", ["ci", "quality", "audit", "release"])
@pytest.mark.parametrize("repository", REFUSED)
def test_should_refuse_any_other_repository_before_any_shared_call(
    monkeypatch: pytest.MonkeyPatch, repository: str, entrypoint: str
) -> None:
    # Given
    graph, foundation, package, history = _recording_graph(monkeypatch)
    call = _refused_entrypoints(graph, repository)[entrypoint]

    # When / Then
    with pytest.raises(ValueError, match="not an allowed edgeproc-core repository"):
        call()  # type: ignore[operator]
    assert (foundation.calls, foundation.green_calls, package.calls, history) == ([], [], [], [])
