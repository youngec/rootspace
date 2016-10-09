# -*- coding: utf-8 -*-

import enum
import uuid

import attr
from attr.validators import instance_of


@attr.s
class Node(object):
    class FileType(enum.Enum):
        directory = 1
        file = 2
        special = 3

    _uid = attr.ib(validator=instance_of(int))
    _gid = attr.ib(validator=instance_of(int))
    _perm = attr.ib(validator=instance_of(int))
    _type = attr.ib(validator=instance_of(FileType))
    _contents = attr.ib(validator=instance_of((dict, uuid.UUID)))

    @property
    def uid(self):
        """
        Return the owner UID.

        :return:
        """
        return self._uid

    @property
    def gid(self):
        """
        Return the owner GID.

        :return:
        """
        return self._gid

    @property
    def perm(self):
        """
        Return the permission data as integer.

        :return:
        """
        return self._perm

    @property
    def perm_str(self):
        """
        Return the permission data as human-readable string.

        :return:
        """
        perm_digits = (self._perm // 64, (self._perm % 64) // 8, self._perm % 8)
        perm_list = (((p // 4) > 0, ((p % 4) // 2) > 0, (p % 2) > 0) for p in perm_digits)
        perm_groups = ("{}{}{}".format("r" if p[0] else "-", "w" if p[1] else "-", "x" if p[2] else "-") for p in
                       perm_list)
        perm_type = "d" if self.is_directory else "-"
        return perm_type + "".join(perm_groups)

    @property
    def is_directory(self):
        return self._type == Node.FileType.directory

    @property
    def is_file(self):
        return self._type == Node.FileType.file

    @property
    def is_special(self):
        return self._type == Node.FileType.special

    @property
    def contents(self):
        """
        Return the node contents.

        :return:
        """
        return self._contents

    def may_read(self, uid, gids):
        """
        Return True if the supplied UID and GIDs have read permission on this node.

        :param uid:
        :param gids:
        :return:
        """
        if uid == 0:
            return True
        elif any(gid == 0 for gid in gids):
            return True
        else:
            if uid == self._uid:
                return ((self._perm // 64) // 4) > 0
            elif any(gid == self._gid for gid in gids):
                return (((self._perm % 64) // 8) // 4) > 0
            else:
                return ((self._perm % 8) // 4) > 0

    def may_write(self, uid, gids):
        """
        Return True if the supplied UID and GIDs have write permission on this node.

        :param uid:
        :param gids:
        :return:
        """
        if uid == 0:
            return True
        elif any(gid == 0 for gid in gids):
            return True
        else:
            if uid == self._uid:
                return (((self._perm // 64) % 4) // 2) > 0
            elif any(gid == self._gid for gid in gids):
                return ((((self._perm % 64) // 8) % 4) // 2) > 0
            else:
                return (((self._perm % 8) % 4) // 2) > 0

    def may_execute(self, uid, gids):
        """
        Return True if the supplied UID and GIDs have execute permission on this node.

        :param uid:
        :param gids:
        :return:
        """
        if uid == self._uid:
            return ((self._perm // 64) % 2) > 0
        elif any(gid == self._gid for gid in gids):
            return (((self._perm % 64) // 8) % 2) > 0
        else:
            return ((self._perm % 8) % 2) > 0


@attr.s
class FileSystem(object):
    _hierarchy = attr.ib(validator=instance_of(Node))
    _database = attr.ib(validator=instance_of(dict))
    root = attr.ib(default="/", validator=instance_of(str))
    sep = attr.ib(default="/", validator=instance_of(str))

    def _uuid(self, path):
        """
        Return a UUID that corresponds to the specified path.

        :param path:
        :return:
        """
        return uuid.uuid5(uuid.NAMESPACE_URL, path)

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

    def _get_child_node(self, parent_node, child_name):
        """
        Return the child of a parent node with a particular name.

        :param parent_node:
        :param child_name:
        :return:
        """
        if parent_node.is_directory:
            child_node = parent_node.contents.get(child_name)
            if child_node is not None:
                return child_node
            else:
                raise FileNotFoundError()
        else:
            raise NotADirectoryError()

    def _find_node(self, path):
        """
        Find the node specified by a given path.

        :param path:
        :return:
        """
        path_parts = self._split(path)
        parent_node = self._hierarchy
        for i, file_name in enumerate(path_parts):
            child_node = self._get_child_node(parent_node, file_name)
            if i == len(path_parts) - 1:
                return (child_node, parent_node)
            else:
                parent_node = child_node

    def stat(self, uid, gids, path):
        """
        Return metadata pertaining to a file system node.

        :param uid:
        :param gids:
        :param path:
        :return:
        """
        return {
            "path": path,

        }
