# -*- coding: utf-8 -*-

import abc
import gzip
import pickle
import datetime
import weakref

import attr
from attr.validators import instance_of

from .exceptions import RootspaceNotAnExecutableError, RootspaceFileNotFoundError, RootspaceNotADirectoryError, RootspacePermissionError
from .utilities import proxy


@attr.s(slots=True)
class Node(object, metaclass=abc.ABCMeta):
    _parent = attr.ib(validator=instance_of((type(None), weakref.ProxyType)), convert=proxy)
    _uid = attr.ib(validator=instance_of(int))
    _gid = attr.ib(validator=instance_of(int))
    _perm = attr.ib(validator=instance_of(int))
    _accessed = attr.ib(default=attr.Factory(datetime.datetime.now), validator=instance_of(datetime.datetime))
    _modified = attr.ib(default=attr.Factory(datetime.datetime.now), validator=instance_of(datetime.datetime))
    _changed = attr.ib(default=attr.Factory(datetime.datetime.now), validator=instance_of(datetime.datetime))

    def _perm_str(self):
        """
        Return the permission data as human-readable string.

        :return:
        """
        perm_digits = (self._perm // 64, (self._perm % 64) // 8, self._perm % 8)
        perm_list = (((p // 4) > 0, ((p % 4) // 2) > 0, (p % 2) > 0) for p in perm_digits)
        perm_groups = ("{}{}{}".format("r" if p[0] else "-", "w" if p[1] else "-", "x" if p[2] else "-") for p in perm_list)
        return "".join(perm_groups)

    def may_read(self, uid, gids):
        """
        Return True if the supplied UID and GIDs have read permission on this node.
        A privileged user (UID 0) always has read access.

        :param uid:
        :param gids:
        :return:
        """
        perm_bits = (
             ((self._perm // 64) // 4) > 0,
             (((self._perm % 64) // 8) // 4) > 0,
             ((self._perm % 8) // 4) > 0
        )
        privileged = (uid == 0)
        user_perm = (uid == self._uid and perm_bits[0])
        group_perm = (any(gid == self._gid for gid in gids) and perm_bits[1])
        other_perm = perm_bits[2]

        return privileged or user_perm or group_perm or other_perm

    def may_write(self, uid, gids):
        """
        Return True if the supplied UID and GIDs have write permission on this node.
        A privileged user (UID 0) always has write access.

        :param uid:
        :param gids:
        :return:
        """
        perm_bits = (
             (((self._perm // 64) % 4) // 2) > 0,
             ((((self._perm % 64) // 8) % 4) // 2) > 0,
             (((self._perm % 8) % 4) // 2) > 0
        )
        privileged = (uid == 0)
        user_perm = (uid == self._uid and perm_bits[0])
        group_perm = (any(gid == self._gid for gid in gids) and perm_bits[1])
        other_perm = perm_bits[2]

        return privileged or user_perm or group_perm or other_perm

    def may_execute(self, uid, gids):
        """
        Return True if the supplied UID and GIDs have execute permission on this node.
        A privileged user (UID 0) has access if any executable bit is set.

        :param uid:
        :param gids:
        :return:
        """
        perm_bits = (
             ((self._perm // 64) % 2) > 0,
             (((self._perm % 64) // 8) % 2) > 0,
             ((self._perm % 8) % 2) > 0
        )
        privileged = (uid == 0 and any(perm_bits))
        user_perm = (uid == self._uid and perm_bits[0])
        group_perm = (any(gid == self._gid for gid in gids) and perm_bits[1])
        other_perm = perm_bits[2]

        return privileged or user_perm or group_perm or other_perm

    def modify_uid(self, uid, gids, new_uid):
        """
        If the supplied UID is the owner of the Node, change the Node owner.
        A privileged user may always change the Node owner.

        :param uid:
        :param gids:
        :param new_uid:
        :return:
        """
        if (uid == 0) or (uid == self._uid):
            self._modified = datetime.datetime.now()
            self._uid = new_uid
        else:
            raise RootspacePermissionError()

    def modify_gid(self, uid, gids, new_gid):
        """
        If the supplied UID is the owner of the Node, change the Node GID.
        A privileged user may always change the Node GID.

        :param uid:
        :param gids:
        :param new_gid:
        :return:
        """
        if (uid == 0) or (uid == self._uid):
            self._modified = datetime.datetime.now()
            self._gid = new_gid
        else:
            raise RootspacePermissionError()

    def modify_perm(self, uid, gids, new_perm):
        """
        If the supplied UID is the owner of the Node, change the Node permissions.
        A privileged user may always change the Node permissions.

        :param uid:
        :param gids:
        :param new_perm:
        :return:
        """
        if (uid == 0) or (uid == self._uid):
            self._modified = datetime.datetime.now()
            self._perm = new_perm
        else:
            raise RootspacePermissionError()

    def stat(self, uid, gids):
        """
        Return Node metadata as dictionary of strings, if the supplied UID and GIDs have
        read permission on the parent Node.

        :param uid:
        :param gids:
        :return:
        """
        if self._parent is None or self._parent.may_read(uid, gids):
            return {
                "uid": "{}".format(self._uid),
                "gid": "{}".format(self._gid),
                "perm": "{:o}".format(self._perm),
                "perm_str": "{}".format(self._perm_str()),
                "accessed": self._accessed.isoformat(),
                "modified": self._modified.isoformat(),
                "changed": self._changed.isoformat()
            }
        else:
            raise RootspacePermissionError()


@attr.s(slots=True)
class DirectoryNode(Node):
    _contents = attr.ib(default=attr.Factory(dict), validator=instance_of(dict))

    def list(self, uid, gids):
        """
        Return the contents of the DirectoryNode as a dictionary.

        :param uid:
        :param gids:
        :return:
        """
        if self.may_read(uid, gids):
            dir_list = {k: v.stat(uid, gids) for k, v in self._contents.items()}
            dir_list["."] = self.stat(uid, gids)
            if self._parent is not None:
                dir_list[".."] = self._parent.stat(uid, gids)
            return dir_list
        else:
            raise RootspacePermissionError()

    def insert_node(self, uid, gids, node_name, node):
        """
        Add a new node to the directory.

        :param uid:
        :param gids:
        :param node_name:
        :param node:
        :return:
        """
        if self.may_write(uid, gids):
            self._contents[node_name] = node
        else:
            raise RootspacePermissionError()


@attr.s(slots=True)
class FileNode(Node):
    _source = attr.ib(default="", validator=instance_of(str))

    def read(self, uid, gids):
        """
        Read from the FileNode.

        :param uid:
        :param gids:
        :return:
        """
        if self.may_read(uid, gids):
            with gzip.open(self._source, "rb") as f:
                return pickle.load(f)
        else:
            raise RootspacePermissionError()

    def write(self, uid, gids, data):
        """
        Write data to the FileNode.

        :param uid:
        :param gids:
        :param data:
        :return:
        """
        if self.may_write(uid, gids):
            with gzip.open(self._source, "wb") as f:
                pickle.dump(data, f)
        else:
            raise RootspacePermissionError()

    def execute(self, uid, gids, context):
        """
        Execute the data within the FileNode.

        :param uid:
        :param gids:
        :param context:
        :return:
        """
        if self.may_execute(uid, gids):
            with gzip.open(self._source, "rb") as f:
                data = pickle.load(f)

            if callable(data):
                return data(context)
            else:
                raise RootspaceNotAnExecutableError()
        else:
            raise RootspacePermissionError()


@attr.s(slots=True)
class LinkNode(Node):
    _target = attr.ib(default=None, validator=instance_of((type(None), weakref.ReferenceType)))


@attr.s
class FileSystem(object):
    _hierarchy = attr.ib(default=DirectoryNode(None, 0, 0, 0o755), validator=instance_of(Node))
    root = attr.ib(default="/", validator=instance_of(str))
    sep = attr.ib(default="/", validator=instance_of(str))
    umask = attr.ib(default=0o022, validator=instance_of(int))

    def _split(self, path):
        """
        Split a path string into a list of directories, starting at the tree root.

        :param path:
        :return:
        """
        if path.startswith(self.root):
            return tuple(filter(None, path.split(self.sep)))
        else:
            raise NotImplementedError("Cannot parse relative paths yet.")

    def _get_child_node(self, uid, gids, parent_node, child_name):
        """
        Return the child of a parent node with a particular name.
        The parent must be a DirectoryNode.

        :param uid:
        :param gids:
        :param parent_node:
        :param child_name:
        :return:
        """
        if parent_node.may_execute(uid, gids):
            if isinstance(parent_node, DirectoryNode):
                child_node = parent_node.contents.get(child_name)
                if child_node is not None:
                    return child_node
                else:
                    raise RootspaceFileNotFoundError()
            else:
                raise RootspaceNotADirectoryError()
        else:
            raise RootspacePermissionError()

    def find_node(self, uid, gids, path):
        """
        Find the node specified by a given path.

        :param uid:
        :param gids:
        :param path:
        :return:
        """
        path_parts = self._split(path)
        parent_node = self._hierarchy
        for i, node_name in enumerate(path_parts):
            child_node = self._get_child_node(uid, gids, parent_node, node_name)
            if i == len(path_parts) - 1:
                return child_node, parent_node
            else:
                parent_node = child_node

    def create_node(self, uid, gids, path, node_type):
        """
        Create a new Node at the specified path:

        :param uid:
        :param gids:
        :param path:
        :param node_type:
        :return:
        """
        path_parts = self._split(path)
        parent_path = self.sep.join(path_parts[:-2])
        file_name = path_parts[-1]
        (parent, grand_parent) = self.find_node(uid, gids, parent_path)
        if node_type == "directory":
            perm = 0o777 & ~self.umask
            parent.insert_node(uid, gids, file_name, DirectoryNode(parent, uid, gids[0], perm))
        elif node_type == "file":
            perm = 0o777 & ~(self.umask | 0o111)
            parent.insert_node(uid, gids, file_name, FileNode(parent, uid, gids[0], perm))
        else:
            raise NotImplementedError("Current cannot create anything other than DirectoryNode and FileNode.")
