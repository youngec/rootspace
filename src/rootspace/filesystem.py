# -*- coding: utf-8 -*-

import copy
import datetime
import enum
import uuid

import attr
from attr.validators import instance_of

from .exceptions import NotAnExecutableError


@attr.s
class Node(object):
    class FileType(enum.Enum):
        directory = 1
        file = 2
        special = 3

    _uid = attr.ib(validator=instance_of(int))
    _gid = attr.ib(validator=instance_of(int))
    _perm = attr.ib(validator=instance_of(int))
    _accessed = attr.ib(validator=instance_of(datetime.datetime))
    _modified = attr.ib(validator=instance_of(datetime.datetime))
    _changed = attr.ib(validator=instance_of(datetime.datetime))
    _type = attr.ib(validator=instance_of(FileType))
    _contents = attr.ib(validator=instance_of((dict, uuid.UUID)))

    @classmethod
    def create(cls, uid, gid, perm, node_type, contents=None):
        """
        Creates a new node.

        :param uid:
        :param gid:
        :param perm:
        :param node_type:
        :param contents:
        :return:
        """
        d = datetime.datetime.now()
        if node_type == "directory":
            nt = cls.FileType.directory
        elif node_type == "file":
            nt = cls.FileType.file
        elif node_type == "special":
            nt = cls.FileType.special
        else:
            raise TypeError("Known node types: {}".format(cls.FileType))

        # TODO: Maybe restrict the content types that each file type can contain.
        if contents is None:
            if nt == cls.FileType.directory:
                contents = dict()
            else:
                contents = uuid.uuid4()

        return cls(uid, gid, perm, d, d, d, nt, contents)

    @classmethod
    def uuid(cls, path):
        return uuid.uuid5(uuid.NAMESPACE_URL, path)

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
    def accessed(self):
        """
        Return the time of last access to this node.

        :return:
        """
        return self._accessed

    @property
    def modified(self):
        """
        Return the time of last modification of this node.

        :return:
        """
        return self._modified

    @property
    def changed(self):
        """
        Return the time of last change of the contents of this node.

        :return:
        """
        return self._changed

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

    def to_dict(self):
        """
        Return a dictionary representation of a Node.

        :return:
        """
        return {"uid": self._uid, "gid": self._gid, "perm": self._perm, "perm_str": self.perm_str}

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
        (target, parent) = self._find_node(path)
        if parent.may_read(uid, gids):
            stat_dict = {
                "path": path,
                "perm": "({:o} / {})".format(target.perm, target.perm_str),
                "uid": "({} / {})".format(target.uid, "Unknown UID"),
                "gid": "({} / {})".format(target.gid, "Unknown GID"),
                "accessed": target.accessed,
                "modified": target.modified,
                "changed": target.changed
            }
            return stat_dict
        else:
            raise PermissionError()

    def list(self, uid, gids, path):
        """
        List the contents of the directory-type file system node.

        :param uid:
        :param gids:
        :param path:
        :return:
        """
        (target, parent) = self._find_node(path)
        if target.may_read(uid, gids):
            if target.is_directory:
                if isinstance(target.contents, dict):
                    dir_list = dict()
                    for k, v in target.contents.items():
                        dir_list[k] = v.to_dict()
                    dir_list["."] = target.to_dict()
                    dir_list[".."] = parent.to_dict()
                    return dir_list
                else:
                    raise NotImplementedError("Currently, directories cannot be linked to the database.")
            else:
                raise NotADirectoryError()
        else:
            raise PermissionError()

    def read(self, uid, gids, path):
        """
        Return the contents of the file- or special-type file system node.

        :param uid:
        :param gids:
        :param path:
        :return:
        """
        (target, parent) = self._find_node(path)
        if target.may_read(uid, gids):
            if target.is_file:
                if isinstance(target.contents, uuid.UUID):
                    data = self._database.get(target.contents)
                    if data is not None:
                        return copy.deepcopy(data)
                    else:
                        raise FileNotFoundError()
                else:
                    raise NotImplementedError("Cannot read from files without database links.")
            elif target.is_special:
                raise NotImplementedError("Cannot read from special files yet.")
            else:
                raise IsADirectoryError()
        else:
            raise PermissionError()

    def write(self, uid, gids, path, data):
        """
        Write the specified data to the specified file.

        :param uid:
        :param gids:
        :param path:
        :return:
        """
        (target, parent) = self._find_node(path)
        if target.may_write(uid, gids):
            if target.is_file:
                if isinstance(target.contents, uuid.UUID):
                    self._database[target.contents] = data
                else:
                    raise NotImplementedError("Cannot write to files without database links.")
            elif target.is_special:
                raise NotImplementedError("Cannot write to special files yet.")
            else:
                raise IsADirectoryError()
        else:
            raise PermissionError()

    def execute(self, uid, gids, path, arguments):
        """
        Execute the data registered with the specified path.

        :param uid:
        :param gids:
        :param path:
        :param arguments:
        :return:
        """
        (target, parent) = self._find_node(path)
        if target.may_execute(uid, gids):
            if target.is_file:
                if isinstance(target.contents, uuid.UUID):
                    data = self._database.get(target.contents)
                    if data is not None:
                        if callable(data):
                            return data(arguments)
                        else:
                            raise NotAnExecutableError()
                    else:
                        raise FileNotFoundError()
                else:
                    raise NotImplementedError("Cannot execute files without database links.")
            elif target.is_special:
                raise NotImplementedError("Cannot execute special files yet.")
            else:
                raise IsADirectoryError()
        else:
            raise PermissionError()
