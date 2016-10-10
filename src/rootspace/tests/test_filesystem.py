# -*- coding: utf-8 -*-

import uuid

import pytest

from rootspace.filesystem import Node, FileSystem


class TestNode(object):
    def test_node(self):
        # The following three statements must work.
        Node.create(0, 0, 0o755, "directory")
        Node.create(0, 0, 0o644, "file")
        Node.create(0, 0, 0o666, "special")

        # The following must raise TypeErrors.
        with pytest.raises(TypeError):
            Node.create(None, 0, 0o755, "directory")
        with pytest.raises(TypeError):
            Node.create(0, None, 0o755, "directory")
        with pytest.raises(TypeError):
            Node.create(0, 0, None, "directory")
        with pytest.raises(TypeError):
            Node.create(0, 0, 0o755, None)
        with pytest.raises(TypeError):
            Node.create(0, 0, 0o755, "directory", 0)

    def test_uid(self):
        node = Node.create(0, 0, 0o755, "directory")
        assert isinstance(node.uid, int)

    def test_gid(self):
        node = Node.create(0, 0, 0o755, "directory")
        assert isinstance(node.gid, int)

    def test_perm(self):
        node = Node.create(0, 0, 0o755, "directory")
        assert isinstance(node.perm, int)

    def test_perm_str(self):
        node = Node.create(0, 0, 0o755, "directory")
        assert isinstance(node.perm_str, str)

    @pytest.mark.parametrize(("node", "expected"), (
            (Node.create(0, 0, 0o755, "directory"), True),
            (Node.create(0, 0, 0o644, "file"), False),
            (Node.create(0, 0, 0o666, "special"), False)
    ))
    def test_is_directory(self, node, expected):
        assert node.is_directory == expected

    @pytest.mark.parametrize(("node", "expected"), (
            (Node.create(0, 0, 0o755, "directory"), False),
            (Node.create(0, 0, 0o644, "file"), True),
            (Node.create(0, 0, 0o666, "special"), False)
    ))
    def test_is_file(self, node, expected):
        assert node.is_file == expected

    @pytest.mark.parametrize(("node", "expected"), (
            (Node.create(0, 0, 0o755, "directory"), False),
            (Node.create(0, 0, 0o644, "file"), False),
            (Node.create(0, 0, 0o666, "special"), True)
    ))
    def test_is_special(self, node, expected):
        assert node.is_special == expected

    @pytest.mark.parametrize(("node", "expected"), (
            (Node.create(0, 0, 0o755, "directory"), dict),
            (Node.create(0, 0, 0o644, "file"), uuid.UUID)
    ))
    def test_contents(self, node, expected):
        assert isinstance(node.contents, expected)

    @pytest.mark.parametrize(("node", "uid", "gids", "expected"), (
            (Node.create(0, 0, 0o700, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o600, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o500, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o400, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o300, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o200, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o100, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o000, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o700, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o600, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o500, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o400, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o300, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o200, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o100, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o000, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o700, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o600, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o500, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o400, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o300, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o200, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o100, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o000, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o700, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o600, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o500, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o400, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o300, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o200, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o100, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o000, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o700, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o600, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o500, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o400, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o300, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o200, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o100, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o000, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o700, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o600, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o500, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o400, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o300, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o200, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o100, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o000, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o700, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o600, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o500, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o400, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o300, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o200, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o100, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o000, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o700, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o600, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o500, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o400, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o300, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o200, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o100, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o000, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o700, "directory"), 1, (1,), True),
            (Node.create(1, 1, 0o600, "directory"), 1, (1,), True),
            (Node.create(1, 1, 0o500, "directory"), 1, (1,), True),
            (Node.create(1, 1, 0o400, "directory"), 1, (1,), True),
            (Node.create(1, 1, 0o300, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o200, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o100, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o000, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o070, "directory"), 1, (1,), True),
            (Node.create(0, 1, 0o060, "directory"), 1, (1,), True),
            (Node.create(0, 1, 0o050, "directory"), 1, (1,), True),
            (Node.create(0, 1, 0o040, "directory"), 1, (1,), True),
            (Node.create(0, 1, 0o030, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o020, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o010, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o000, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o700, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o600, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o500, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o400, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o300, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o200, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o100, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o000, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o007, "directory"), 2, (2,), True),
            (Node.create(1, 1, 0o006, "directory"), 2, (2,), True),
            (Node.create(1, 1, 0o005, "directory"), 2, (2,), True),
            (Node.create(1, 1, 0o004, "directory"), 2, (2,), True),
            (Node.create(1, 1, 0o003, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o002, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o001, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o000, "directory"), 2, (2,), False),
    ))
    def test_may_read(self, node, uid, gids, expected):
        assert node.may_read(uid, gids) == expected

    @pytest.mark.parametrize(("node", "uid", "gids", "expected"), (
            (Node.create(0, 0, 0o700, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o600, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o500, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o400, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o300, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o200, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o100, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o000, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o700, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o600, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o500, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o400, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o300, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o200, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o100, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o000, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o700, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o600, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o500, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o400, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o300, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o200, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o100, "directory"), 0, (0,), True),
            (Node.create(1, 1, 0o000, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o700, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o600, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o500, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o400, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o300, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o200, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o100, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o000, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o700, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o600, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o500, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o400, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o300, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o200, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o100, "directory"), 1, (0,), True),
            (Node.create(0, 1, 0o000, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o700, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o600, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o500, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o400, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o300, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o200, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o100, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o000, "directory"), 1, (0,), True),
            (Node.create(0, 0, 0o700, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o600, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o500, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o400, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o300, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o200, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o100, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o000, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o700, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o600, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o500, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o400, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o300, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o200, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o100, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o000, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o700, "directory"), 1, (1,), True),
            (Node.create(1, 1, 0o600, "directory"), 1, (1,), True),
            (Node.create(1, 1, 0o500, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o400, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o300, "directory"), 1, (1,), True),
            (Node.create(1, 1, 0o200, "directory"), 1, (1,), True),
            (Node.create(1, 1, 0o100, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o000, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o070, "directory"), 1, (1,), True),
            (Node.create(0, 1, 0o060, "directory"), 1, (1,), True),
            (Node.create(0, 1, 0o050, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o040, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o030, "directory"), 1, (1,), True),
            (Node.create(0, 1, 0o020, "directory"), 1, (1,), True),
            (Node.create(0, 1, 0o010, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o000, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o700, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o600, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o500, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o400, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o300, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o200, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o100, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o000, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o007, "directory"), 2, (2,), True),
            (Node.create(1, 1, 0o006, "directory"), 2, (2,), True),
            (Node.create(1, 1, 0o005, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o004, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o003, "directory"), 2, (2,), True),
            (Node.create(1, 1, 0o002, "directory"), 2, (2,), True),
            (Node.create(1, 1, 0o001, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o000, "directory"), 2, (2,), False),
    ))
    def test_may_write(self, node, uid, gids, expected):
        assert node.may_write(uid, gids) == expected

    @pytest.mark.parametrize(("node", "uid", "gids", "expected"), (
            (Node.create(0, 0, 0o700, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o600, "directory"), 0, (0,), False),
            (Node.create(0, 0, 0o500, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o400, "directory"), 0, (0,), False),
            (Node.create(0, 0, 0o300, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o200, "directory"), 0, (0,), False),
            (Node.create(0, 0, 0o100, "directory"), 0, (0,), True),
            (Node.create(0, 0, 0o000, "directory"), 0, (0,), False),
            (Node.create(0, 1, 0o700, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o600, "directory"), 0, (0,), False),
            (Node.create(0, 1, 0o500, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o400, "directory"), 0, (0,), False),
            (Node.create(0, 1, 0o300, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o200, "directory"), 0, (0,), False),
            (Node.create(0, 1, 0o100, "directory"), 0, (0,), True),
            (Node.create(0, 1, 0o000, "directory"), 0, (0,), False),
            (Node.create(1, 1, 0o700, "directory"), 0, (0,), False),
            (Node.create(1, 1, 0o600, "directory"), 0, (0,), False),
            (Node.create(1, 1, 0o500, "directory"), 0, (0,), False),
            (Node.create(1, 1, 0o400, "directory"), 0, (0,), False),
            (Node.create(1, 1, 0o300, "directory"), 0, (0,), False),
            (Node.create(1, 1, 0o200, "directory"), 0, (0,), False),
            (Node.create(1, 1, 0o100, "directory"), 0, (0,), False),
            (Node.create(1, 1, 0o000, "directory"), 0, (0,), False),
            (Node.create(0, 0, 0o700, "directory"), 1, (0,), False),
            (Node.create(0, 0, 0o600, "directory"), 1, (0,), False),
            (Node.create(0, 0, 0o500, "directory"), 1, (0,), False),
            (Node.create(0, 0, 0o400, "directory"), 1, (0,), False),
            (Node.create(0, 0, 0o300, "directory"), 1, (0,), False),
            (Node.create(0, 0, 0o200, "directory"), 1, (0,), False),
            (Node.create(0, 0, 0o100, "directory"), 1, (0,), False),
            (Node.create(0, 0, 0o000, "directory"), 1, (0,), False),
            (Node.create(0, 1, 0o700, "directory"), 1, (0,), False),
            (Node.create(0, 1, 0o600, "directory"), 1, (0,), False),
            (Node.create(0, 1, 0o500, "directory"), 1, (0,), False),
            (Node.create(0, 1, 0o400, "directory"), 1, (0,), False),
            (Node.create(0, 1, 0o300, "directory"), 1, (0,), False),
            (Node.create(0, 1, 0o200, "directory"), 1, (0,), False),
            (Node.create(0, 1, 0o100, "directory"), 1, (0,), False),
            (Node.create(0, 1, 0o000, "directory"), 1, (0,), False),
            (Node.create(1, 1, 0o700, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o600, "directory"), 1, (0,), False),
            (Node.create(1, 1, 0o500, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o400, "directory"), 1, (0,), False),
            (Node.create(1, 1, 0o300, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o200, "directory"), 1, (0,), False),
            (Node.create(1, 1, 0o100, "directory"), 1, (0,), True),
            (Node.create(1, 1, 0o000, "directory"), 1, (0,), False),
            (Node.create(0, 0, 0o700, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o600, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o500, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o400, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o300, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o200, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o100, "directory"), 1, (1,), False),
            (Node.create(0, 0, 0o000, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o700, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o600, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o500, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o400, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o300, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o200, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o100, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o000, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o700, "directory"), 1, (1,), True),
            (Node.create(1, 1, 0o600, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o500, "directory"), 1, (1,), True),
            (Node.create(1, 1, 0o400, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o300, "directory"), 1, (1,), True),
            (Node.create(1, 1, 0o200, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o100, "directory"), 1, (1,), True),
            (Node.create(1, 1, 0o000, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o070, "directory"), 1, (1,), True),
            (Node.create(0, 1, 0o060, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o050, "directory"), 1, (1,), True),
            (Node.create(0, 1, 0o040, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o030, "directory"), 1, (1,), True),
            (Node.create(0, 1, 0o020, "directory"), 1, (1,), False),
            (Node.create(0, 1, 0o010, "directory"), 1, (1,), True),
            (Node.create(0, 1, 0o000, "directory"), 1, (1,), False),
            (Node.create(1, 1, 0o700, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o600, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o500, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o400, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o300, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o200, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o100, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o000, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o007, "directory"), 2, (2,), True),
            (Node.create(1, 1, 0o006, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o005, "directory"), 2, (2,), True),
            (Node.create(1, 1, 0o004, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o003, "directory"), 2, (2,), True),
            (Node.create(1, 1, 0o002, "directory"), 2, (2,), False),
            (Node.create(1, 1, 0o001, "directory"), 2, (2,), True),
            (Node.create(1, 1, 0o000, "directory"), 2, (2,), False),
    ))
    def test_may_execute(self, node, uid, gids, expected):
        assert node.may_execute(uid, gids) == expected


class TestFileSystem(object):
    @pytest.fixture
    def file_system(self):
        hierarchy = Node.create(0, 0, 0o755, "directory", {
            "bin": Node.create(0, 0, 0o755, "directory", {
                "test": Node.create(0, 0, 0o755, "file", Node.uuid("/bin/test")),
                "badexec": Node.create(0, 0, 0o755, "file", Node.uuid("/bin/badexec")),
                "badperm": Node.create(0, 0, 0o644, "file", Node.uuid("/bin/badperm"))
            }),
            "dev": Node.create(0, 0, 0o755, "directory", {
                "null": Node.create(0, 0, 0o666, "special", Node.uuid("/dev/null"))
            }),
            "etc": Node.create(0, 0, 0o755, "directory", {
                "passwd": Node.create(0, 0, 0o644, "file", Node.uuid("/etc/passwd")),
                "shadow": Node.create(0, 0, 0o000, "file", Node.uuid("/etc/shadow"))
            }),
            "home": Node.create(0, 0, 0o755, "directory", {
                "test": Node.create(1000, 1000, 0o700, "directory", {
                    ".profile": Node.create(1000, 1000, 0o640, "file", Node.uuid("/home/test/.profile"))
                })
            }),
            "sbin": Node.create(0, 0, 0o755, "directory", Node.uuid("/sbin"))
        })
        database = {
            Node.uuid("/bin/test"): (lambda a: 0),
            Node.uuid("/bin/badexec"): "This is a pretend executable file.",
            Node.uuid("/bin/badperm"): (lambda a: 0),
            Node.uuid("/dev/null"): None,
            Node.uuid("/etc/passwd"): {
                "root": {"password": "x", "uid": 0, "gid": 0, "gecos": "root", "home": "/root", "shell": "/bin/sh"},
                "test": {"password": "x", "uid": 1000, "gid": 1000, "gecos": "test", "home": "/home/test", "shell": "/bin/sh"}
            },
            Node.uuid("/etc/shadow"): {
                "root": {"password": "!", "changed": 0, "minimum": None, "maximum": None, "warn": None, "inactive": None, "expire": None},
                "test": {"password": "!", "changed": 0, "minimum": None, "maximum": None, "warn": None, "inactive": None, "expire": None}
            }
        }
        return FileSystem(hierarchy, database, "/", "/")

    def test_find_node_signature(self, file_system):
        nodes = file_system._find_node("/etc/shadow")
        assert isinstance(nodes, tuple) and all(isinstance(n, Node) for n in nodes)

    def test_find_node_badfile(self, file_system):
        with pytest.raises(FileNotFoundError):
            file_system._find_node("/etc/badfile")

    def test_find_node_baddir(self, file_system):
        with pytest.raises(FileNotFoundError):
            file_system._find_node("/baddir/ignored")

    def test_find_node_file_as_dir(self, file_system):
        with pytest.raises(NotADirectoryError):
            file_system._find_node("/etc/passwd/ignored")

    def test_find_node_special_as_dir(self, file_system):
        with pytest.raises(NotADirectoryError):
            file_system._find_node("/dev/null/ignored")

    def test_stat_signature(self, file_system):
        assert isinstance(file_system.stat(0, (0,), "/etc/shadow"), dict)

    def test_stat_good_perm(self, file_system):
        file_system.stat(1, (1,), "/etc/shadow")

    def test_stat_bad_perm(self, file_system):
        with pytest.raises(PermissionError):
            file_system.stat(1, (1,), "/home/test/.profile")

    def test_list_signature(self, file_system):
        assert isinstance(file_system.list(0, (0,), "/etc"), dict)

    def test_list_good_perm(self, file_system):
        file_system.list(1, (1,), "/etc")

    def test_list_bad_perm(self, file_system):
        with pytest.raises(PermissionError):
            file_system.list(1, (1,), "/home/test")

    def test_list_file(self, file_system):
        with pytest.raises(NotADirectoryError):
            file_system.list(1, (1,), "/etc/passwd")

    def test_list_special(self, file_system):
        with pytest.raises(NotADirectoryError):
            file_system.list(1, (1,), "/dev/null")

    @pytest.mark.xfail(raises=NotImplementedError)
    def test_list_dir_link(self, file_system):
        file_system.list(1, (1,), "/sbin")

    def test_read_signature(self, file_system):
        assert file_system.read(0, (0,), "/etc/passwd") == file_system._database[Node.uuid("/etc/passwd")]

    def test_read_good_perm(self, file_system):
        file_system.read(1, (1,), "/etc/passwd")

    def test_read_bad_perm(self, file_system):
        with pytest.raises(PermissionError):
            file_system.read(1, (1,), "/etc/shadow")

    def test_read_dir(self, file_system):
        with pytest.raises(IsADirectoryError):
            file_system.read(1, (1,), "/etc")
