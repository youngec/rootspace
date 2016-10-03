# -*- coding: utf-8 -*-

import pytest

from rootspace.components import FileSystemState
from rootspace.exceptions import NotAnExecutableError


class TestFileSystemStateUnix(object):
    hierarchy = {
        "root": {"uid": 0, "gid": 0, "perm": 0o755, "contents": {
            "bin": {"uid": 0, "gid": 0, "perm": 0o755, "contents": {
                "test": {"uid": 0, "gid": 0, "perm": 0o755, "id": 0x0004},
                "badexec": {"uid": 0, "gid": 0, "perm": 0o755, "id": 0x0005}
            }},
            "dev": {"uid": 0, "gid": 0, "perm": 0o755, "contents": {}},
            "etc": {"uid": 0, "gid": 0, "perm": 0o755, "contents": {
                "passwd": {"uid": 0, "gid": 0, "perm": 0o644, "id": 0x0001},
                "shadow": {"uid": 0, "gid": 0, "perm": 0o000, "id": 0x0002},
                "config": {"uid": 0, "gid": 0, "perm": 0o666, "id": 0x0006}
            }},
            "home": {"uid": 0, "gid": 0, "perm": 0o755, "contents": {}},
            "root": {"uid": 0, "gid": 0, "perm": 0o750, "contents": {
                "secret": {"uid": 0, "gid": 0, "perm": 0o700, "id": 0x0003},
                "secret_dir": {"uid": 0, "gid": 0, "perm": 0o755, "contents": {}}
            }},
            "tmp": {"uid": 0, "gid": 0, "perm": 0o777, "contents": {}},
            "usr": {"uid": 0, "gid": 0, "perm": 0o755, "contents": {}}
        }}
    }

    database = {
        0x0001: {
            "root": {
                "password": "x",
                "UID": 0,
                "GID": 0,
                "GECOS": "root",
                "directory": "/root",
                "shell": "/bin/sh"
            }
        },
        0x0002: {
            "root": {
                "password": "!",
                "lastchanged": 0,
                "minimum": None,
                "maximum": None,
                "warn": None,
                "inactive": None,
                "expire": None
            }
        },
        0x0003: "This is a secret file.",
        0x0004: lambda a: 0,
        0x0005: "This is an executable file.",
        0x0006: "This is a configuration file."
    }

    @pytest.fixture
    def file_system_state(self):
        return FileSystemState(TestFileSystemStateUnix.hierarchy, TestFileSystemStateUnix.database, "unix", "/", "/")

    def test_bad_file_stat(self, file_system_state):
        with pytest.raises(FileNotFoundError):
            file_system_state.stat(0, 0, "/etc/badfile")

    def test_bad_file_read(self, file_system_state):
        with pytest.raises(FileNotFoundError):
            file_system_state.read(0, 0, "/etc/badfile")

    @pytest.mark.xfail(raises=FileNotFoundError)
    def test_bad_file_write(self, file_system_state):
        file_system_state.write(0, 0, "/etc/badfile", None)

    def test_bad_file_execute(self, file_system_state):
        with pytest.raises(FileNotFoundError):
            file_system_state.execute(0, 0, "/etc/badfile", None)

    def test_bad_directory_stat(self, file_system_state):
        with pytest.raises(FileNotFoundError):
            file_system_state.stat(0, 0, "/baddirectory/ignored")

    def test_bad_directory_read(self, file_system_state):
        with pytest.raises(FileNotFoundError):
            file_system_state.read(0, 0, "/baddirectory/ignored")

    def test_bad_directory_write(self, file_system_state):
        with pytest.raises(FileNotFoundError):
            file_system_state.write(0, 0, "/baddirectory/ignored", None)

    def test_bad_directory_execute(self, file_system_state):
        with pytest.raises(FileNotFoundError):
            file_system_state.execute(0, 0, "/baddirectory/ignored", None)

    def test_disallowed_stat_directory(self, file_system_state):
        with pytest.raises(PermissionError):
            file_system_state.stat(1000, 1000, "/root/secret")

    def test_disallowed_stat_file(self, file_system_state):
        # Stat will work on files that one does not have read permission for.
        file_system_state.stat(1000, 1000, "/etc/shadow")

    def test_disallowed_read_directory(self, file_system_state):
        with pytest.raises(PermissionError):
            file_system_state.read(1000, 1000, "/root/secret")

    def test_disallowed_read_file(self, file_system_state):
        with pytest.raises(PermissionError):
            file_system_state.read(1000, 1000, "/etc/shadow")

    @pytest.mark.parametrize("path", ["/etc", "/etc/passwd"])
    def test_stat(self, file_system_state, path):
        stat = file_system_state.stat(0, 0, path)

        assert isinstance(stat, dict)
        assert all(k in stat for k in ("path", "perm", "uid", "gid"))

    def test_read_file(self, file_system_state):
        data = file_system_state.read(0, 0, "/etc/passwd")

        assert data == TestFileSystemStateUnix.database[0x0001]
        assert id(data) != id(TestFileSystemStateUnix.database[0x0001])

    def test_read_directory(self, file_system_state):
        with pytest.raises(IsADirectoryError):
            file_system_state.read(0, 0, "/etc")

    def test_write_file(self, file_system_state):
        file_system_state.write(0, 0, "/etc/shadow", "Root is 1337!")

    def test_write_directory(self, file_system_state):
        with pytest.raises(IsADirectoryError):
            file_system_state.write(0, 0, "/etc", None)

    def test_execute_executable(self, file_system_state):
        assert file_system_state.execute(0, 0, "/bin/test", None) == 0

    def test_execute_non_executable(self, file_system_state):
        with pytest.raises(NotAnExecutableError):
            file_system_state.execute(0, 0, "/bin/badexec", None)
