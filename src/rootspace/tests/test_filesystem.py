# -*- coding: utf-8 -*-

import itertools
import json
import uuid
import warnings

import pytest
from rootspace.exceptions import RootspacePermissionError, RootspaceFileNotFoundError, FixmeWarning
from rootspace.filesystem import Node, DirectoryNode, FileNode, FileSystem


class TestNode(object):
    def test_instantiation(self):
        parent = Node(0, 0, 0)
        Node(0, 0, 0, parent=parent)

    def test_from_dict(self):
        s = {"uid": 0, "gid": 0, "perm": 0o755, "accessed": 0.0, "modified": 0.0, "changed": 0.0}
        assert isinstance(Node.from_dict(s), Node)

    def test_to_dict(self):
        value = Node(0, 0, 0o755).to_dict(0, (0,))
        assert isinstance(value, dict)
        assert isinstance(json.dumps(value), str)

    def test_serialisation(self):
        s = {"uid": 0, "gid": 0, "perm": 0o755, "accessed": 0.0, "modified": 0.0, "changed": 0.0}
        n = Node.from_dict(s)

        assert s == n.to_dict(0, (0,))

    def test_perm_str(self):
        assert isinstance(Node(0, 0, 0)._perm_str(), str)

    def test_may_read(self):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)

        def exp_read(nuid, ngid, nperm, uid, gid):
            perm_bits = (
                ((nperm // 64) // 4) > 0,
                (((nperm % 64) // 8) // 4) > 0,
                ((nperm % 8) // 4) > 0
            )
            privileged = (uid == 0)
            user_perm = (uid == nuid and perm_bits[0])
            group_perm = (gid == ngid and perm_bits[1])
            other_perm = perm_bits[2]

            return privileged or user_perm or group_perm or other_perm

        for nu, ng, np, u, g in itertools.product(uids, gids, perms, uids, gids):
            assert Node(nu, ng, np).may_read(u, (g,)) == exp_read(nu, ng, np, u, g)

    def test_may_write(self):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)

        def exp_write(nuid, ngid, nperm, uid, gid):
            perm_bits = (
                (((nperm // 64) % 4) // 2) > 0,
                ((((nperm % 64) // 8) % 4) // 2) > 0,
                (((nperm % 8) % 4) // 2) > 0
            )
            privileged = (uid == 0)
            user_perm = (uid == nuid and perm_bits[0])
            group_perm = (gid == ngid and perm_bits[1])
            other_perm = perm_bits[2]

            return privileged or user_perm or group_perm or other_perm

        for nu, ng, np, u, g in itertools.product(uids, gids, perms, uids, gids):
            assert Node(nu, ng, np).may_write(u, (g,)) == exp_write(nu, ng, np, u, g)

    def test_may_execute(self):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)

        def exp_exec(nuid, ngid, nperm, uid, gid):
            perm_bits = (
                ((nperm // 64) % 2) > 0,
                (((nperm % 64) // 8) % 2) > 0,
                ((nperm % 8) % 2) > 0
            )
            privileged = (uid == 0 and any(perm_bits))
            user_perm = (uid == nuid and perm_bits[0])
            group_perm = (gid == ngid and perm_bits[1])
            other_perm = perm_bits[2]

            return privileged or user_perm or group_perm or other_perm
        for nu, ng, np, u, g in itertools.product(uids, gids, perms, uids, gids):
            assert Node(nu, ng, np).may_execute(u, (g,)) == exp_exec(nu, ng, np, u, g)

    def test_modify_parent_perm(self):
        parents = (Node(0, 0, 0o000), Node(0, 0, 0o755))
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)

        for pa, nu, ng, np, u, g, npa in itertools.product(parents, uids, gids, perms, uids, gids, parents):
            if pa is None or pa.may_write(u, (g,)):
                Node(nu, ng, np, parent=pa).modify_parent(u, (g,), npa)
            else:
                with pytest.raises(RootspacePermissionError):
                    Node(nu, ng, np, parent=pa).modify_parent(u, (g,), npa)

    def test_modify_parent_input(self):
        for npa in (None, int(), float(), str(), dict(), list(), tuple(), set(), object()):
            with pytest.raises(TypeError):
                Node(0, 0, 0).modify_parent(0, (0,), npa)

    def test_modify_uid_perm(self):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)
        new_uids = (0,)

        for nu, ng, np, u, g, uu in itertools.product(uids, gids, perms, uids, gids, new_uids):
            if u == 0 or u == nu:
                Node(nu, ng, np).modify_uid(u, (g,), uu)
            else:
                with pytest.raises(RootspacePermissionError):
                    Node(nu, ng, np).modify_uid(u, (g,), uu)

    def test_modify_uid_input(self):
        for uu in (None, float(), str(), dict(), list(), tuple(), set(), object()):
            with pytest.raises(TypeError):
                Node(0, 0, 0).modify_uid(0, (0,), uu)

    def test_modify_gid_perm(self):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)
        new_gids = (0,)

        for nu, ng, np, u, g, gg in itertools.product(uids, gids, perms, uids, gids, new_gids):
            if u == 0 or u == nu:
                Node(nu, ng, np).modify_gid(u, (g,), gg)
            else:
                with pytest.raises(RootspacePermissionError):
                    Node(nu, ng, np).modify_gid(u, (g,), gg)

    def test_modify_gid_input(self):
        for gg in (None, float(), str(), dict(), list(), tuple(), set(), object()):
            with pytest.raises(TypeError):
                Node(0, 0, 0).modify_gid(0, (0,), gg)

    def test_modify_perm_perm(self):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)
        new_perms = (0,)

        for nu, ng, np, u, g, pp in itertools.product(uids, gids, perms, uids, gids, new_perms):
            if u == 0 or u == nu:
                Node(nu, ng, np).modify_perm(u, (g,), pp)
            else:
                with pytest.raises(RootspacePermissionError):
                    Node(nu, ng, np).modify_perm(u, (g,), pp)

    def test_modify_perm_input(self):
        for pp in (None, float(), str(), dict(), list(), tuple(), set(), object()):
            with pytest.raises(TypeError):
                Node(0, 0, 0).modify_perm(0, (0,), pp)

    def test_stat_perm(self):
        parents = (None, Node(0, 0, 0o755))
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)

        for pa, nu, ng, np, u, g in itertools.product(parents, uids, gids, perms, uids, gids):
            if pa is None or pa.may_read(u, (g,)):
                Node(nu, ng, np, parent=pa).stat(u, (g,))
            else:
                with pytest.raises(RootspacePermissionError):
                    Node(pa, nu, ng, np, parent=pa).stat(u, (g,))

    def test_stat_value(self):
        value = Node(0, 0, 0o755).stat(0, (0,))
        assert isinstance(value, dict)
        assert all(k in value for k in ("uid", "gid", "perm", "accessed", "modified", "changed"))


class TestDirectoryNode(object):
    def test_from_dict(self):
        s = {"uid": 0, "gid": 0, "perm": 0o755, "accessed": 0.0, "modified": 0.0, "changed": 0.0, "contents": {}}
        assert isinstance(DirectoryNode.from_dict(s), Node)

    def test_to_dict(self):
        value = DirectoryNode(0, 0, 0o755).to_dict(0, (0,))
        assert isinstance(value, dict)
        assert isinstance(json.dumps(value), str)

    def test_serialisation(self):
        s = {"uid": 0, "gid": 0, "perm": 0o755, "accessed": 0.0, "modified": 0.0, "changed": 0.0, "contents": {}}
        n = DirectoryNode.from_dict(s)

        assert s == n.to_dict(0, (0,))

    def test_list_perm(self):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)

        for u, g in itertools.product(uids, gids):
            node = DirectoryNode(0, 1, 0o750)

            if node.may_read(u, (g,)):
                node.list(u, (g,))
            else:
                with pytest.raises(RootspacePermissionError):
                    node.list(u, (g,))

    def test_list_value(self):
        parent = DirectoryNode(0, 0, 0o755)
        child = DirectoryNode(0, 0, 0o755, parent=parent)

        value = parent.list(0, (0,))
        assert isinstance(value, dict)
        assert "." in value and ".." not in value
        assert isinstance(value["."], dict)
        assert value["."] == parent.stat(0, (0,))

        value2 = child.list(0, (0,))
        assert isinstance(value2, dict)
        assert "." in value2 and ".." in value2

    def test_insert_node_perm(self):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)

        for u, g in itertools.product(uids, gids):
            node = DirectoryNode(0, 1, 0o750)
            child = DirectoryNode(0, 1, 0o750)

            if node.may_write(u, (g,)):
                node.insert_node(u, (g,), "child", child)
            else:
                with pytest.raises(RootspacePermissionError):
                    node.insert_node(u, (g,), "child", child)

    def test_insert_node_input(self):
        for pp in (None, int(), float(), str(), dict(), list(), tuple(), set(), object()):
            with pytest.raises(TypeError):
                DirectoryNode(0, 0, 0).insert_node(0, (0,), "child", pp)

    def test_remove_node_perm(self):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)

        for u, g in itertools.product(uids, gids):
            node = DirectoryNode(0, 1, 0o750)
            child = DirectoryNode(0, 1, 0o750)
            node.insert_node(0, (0,), "child", child)

            if node.may_write(u, (g,)):
                node.remove_node(u, (g,), "child")
            else:
                with pytest.raises(RootspacePermissionError):
                    node.remove_node(u, (g,), "child")

    def test_remove_node_badfile(self):
        with pytest.raises(RootspaceFileNotFoundError):
            DirectoryNode(0, 0, 0o755).remove_node(0, (0,), "child")

    def test_move_node_calls(self, mocker):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)

        mocker.patch("rootspace.filesystem.DirectoryNode.insert_node")
        mocker.patch("rootspace.filesystem.DirectoryNode.remove_node")

        for u, g in itertools.product(uids, gids):
            parent_a = DirectoryNode(0, 1, 0o750)
            parent_b = DirectoryNode(0, 1, 0o750)
            child = DirectoryNode(0, 1, 0o750, parent=parent_a)
            parent_a._contents["child"] = child

            parent_a.move_node(u, (g,), "child", parent_b, "new_child")

            assert parent_b.insert_node.call_count == 1
            assert parent_a.remove_node.call_count == 1

            mocker.resetall()

    def test_move_node_input(self):
        for pp in (None, int(), float(), str(), dict(), list(), tuple(), set(), object()):
            with pytest.raises(TypeError):
                DirectoryNode(0, 0, 0).move_node(0, (0,), "some", pp, "other")


class TestFileNode(object):
    def test_from_dict(self):
        src = str(uuid.uuid5(uuid.NAMESPACE_URL, "/path"))
        s = {"uid": 0, "gid": 0, "perm": 0o644, "accessed": 0.0, "modified": 0.0, "changed": 0.0, "source": src}
        assert isinstance(FileNode.from_dict(s), Node)

    def test_to_dict(self):
        value = FileNode(0, 0, 0o644).to_dict(0, (0,))
        assert isinstance(value, dict)
        assert isinstance(json.dumps(value), str)

    def test_serialisation(self):
        src = str(uuid.uuid5(uuid.NAMESPACE_URL, "/path"))
        s = {"uid": 0, "gid": 0, "perm": 0o644, "accessed": 0.0, "modified": 0.0, "changed": 0.0, "source": src}
        n = FileNode.from_dict(s)

        assert s == n.to_dict(0, (0,))

    def test_get_source_perm(self):
        parents = (None, DirectoryNode(0, 0, 0o000), DirectoryNode(0, 0, 0o755))
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)

        for p, u, g in itertools.product(parents, uids, gids):
            if p is None or p.may_execute(u, (g,)):
                FileNode(u, g, 0o644, parent=p).get_source(u, (g,))
            else:
                with pytest.raises(RootspacePermissionError):
                    FileNode(u, g, 0o644, parent=p).get_source(u, (g,))

    def test_get_source_value_and_signature(self):
        node = FileNode(0, 0, 0o644)
        assert node.get_source(0, (0,)) == str(node._source)
        assert node.get_source(0, (0,), as_string=True) == str(node._source)
        assert node.get_source(0, (0,), as_string=False) == node._source


class TestFileSystem(object):
    def test_generate_unix(self, tmpdir):
        assert isinstance(FileSystem.generate_unix(str(tmpdir.join("db"))), FileSystem)

    def test_split_input(self):
        warnings.warn("This test needs to fuzz the split method.", FixmeWarning)
        FileSystem("")._split("/")

    def test_split_value(self):
        warnings.warn("This test needs to fuzz the separate method.", FixmeWarning)
        value = FileSystem("")._split("/")
        assert isinstance(value, tuple)
        assert all(isinstance(el, str) for el in value) or len(value) == 0

    def test_separate_calls(self, mocker):
        mocker.patch("rootspace.filesystem.FileSystem._split")

        input_path = "/"
        fs = FileSystem("")
        fs._separate(input_path)

        fs._split.assert_called_once_with(input_path)

    @pytest.mark.parametrize(("path", "expected"), (
        ("/directory/basename", ("/directory", "basename")),
        ("/", ("/", ""))
    ))
    def test_separate_value(self, path, expected):
        assert FileSystem("")._separate(path) == expected

