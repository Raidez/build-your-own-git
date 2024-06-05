import os
import zlib
import magic
import pytest
import subprocess

executable_path = os.path.abspath("./app/git")


@pytest.fixture
def git_init_folder(tmp_path):
    os.mkdir(tmp_path / ".git")
    os.mkdir(tmp_path / ".git/objects")
    os.mkdir(tmp_path / ".git/refs")
    with open(tmp_path / ".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")


@pytest.fixture
def git_touch_file(tmp_path):
    with open(tmp_path / "test.txt", "w") as f:
        f.write("hello world\n")


@pytest.fixture
def git_hash_object(tmp_path, git_touch_file):
    blob_sha = "3b18e512dba79e4c8300dd08aeb37f8e728b8dad"
    payload = b"blob 11\0hello world\n"

    os.mkdir(tmp_path / f".git/objects/{blob_sha[:2]}")
    with open(tmp_path / f".git/objects/{blob_sha[:2]}/{blob_sha[2:]}", "wb") as f:
        f.write(zlib.compress(payload))


################################################################################


def test_hello(tmp_path):
    process = subprocess.run(
        executable_path, cwd=tmp_path, shell=True, text=True, capture_output=True
    )

    print(process.stdout)
    assert process.returncode == 0

    assert f"hello world {tmp_path}" == process.stdout.strip()


def test_init(tmp_path):
    process = subprocess.run(
        executable_path + " init",
        cwd=tmp_path,
        shell=True,
        text=True,
        capture_output=True,
    )

    print(process.stdout)
    assert process.returncode == 0

    assert (git_path := tmp_path / ".git").exists() and git_path.is_dir()
    assert (git_objects := git_path / "objects").exists() and git_objects.is_dir()
    assert (git_refs := git_path / "refs").exists() and git_refs.is_dir()
    assert (
        (git_head := git_path / "HEAD").exists()
        and git_head.is_file()
        and "ref: refs/heads/main" in git_head.read_text()
    )
    assert "Initialized git directory" == process.stdout.strip()


def test_hash_object(tmp_path, git_init_folder, git_touch_file):
    process = subprocess.run(
        executable_path + " hash-object test.txt",
        cwd=tmp_path,
        shell=True,
        text=True,
        capture_output=True,
    )

    print(process.stdout)
    assert process.returncode == 0

    assert "3b18e512dba79e4c8300dd08aeb37f8e728b8dad" == process.stdout.strip()


def test_encode_blob(tmp_path, git_init_folder, git_touch_file):
    process = subprocess.run(
        executable_path + " hash-object -w test.txt",
        cwd=tmp_path,
        shell=True,
        text=True,
        capture_output=True,
    )

    print(process.stdout)
    assert process.returncode == 0

    blob_sha = "3b18e512dba79e4c8300dd08aeb37f8e728b8dad"
    assert (blob := tmp_path / f".git/objects/{blob_sha[:2]}/{blob_sha[2:]}").exists()
    assert "zlib compressed data" == magic.from_file(blob)


def test_decode_blob(tmp_path, git_init_folder, git_hash_object):
    process = subprocess.run(
        executable_path + " cat-file -p 3b18e512dba79e4c8300dd08aeb37f8e728b8dad",
        cwd=tmp_path,
        shell=True,
        text=True,
        capture_output=True,
    )

    print(process.stdout)
    assert process.returncode == 0

    assert "hello world" == process.stdout.strip()
