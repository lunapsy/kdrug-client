"""._env 로더/생성기 테스트."""

import os

import pytest

from kdrug import KdrugClient, create_env_file, load_dotenv
from kdrug._env import find_dotenv


def test_create_and_load_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("KDRUG_API_KEY", raising=False)

    path = create_env_file()
    assert path.exists()
    # 템플릿 키 채우기
    path.write_text("KDRUG_API_KEY=my-secret-key\n", encoding="utf-8")

    assert load_dotenv() is True
    assert os.environ["KDRUG_API_KEY"] == "my-secret-key"

    client = KdrugClient.from_env()
    assert client.api_key == "my-secret-key"


def test_create_env_refuses_overwrite(tmp_path):
    target = tmp_path / ".env"
    target.write_text("KDRUG_API_KEY=existing\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        create_env_file(target)
    # force=True 면 덮어씀
    create_env_file(target, force=True)
    assert "KDRUG_API_KEY=" in target.read_text(encoding="utf-8")


def test_real_env_takes_priority(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("KDRUG_API_KEY=from-file\n", encoding="utf-8")
    monkeypatch.setenv("KDRUG_API_KEY", "from-shell")

    load_dotenv()  # override=False 이므로 기존 환경변수 유지
    assert os.environ["KDRUG_API_KEY"] == "from-shell"


def test_find_dotenv_searches_parents(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("KDRUG_API_KEY=x\n", encoding="utf-8")
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    found = find_dotenv()
    assert found is not None and found.name == ".env"


def test_load_dotenv_missing_returns_false(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_dotenv(tmp_path / "nope.env") is False
