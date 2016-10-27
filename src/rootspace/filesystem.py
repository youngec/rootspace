# -*- coding: utf-8 -*-

import abc
import gzip
import pickle
import datetime
import weakref

import attr
from attr.validators import instance_of

from .exceptions import RootspaceNotAnExecutableError, RootspaceFileNotFoundError, \
    RootspaceNotADirectoryError, RootspacePermissionError, RootspaceFileExistsError
from .utilities import ref


@attr.s
class Node(object):
    """
    Describes the generalized functionality of a node in a UNIX-like filesystem.
    """
    # TODO: I might want to change the signature to provide a default value of parent.
    _parent = attr.ib(validator=instance_of((type(None), weakref.ReferenceType)), convert=ref)
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

    def modify_parent(self, uid, gids, new_parent):
        """
        Change the parent of the current Node.

        :param uid:
        :param gids:
        :param new_parent:
        :return:
        """
        if isinstance(new_parent, Node):
            if self._parent is None or self._parent().may_write(uid, gids):
                self._modified = datetime.datetime.now()
                self._parent = weakref.ref(new_parent)
            else:
                raise RootspacePermissionError()
        else:
            raise TypeError("Expected 'new_parent' to be a Node.")

    def modify_uid(self, uid, gids, new_uid):
        """
        If the supplied UID is the owner of the Node, change the Node owner.
        A privileged user may always change the Node owner.

        :param uid:
        :param gids:
        :param new_uid:
        :return:
        """
        if isinstance(new_uid, int):
            if (uid == 0) or (uid == self._uid):
                self._modified = datetime.datetime.now()
                self._uid = new_uid
            else:
                raise RootspacePermissionError()
        else:
            raise TypeError("Expected 'new_uid' to be an integer.")

    def modify_gid(self, uid, gids, new_gid):
        """
        If the supplied UID is the owner of the Node, change the Node GID.
        A privileged user may always change the Node GID.

        :param uid:
        :param gids:
        :param new_gid:
        :return:
        """
        if isinstance(new_gid, int):
            if (uid == 0) or (uid == self._uid):
                self._modified = datetime.datetime.now()
                self._gid = new_gid
            else:
                raise RootspacePermissionError()
        else:
            raise TypeError("Expected 'new_gid' to be an integer.")

    def modify_perm(self, uid, gids, new_perm):
        """
        If the supplied UID is the owner of the Node, change the Node permissions.
        A privileged user may always change the Node permissions.

        :param uid:
        :param gids:
        :param new_perm:
        :return:
        """
        if isinstance(new_perm, int):
            if (uid == 0) or (uid == self._uid):
                self._modified = datetime.datetime.now()
                self._perm = new_perm
            else:
                raise RootspacePermissionError()
        else:
            raise TypeError("Expected 'new_perm' to be an integer.")

    def stat(self, uid, gids):
        """
        Return Node metadata as dictionary of strings, if the supplied UID and GIDs have
        read permission on the parent Node.

        :param uid:
        :param gids:
        :return:
        """
        if self._parent is None or self._parent().may_read(uid, gids):
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


@attr.s
class DirectoryNode(Node):
    """
    Describes a directory in a UNIX-like filesystem.
    """
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
                dir_list[".."] = self._parent().stat(uid, gids)
            return dir_list
        else:
            raise RootspacePermissionError()

    def insert_node(self, uid, gids, node_name, node, replace=True):
        """
        Add a new node to the directory.

        :param uid:
        :param gids:
        :param node_name:
        :param node:
        :param replace:
        :return:
        """
        if isinstance(node, Node):
            if self.may_write(uid, gids):
                if replace or (node_name not in self._contents):
                    self._contents[node_name] = node
                    node.modify_parent(uid, gids, self)
                else:
                    raise RootspaceFileExistsError()
            else:
                raise RootspacePermissionError()
        else:
            raise TypeError("Expected 'node' to be a Node instance.")

    def remove_node(self, uid, gids, node_name):
        """
        Remove a node from the directory.

        :param uid:
        :param gids:
        :param node_name:
        :return:
        """
        if self.may_write(uid, gids):
            if node_name in self._contents:
                self._contents.pop(node_name)
            else:
                raise RootspaceFileNotFoundError()
        else:
            raise RootspacePermissionError()

    def move_node(self, uid, gids, old_name, new_parent, new_name, replace=True):
        if isinstance(new_parent, Node):
            if old_name in self._contents:
                new_parent.insert_node(uid, gids, new_name, self._contents[old_name], replace)
                self.remove_node(uid, gids, old_name)
            else:
                raise RootspaceFileNotFoundError()
        else:
            raise TypeError("Expected 'new_parent' to be a Node.")


@attr.s
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

    def execute(self, uid, gids):
        """
        Execute the data within the FileNode.

        :param uid:
        :param gids:
        :return:
        """
        if self.may_execute(uid, gids):
            with gzip.open(self._source, "rb") as f:
                data = pickle.load(f)

            if callable(data):
                return data
            else:
                raise RootspaceNotAnExecutableError()
        else:
            raise RootspacePermissionError()


@attr.s
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
        # FIXME: Sanitize the path string (multiple occurrences of self.sep, trailing self.sep, etc.)
        if path.startswith(self.root):
            return tuple(filter(None, path.split(self.sep)))
        else:
            raise NotImplementedError("Cannot parse relative paths yet.")

    def _separate(self, path):
        """
        Return the path to the parent directory of the specified path and
        the basename of the specified path.

        :param path:
        :return:
        """
        path_parts = self._split(path)
        return self.sep.join(path_parts[:-2]), path_parts[-1]

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

    def _exists(self, uid, gids, path):
        """
        Return True, if the specified path points to a valid node.

        :param path:
        :return:
        """
        path_parts = self._split(path)
        parent_node = self._hierarchy
        try:
            for i, node_name in enumerate(path_parts):
                child_node = self._get_child_node(uid, gids, parent_node, node_name)
                if i == len(path_parts) - 1:
                    return True
                else:
                    parent_node = child_node
        except (RootspaceFileNotFoundError, RootspaceNotADirectoryError):
            pass

        return False

    def _find_node(self, uid, gids, path):
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

    def find_path(self, uid, gids, search_paths, node_name):
        """
        Given a list of search paths, try to find all occurrences of the specified node name.

        :param search_paths:
        :param node_name:
        :return:
        """
        node_paths = list()
        for search_path in search_paths:
            node_path = self.sep.join(search_path, node_name)
            try:
                if self._exists(uid, gids, node_path):
                    node_paths.append(node_path)
            except RootspacePermissionError:
                pass

        if len(node_paths) > 0:
            return node_paths
        else:
            raise RootspaceFileNotFoundError

    def create_node(self, uid, gids, path, node_type):
        """
        Create a new Node at the specified path.

        :param uid:
        :param gids:
        :param path:
        :param node_type:
        :return:
        """
        parent_path, file_name = self._separate(path)
        (parent, _) = self._find_node(uid, gids, parent_path)
        if isinstance(parent, DirectoryNode):
            if node_type == "directory":
                perm = 0o777 & ~self.umask
                parent.insert_node(uid, gids, file_name, DirectoryNode(None, uid, gids[0], perm))
            elif node_type == "file":
                perm = 0o777 & ~(self.umask | 0o111)
                parent.insert_node(uid, gids, file_name, FileNode(None, uid, gids[0], perm))
            else:
                raise NotImplementedError("Currently cannot create anything other than DirectoryNode and FileNode.")
        else:
            raise RootspaceNotADirectoryError()

    def remove_node(self, uid, gids, path):
        """
        Remove the Node at the specified path.

        :param uid:
        :param gids:
        :param path:
        :return:
        """
        parent_path, file_name = self._separate(path)
        (parent, _) = self._find_node(uid, gids, parent_path)
        if isinstance(parent, DirectoryNode):
            parent.remove_node(uid, gids, file_name)
        else:
            raise RootspaceNotADirectoryError()

    def move_node(self, uid, gids, source_path, target_path, replace=True):
        """
        Move the Node from the source to the target path.

        :param uid:
        :param gids:
        :param source_path:
        :param target_path:
        :param replace:
        :return:
        """
        source_parent_path, source_name = self._separate(source_path)
        target_parent_path, target_name = self._separate(target_path)

        (source_parent, _) = self._find_node(uid, gids, source_parent_path)
        (target_parent, _) = self._find_node(uid, gids, target_parent_path)

        if isinstance(source_parent, DirectoryNode):
            source_parent.move_node(uid, gids, source_name, target_parent, target_name, replace)
        else:
            raise RootspaceNotADirectoryError()
