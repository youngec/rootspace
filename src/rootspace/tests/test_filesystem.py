# -*- coding: utf-8 -*-

import uuid

import pytest

from rootspace.filesystem import Node, FileSystem


class TestNode(object):
    def test_node(self):
        # The following two statements must work.
        Node(0, 0, 0o755, Node.FileType.directory, {})
        Node(0, 0, 0o644, Node.FileType.directory, uuid.uuid4())

        # The following must raise TypeErrors.
        with pytest.raises(TypeError):
            Node(None, 0, 0o755, Node.FileType.directory, {})
        with pytest.raises(TypeError):
            Node(0, None, 0o755, Node.FileType.directory, {})
        with pytest.raises(TypeError):
            Node(0, 0, None, Node.FileType.directory, {})
        with pytest.raises(TypeError):
            Node(0, 0, 0o755, None, {})
        with pytest.raises(TypeError):
            Node(0, 0, 0o755, Node.FileType.directory, None)

    def test_uid(self):
        node = Node(0, 0, 0o755, Node.FileType.directory, {})
        assert isinstance(node.uid, int)

    def test_gid(self):
        node = Node(0, 0, 0o755, Node.FileType.directory, {})
        assert isinstance(node.gid, int)

    def test_perm(self):
        node = Node(0, 0, 0o755, Node.FileType.directory, {})
        assert isinstance(node.perm, int)
        assert isinstance(node.perm_str, str)

    @pytest.mark.parametrize(("node", "expected"), (
            (Node(0, 0, 0o755, Node.FileType.directory, {}), True),
            (Node(0, 0, 0o644, Node.FileType.file, uuid.uuid4()), False),
            (Node(0, 0, 0o666, Node.FileType.special, uuid.uuid4()), False)
    ))
    def test_is_directory(self, node, expected):
        assert node.is_directory == expected

    @pytest.mark.parametrize(("node", "expected"), (
            (Node(0, 0, 0o755, Node.FileType.directory, {}), False),
            (Node(0, 0, 0o644, Node.FileType.file, uuid.uuid4()), True),
            (Node(0, 0, 0o666, Node.FileType.special, uuid.uuid4()), False)
    ))
    def test_is_file(self, node, expected):
        assert node.is_file == expected

    @pytest.mark.parametrize(("node", "expected"), (
            (Node(0, 0, 0o755, Node.FileType.directory, {}), False),
            (Node(0, 0, 0o644, Node.FileType.file, uuid.uuid4()), False),
            (Node(0, 0, 0o666, Node.FileType.special, uuid.uuid4()), True)
    ))
    def test_is_special(self, node, expected):
        assert node.is_special == expected

    @pytest.mark.parametrize(("node", "expected"), (
            (Node(0, 0, 0o755, Node.FileType.directory, {}), dict),
            (Node(0, 0, 0o755, Node.FileType.file, uuid.uuid4()), uuid.UUID)
    ))
    def test_contents(self, node, expected):
        assert isinstance(node.contents, expected)

    @pytest.mark.parametrize(("node", "uid", "gids", "expected"), (
            (Node(0, 0, 0o700, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o600, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o500, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o400, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o300, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o200, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o100, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o000, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o700, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o600, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o500, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o400, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o300, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o200, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o100, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o000, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o700, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o600, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o500, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o400, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o300, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o200, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o100, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o700, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o600, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o500, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o400, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o300, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o200, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o100, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o000, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o700, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o600, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o500, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o400, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o300, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o200, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o100, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o000, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o700, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o600, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o500, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o400, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o300, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o200, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o100, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o700, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o600, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o500, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o400, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o300, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o200, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o100, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o000, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o700, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o600, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o500, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o400, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o300, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o200, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o100, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o000, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o700, Node.FileType.directory, {}), 1, (1,), True),
            (Node(1, 1, 0o600, Node.FileType.directory, {}), 1, (1,), True),
            (Node(1, 1, 0o500, Node.FileType.directory, {}), 1, (1,), True),
            (Node(1, 1, 0o400, Node.FileType.directory, {}), 1, (1,), True),
            (Node(1, 1, 0o300, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o200, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o100, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o070, Node.FileType.directory, {}), 1, (1,), True),
            (Node(0, 1, 0o060, Node.FileType.directory, {}), 1, (1,), True),
            (Node(0, 1, 0o050, Node.FileType.directory, {}), 1, (1,), True),
            (Node(0, 1, 0o040, Node.FileType.directory, {}), 1, (1,), True),
            (Node(0, 1, 0o030, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o020, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o010, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o000, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o700, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o600, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o500, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o400, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o300, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o200, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o100, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o007, Node.FileType.directory, {}), 2, (2,), True),
            (Node(1, 1, 0o006, Node.FileType.directory, {}), 2, (2,), True),
            (Node(1, 1, 0o005, Node.FileType.directory, {}), 2, (2,), True),
            (Node(1, 1, 0o004, Node.FileType.directory, {}), 2, (2,), True),
            (Node(1, 1, 0o003, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o002, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o001, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 2, (2,), False),
    ))
    def test_may_read(self, node, uid, gids, expected):
        assert node.may_read(uid, gids) == expected

    @pytest.mark.parametrize(("node", "uid", "gids", "expected"), (
            (Node(0, 0, 0o700, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o600, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o500, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o400, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o300, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o200, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o100, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o000, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o700, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o600, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o500, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o400, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o300, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o200, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o100, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o000, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o700, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o600, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o500, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o400, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o300, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o200, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o100, Node.FileType.directory, {}), 0, (0,), True),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o700, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o600, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o500, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o400, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o300, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o200, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o100, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o000, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o700, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o600, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o500, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o400, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o300, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o200, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o100, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 1, 0o000, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o700, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o600, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o500, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o400, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o300, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o200, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o100, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 1, (0,), True),
            (Node(0, 0, 0o700, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o600, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o500, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o400, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o300, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o200, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o100, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o000, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o700, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o600, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o500, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o400, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o300, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o200, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o100, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o000, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o700, Node.FileType.directory, {}), 1, (1,), True),
            (Node(1, 1, 0o600, Node.FileType.directory, {}), 1, (1,), True),
            (Node(1, 1, 0o500, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o400, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o300, Node.FileType.directory, {}), 1, (1,), True),
            (Node(1, 1, 0o200, Node.FileType.directory, {}), 1, (1,), True),
            (Node(1, 1, 0o100, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o070, Node.FileType.directory, {}), 1, (1,), True),
            (Node(0, 1, 0o060, Node.FileType.directory, {}), 1, (1,), True),
            (Node(0, 1, 0o050, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o040, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o030, Node.FileType.directory, {}), 1, (1,), True),
            (Node(0, 1, 0o020, Node.FileType.directory, {}), 1, (1,), True),
            (Node(0, 1, 0o010, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o000, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o700, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o600, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o500, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o400, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o300, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o200, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o100, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o007, Node.FileType.directory, {}), 2, (2,), True),
            (Node(1, 1, 0o006, Node.FileType.directory, {}), 2, (2,), True),
            (Node(1, 1, 0o005, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o004, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o003, Node.FileType.directory, {}), 2, (2,), True),
            (Node(1, 1, 0o002, Node.FileType.directory, {}), 2, (2,), True),
            (Node(1, 1, 0o001, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 2, (2,), False),
    ))
    def test_may_write(self, node, uid, gids, expected):
        assert node.may_write(uid, gids) == expected

    @pytest.mark.parametrize(("node", "uid", "gids", "expected"), (
            (Node(0, 0, 0o700, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o600, Node.FileType.directory, {}), 0, (0,), False),
            (Node(0, 0, 0o500, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o400, Node.FileType.directory, {}), 0, (0,), False),
            (Node(0, 0, 0o300, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o200, Node.FileType.directory, {}), 0, (0,), False),
            (Node(0, 0, 0o100, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 0, 0o000, Node.FileType.directory, {}), 0, (0,), False),
            (Node(0, 1, 0o700, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o600, Node.FileType.directory, {}), 0, (0,), False),
            (Node(0, 1, 0o500, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o400, Node.FileType.directory, {}), 0, (0,), False),
            (Node(0, 1, 0o300, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o200, Node.FileType.directory, {}), 0, (0,), False),
            (Node(0, 1, 0o100, Node.FileType.directory, {}), 0, (0,), True),
            (Node(0, 1, 0o000, Node.FileType.directory, {}), 0, (0,), False),
            (Node(1, 1, 0o700, Node.FileType.directory, {}), 0, (0,), False),
            (Node(1, 1, 0o600, Node.FileType.directory, {}), 0, (0,), False),
            (Node(1, 1, 0o500, Node.FileType.directory, {}), 0, (0,), False),
            (Node(1, 1, 0o400, Node.FileType.directory, {}), 0, (0,), False),
            (Node(1, 1, 0o300, Node.FileType.directory, {}), 0, (0,), False),
            (Node(1, 1, 0o200, Node.FileType.directory, {}), 0, (0,), False),
            (Node(1, 1, 0o100, Node.FileType.directory, {}), 0, (0,), False),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 0, (0,), False),
            (Node(0, 0, 0o700, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 0, 0o600, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 0, 0o500, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 0, 0o400, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 0, 0o300, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 0, 0o200, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 0, 0o100, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 0, 0o000, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 1, 0o700, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 1, 0o600, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 1, 0o500, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 1, 0o400, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 1, 0o300, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 1, 0o200, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 1, 0o100, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 1, 0o000, Node.FileType.directory, {}), 1, (0,), False),
            (Node(1, 1, 0o700, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o600, Node.FileType.directory, {}), 1, (0,), False),
            (Node(1, 1, 0o500, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o400, Node.FileType.directory, {}), 1, (0,), False),
            (Node(1, 1, 0o300, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o200, Node.FileType.directory, {}), 1, (0,), False),
            (Node(1, 1, 0o100, Node.FileType.directory, {}), 1, (0,), True),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 1, (0,), False),
            (Node(0, 0, 0o700, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o600, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o500, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o400, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o300, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o200, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o100, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 0, 0o000, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o700, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o600, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o500, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o400, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o300, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o200, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o100, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o000, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o700, Node.FileType.directory, {}), 1, (1,), True),
            (Node(1, 1, 0o600, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o500, Node.FileType.directory, {}), 1, (1,), True),
            (Node(1, 1, 0o400, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o300, Node.FileType.directory, {}), 1, (1,), True),
            (Node(1, 1, 0o200, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o100, Node.FileType.directory, {}), 1, (1,), True),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o070, Node.FileType.directory, {}), 1, (1,), True),
            (Node(0, 1, 0o060, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o050, Node.FileType.directory, {}), 1, (1,), True),
            (Node(0, 1, 0o040, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o030, Node.FileType.directory, {}), 1, (1,), True),
            (Node(0, 1, 0o020, Node.FileType.directory, {}), 1, (1,), False),
            (Node(0, 1, 0o010, Node.FileType.directory, {}), 1, (1,), True),
            (Node(0, 1, 0o000, Node.FileType.directory, {}), 1, (1,), False),
            (Node(1, 1, 0o700, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o600, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o500, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o400, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o300, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o200, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o100, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o007, Node.FileType.directory, {}), 2, (2,), True),
            (Node(1, 1, 0o006, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o005, Node.FileType.directory, {}), 2, (2,), True),
            (Node(1, 1, 0o004, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o003, Node.FileType.directory, {}), 2, (2,), True),
            (Node(1, 1, 0o002, Node.FileType.directory, {}), 2, (2,), False),
            (Node(1, 1, 0o001, Node.FileType.directory, {}), 2, (2,), True),
            (Node(1, 1, 0o000, Node.FileType.directory, {}), 2, (2,), False),
    ))
    def test_may_execute(self, node, uid, gids, expected):
        assert node.may_execute(uid, gids) == expected


class TestFileSystem(object):
    @pytest.fixture
    def file_system(self):
        hierarchy = Node(0, 0, 0o755, Node.FileType.directory, {
            "bin": Node(0, 0, 0o755, Node.FileType.directory, {
                "test": Node(0, 0, 0o755, Node.FileType.file, uuid.uuid5(uuid.NAMESPACE_URL, "/bin/test")),
                "badexec": Node(0, 0, 0o755, Node.FileType.file, uuid.uuid5(uuid.NAMESPACE_URL, "/bin/badexec")),
                "badperm": Node(0, 0, 0o644, Node.FileType.file, uuid.uuid5(uuid.NAMESPACE_URL, "/bin/badperm"))
            }),
            "dev": Node(0, 0, 0o755, Node.FileType.directory, {
                "null": Node(0, 0, 0o666, Node.FileType.special, uuid.uuid5(uuid.NAMESPACE_URL, "/dev/null"))
            }),
            "etc": Node(0, 0, 0o755, Node.FileType.directory, {
                "passwd": Node(0, 0, 0o644, Node.FileType.file, uuid.uuid5(uuid.NAMESPACE_URL, "/etc/passwd")),
                "shadow": Node(0, 0, 0o000, Node.FileType.file, uuid.uuid5(uuid.NAMESPACE_URL, "/etc/shadow"))
            }),
            "home": Node(0, 0, 0o755, Node.FileType.directory, {
                "test": Node(1000, 1000, 0o700, Node.FileType.directory, {
                    ".profile": Node(1000, 1000, 0o640, Node.FileType.file, uuid.uuid5(uuid.NAMESPACE_URL, "/home/test/.profile"))
                })
            }),
        })
        database = {
            uuid.uuid5(uuid.NAMESPACE_URL, "/bin/test"): (lambda a: 0),
            uuid.uuid5(uuid.NAMESPACE_URL, "/bin/badexec"): "This is a pretend executable file.",
            uuid.uuid5(uuid.NAMESPACE_URL, "/bin/badperm"): (lambda a: 0),
            uuid.uuid5(uuid.NAMESPACE_URL, "/dev/null"): None,
            uuid.uuid5(uuid.NAMESPACE_URL, "/etc/passwd"): {
                "root": {"password": "x", "uid": 0, "gid": 0, "gecos": "root", "home": "/root", "shell": "/bin/sh"},
                "test": {"password": "x", "uid": 1000, "gid": 1000, "gecos": "test", "home": "/home/test", "shell": "/bin/sh"}
            },
            uuid.uuid5(uuid.NAMESPACE_URL, "/etc/shadow"): {
                "root": {"password": "!", "changed": 0, "minimum": None, "maximum": None, "warn": None, "inactive": None, "expire": None},
                "test": {"password": "!", "changed": 0, "minimum": None, "maximum": None, "warn": None, "inactive": None, "expire": None}
            }
        }
        return FileSystem(hierarchy, database, "/", "/")

    def test_find_node(self, file_system):
        nodes = file_system._find_node("/etc/shadow")
        assert isinstance(nodes, tuple) and all(isinstance(n, Node) for n in nodes)
        with pytest.raises(FileNotFoundError):
            file_system._find_node("/etc/badfile")
        with pytest.raises(FileNotFoundError):
            file_system._find_node("/baddir/ignored")
        with pytest.raises(NotADirectoryError):
            file_system._find_node("/etc/passwd/ignored")
        with pytest.raises(NotADirectoryError):
            file_system._find_node("/dev/null/ignored")

    def test_stat(self, file_system):
        assert isinstance(file_system.stat(0, (0,), "/etc/shadow"), dict)
        pass
