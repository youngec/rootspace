# -*- coding: utf-8 -*-

import itertools

import pytest

from rootspace.exceptions import RootspacePermissionError
from rootspace.filesystem import Node, FileSystem


class TestNode(object):
    def test_instantiation(self):
        parent = Node(None, 0, 0, 0)
        Node(parent, 0, 0, 0)

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
            assert Node(None, nu, ng, np).may_read(u, (g,)) == exp_read(nu, ng, np, u, g)

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
            assert Node(None, nu, ng, np).may_write(u, (g,)) == exp_write(nu, ng, np, u, g)

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
            assert Node(None, nu, ng, np).may_execute(u, (g,)) == exp_exec(nu, ng, np, u, g)

    def test_modify_parent_perm(self):
        parents = (Node(None, 0, 0, 0o000), Node(None, 0, 0, 0o755))
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)

        for pa, nu, ng, np, u, g, npa in itertools.product(parents, uids, gids, perms, uids, gids, parents):
            if pa is None or pa.may_write(u, (g,)):
                Node(pa, nu, ng, np).modify_parent(u, (g,), npa)
            else:
                with pytest.raises(RootspacePermissionError):
                    Node(pa, nu, ng, np).modify_parent(u, (g,), npa)

    def test_modify_parent_input(self):
        for npa in (None, int(), float(), str(), dict(), list(), tuple(), set(), object()):
            with pytest.raises(TypeError):
                Node(None, 0, 0, 0).modify_parent(0, (0,), npa)

    def test_modify_uid_perm(self):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)
        new_uids = (0,)

        for nu, ng, np, u, g, uu in itertools.product(uids, gids, perms, uids, gids, new_uids):
            if u == 0 or u == nu:
                Node(None, nu, ng, np).modify_uid(u, (g,), uu)
            else:
                with pytest.raises(RootspacePermissionError):
                    Node(None, nu, ng, np).modify_uid(u, (g,), uu)

    def test_modify_uid_input(self):
        for uu in (None, float(), str(), dict(), list(), tuple(), set(), object()):
            with pytest.raises(TypeError):
                Node(None, 0, 0, 0).modify_uid(0, (0,), uu)

    def test_modify_gid_perm(self):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)
        new_gids = (0,)

        for nu, ng, np, u, g, gg in itertools.product(uids, gids, perms, uids, gids, new_gids):
            if u == 0 or u == nu:
                Node(None, nu, ng, np).modify_gid(u, (g,), gg)
            else:
                with pytest.raises(RootspacePermissionError):
                    Node(None, nu, ng, np).modify_gid(u, (g,), gg)

    def test_modify_gid_input(self):
        for gg in (None, float(), str(), dict(), list(), tuple(), set(), object()):
            with pytest.raises(TypeError):
                Node(None, 0, 0, 0).modify_gid(0, (0,), gg)

    def test_modify_perm_perm(self):
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)
        new_perms = (0,)

        for nu, ng, np, u, g, pp in itertools.product(uids, gids, perms, uids, gids, new_perms):
            if u == 0 or u == nu:
                Node(None, nu, ng, np).modify_perm(u, (g,), pp)
            else:
                with pytest.raises(RootspacePermissionError):
                    Node(None, nu, ng, np).modify_perm(u, (g,), pp)

    def test_modify_perm_input(self):
        for pp in (None, float(), str(), dict(), list(), tuple(), set(), object()):
            with pytest.raises(TypeError):
                Node(None, 0, 0, 0).modify_perm(0, (0,), pp)

    def test_stat_perm(self):
        parents = (None, Node(None, 0, 0, 0o755))
        uids = (0, 1, 1000)
        gids = (0, 1, 1000)
        perms = range(512)

        for pa, nu, ng, np, u, g in itertools.product(parents, uids, gids, perms, uids, gids):
            if pa is None or pa.may_read(u, (g,)):
                Node(pa, nu, ng, np).stat(u, (g,))
            else:
                with pytest.raises(RootspacePermissionError):
                    Node(pa, nu, ng, np).stat(u, (g,))

    def test_stat_value(self):
        value = Node(None, 0, 0, 0o755).stat(0, (0,))
        assert isinstance(value, dict)
        assert all(k in value for k in ("uid", "gid", "perm", "accessed", "modified", "changed"))


class TestDirectoryNode(object):
    pass


class TestFileNode(object):
    pass


class TestLinkNode(object):
    pass


class TestFileSystem(object):
    pass
