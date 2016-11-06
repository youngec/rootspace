# -*- coding: utf-8 -*-

import collections
import copy
import datetime
import shelve
import uuid
import warnings
import weakref

import attr
from attr.validators import instance_of

from .exceptions import RootspaceNotAnExecutableError, RootspaceFileNotFoundError, \
    RootspaceNotADirectoryError, RootspacePermissionError, RootspaceFileExistsError, \
    RootspaceIsADirectoryError, FixmeWarning
from .executables import Executable, registry
from .utilities import to_ref, to_uuid


@attr.s
class Node(object):
    """
    Describes the generalized functionality of a node in a UNIX-like filesystem.
    """
    _uid = attr.ib(validator=instance_of(int))
    _gid = attr.ib(validator=instance_of(int))
    _perm = attr.ib(validator=instance_of(int))
    _uuid = attr.ib(default=uuid.uuid4(), validator=instance_of(uuid.UUID))
    _parent = attr.ib(default=None, validator=instance_of((type(None), weakref.ReferenceType)), convert=to_ref)
    _accessed = attr.ib(default=0.0, validator=instance_of(float))
    _modified = attr.ib(default=0.0, validator=instance_of(float))
    _changed = attr.ib(default=0.0, validator=instance_of(float))

    @classmethod
    def from_dict(cls, serialised):
        """
        Create a Node based on a serialised representation of the Node and its children.

        :param serialised:
        :return:
        """
        return cls(**serialised)

    @property
    def uuid(self):
        return self._uuid

    def to_dict(self, uid, gids, recursive=True):
        """
        Serialize the node to a dictionary.

        :param uid:
        .param gids:
        :param recursive:
        :return:
        """
        return self.stat(uid, gids)

    def _perm_str(self):
        """
        Return the permission data as human-readable string.

        :return:
        """
        perm_digits = (self._perm // 64, (self._perm % 64) // 8, self._perm % 8)
        perm_list = (((p // 4) > 0, ((p % 4) // 2) > 0, (p % 2) > 0) for p in perm_digits)
        perm_groups = ("{}{}{}".format(
            "r" if p[0] else "-", "w" if p[1] else "-", "x" if p[2] else "-"
        ) for p in perm_list)
        return "".join(perm_groups)

    def may_read(self, uid, gids):
        """
        Return True if the supplied UID and GIDs have read permission on this node.
        A privileged user (UID 0) always has read access.

        :param uid:
        :param gids:
        :return:
        """
        if not isinstance(gids, collections.Iterable):
            gids = (gids,)

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
        if not isinstance(gids, collections.Iterable):
            gids = (gids,)

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
        if not isinstance(gids, collections.Iterable):
            gids = (gids,)

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
                self._modified = datetime.datetime.timestamp(datetime.datetime.now())
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
                self._modified = datetime.datetime.timestamp(datetime.datetime.now())
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
                self._modified = datetime.datetime.timestamp(datetime.datetime.now())
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
                self._modified = datetime.datetime.timestamp(datetime.datetime.now())
                self._perm = new_perm
            else:
                raise RootspacePermissionError()
        else:
            raise TypeError("Expected 'new_perm' to be an integer.")

    def reset_perm(self, uid, gids, mask):
        """
        Reset the permissions byte using the given mask. Otherwise works exactly like
        modify_perm.

        :param uid:
        :param gids:
        :param mask:
        :return:
        """
        if isinstance(mask, int):
            if (uid == 0) or (uid == self._uid):
                self._modified = datetime.datetime.timestamp(datetime.datetime.now())
                self._perm = 0o777 & ~mask
            else:
                raise RootspacePermissionError()
        else:
            raise TypeError("Expected 'mask' to be an integer.")

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
                "uid": self._uid,
                "gid": self._gid,
                "perm": self._perm,
                "accessed": self._accessed,
                "modified": self._modified,
                "changed": self._changed
            }
        else:
            raise RootspacePermissionError()


@attr.s
class DirectoryNode(Node):
    """
    Describes a directory in a UNIX-like filesystem.
    """
    _contents = attr.ib(default=attr.Factory(dict), validator=instance_of(dict))

    def to_dict(self, uid, gids, recursive=True):
        serialised = super(DirectoryNode, self).to_dict(uid, gids)

        if recursive:
            if self.may_read(uid, gids) and self.may_execute(uid, gids):
                serialised["contents"] = {}
                for name, node in self._contents.items():
                    serialised["contents"][name] = node.to_dict(uid, gids)
            else:
                raise RootspacePermissionError()

        return serialised

    def update_children(self, uid, gids, recursive=True):
        """
        Ensure that all children of this node have the correct parent reference.

        :param uid:
        :param gids:
        :return:
        """
        if self.may_write(uid, gids):
            for child_node in self._contents.values():
                child_node.modify_parent(uid, gids, self)
                if recursive and isinstance(child_node, DirectoryNode):
                    child_node.update_children(uid, gids)
        else:
            raise RootspacePermissionError()

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
        """
        Move a node from one directory to the next.

        :param uid:
        :param gids:
        :param old_name:
        :param new_parent:
        :param new_name:
        :param replace:
        :return:
        """
        if isinstance(new_parent, Node):
            if old_name in self._contents:
                new_parent.insert_node(uid, gids, new_name, self._contents[old_name], replace)
                self.remove_node(uid, gids, old_name)
            else:
                raise RootspaceFileNotFoundError()
        else:
            raise TypeError("Expected 'new_parent' to be a Node.")

    def copy_node(self, uid, gids, old_name, new_parent, new_name, replace=True):
        """
        Copy a node to another directory.

        :param uid:
        :param gids:
        :param old_name:
        :param new_parent:
        :param new_name:
        :param replace:
        :return:
        """
        if isinstance(new_parent, Node):
            if old_name in self._contents:
                node_copy = copy.deepcopy(self._contents[old_name])
                new_parent.insert_node(uid, gids, new_name, node_copy, replace)
            else:
                raise RootspaceFileNotFoundError()
        else:
            raise TypeError("Expected 'new_parent' to be a Node.")


@attr.s
class FileNode(Node):
    _source = attr.ib(default=attr.Factory(uuid.uuid4), validator=instance_of(uuid.UUID), convert=to_uuid)

    def to_dict(self, uid, gids, recursive=True):
        serialised = super(FileNode, self).to_dict(uid, gids)

        if self._parent is None or self._parent().may_execute(uid, gids):
            serialised["source"] = str(self._source)
        else:
            raise RootspacePermissionError()

        return serialised

    def get_source(self, uid, gids, as_string=True):
        """
        Return the souce of the file.

        :param uid:
        :param gids:
        :param as_string:
        :return:
        """
        if self._parent is None or self._parent().may_execute(uid, gids):
            if as_string:
                return str(self._source)
            else:
                return self._source
        else:
            raise RootspacePermissionError()


@attr.s
class FileSystem(object):
    _db = attr.ib(validator=instance_of(str))
    _hier = attr.ib(default=DirectoryNode(0, 0, 0o755), validator=instance_of(Node))
    root = attr.ib(default="/", validator=instance_of(str))
    sep = attr.ib(default="/", validator=instance_of(str))
    umask = attr.ib(default=0o022, validator=instance_of(int))

    @classmethod
    def generate_unix(cls, db_path, umask=0o022):
        """
        Generate a virtual UNIX-like file system.

        :param db_path:
        :param umask:
        :return:
        """
        efi = str(uuid.uuid4())
        hostname = str(uuid.uuid4())
        passwd = str(uuid.uuid4())
        shadow = str(uuid.uuid4())

        hier = DirectoryNode(0, 0, 0o755, contents={
            "bin": DirectoryNode(0, 0, 0o755, contents={}),
            "boot": DirectoryNode(0, 0, 0o755, contents={
                "EFI": DirectoryNode(0, 0, 0o755, contents={
                    "BOOT": DirectoryNode(0, 0, 0o755, contents={
                        "BOOTX64.EFI": FileNode(0, 0, 0o755, source=efi)
                    })
                })
            }),
            "dev": DirectoryNode(0, 0, 0o755, contents={}),
            "etc": DirectoryNode(0, 0, 0o755, contents={
                "hostname": FileNode(0, 0, 0o644, source=hostname),
                "passwd": FileNode(0, 0, 0o644, source=passwd),
                "shadow": FileNode(0, 0, 0o000, source=shadow)
            }),
            "home": DirectoryNode(0, 0, 0o755, contents={}),
            "root": DirectoryNode(0, 0, 0o755, contents={}),
            "usr": DirectoryNode(0, 0, 0o755, contents={}),
            "var": DirectoryNode(0, 0, 0o755, contents={})
        })
        hier.update_children(0, 0)

        with shelve.open(db_path, writeback=True) as db:
            db[hostname] = "hostname"
            db[passwd] = [
                {"username": "root", "password": "x", "uid": 0, "gid": 0, "gecos": "root", "home": "/root"}
            ]
            db[shadow] = [
                {"username": "root", "password": "!", "changed": 0, "minimum": 0, "maximum": 99999, "warn": 7, "disable": 1, "disabled": 0}
            ]
            db[efi] = ""

        return cls(db_path, hier, "/", "/", umask)

    def to_dict(self, uid, gids, recursive=True):
        """
        Serialise the file system to a dictionary.

        :param uid:
        :param gids:
        :param recursive:
        :return:
        """
        return {
            "db": self._db,
            "hier": self._hier.to_dict(uid, gids, recursive),
            "root": self.root,
            "sep": self.sep,
            "umask": self.umask
        }

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
        if len(path_parts) > 0:
            return self.root + self.sep.join(path_parts[:-1]), path_parts[-1]
        else:
            return self.root, ""

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

    def _find_node(self, uid, gids, path):
        """
        Find the node specified by a given path.

        :param uid:
        :param gids:
        :param path:
        :return:
        """
        path_parts = self._split(path)
        parent_node = self._hier
        for i, node_name in enumerate(path_parts):
            child_node = self._get_child_node(uid, gids, parent_node, node_name)
            if i == len(path_parts) - 1:
                return child_node, parent_node
            else:
                parent_node = child_node

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
                parent.insert_node(uid, gids, file_name, DirectoryNode(uid, gids[0], perm))
            elif node_type == "file":
                perm = 0o777 & ~(self.umask | 0o111)
                parent.insert_node(uid, gids, file_name, FileNode(uid, gids[0], perm))
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

    def copy_node(self, uid, gids, source_path, target_path, replace=True):
        """
        Copy the Node from the source to the target path.

        :param uid:
        :param gids:
        :param source_path:
        :param target_path:
        :param replace:
        :return:
        """
        warnings.warn("The method copy_node currently does not copy the file contents.", FixmeWarning)

        source_parent_path, source_name = self._separate(source_path)
        target_parent_path, target_name = self._separate(target_path)

        (source_parent, _) = self._find_node(uid, gids, source_parent_path)
        (target_parent, _) = self._find_node(uid, gids, target_parent_path)

        if isinstance(source_parent, DirectoryNode):
            source_parent.copy_node(uid, gids, source_name, target_parent, target_name, replace)
        else:
            raise RootspaceNotADirectoryError()

    def read(self, uid, gids, path):
        """
        Read from a file.
        """
        (target, parent) = self._find_node(uid, gids, path)

        if target.may_read(uid, gids):
            if isinstance(target, FileNode):
                target_source = target.get_source(uid, gids)
                with shelve.open(self._db) as db:
                    if target_source in db:
                        return db[target_source]
                    else:
                        return None
            else:
                raise RootspaceIsADirectoryError()
        else:
            raise RootspacePermissionError()

    def write(self, uid, gids, path, data):
        """
        Write to a file.
        """
        (target, parent) = self._find_node(uid, gids, path)

        if target.may_write(uid, gids):
            if isinstance(target, FileNode):
                target_source = target.get_source(uid, gids)
                with shelve.open(self._db) as db:
                    db[target_source] = data
                    db.sync()
            else:
                raise RootspaceIsADirectoryError()
        else:
            raise RootspacePermissionError()

    def execute(self, uid, gids, path, arguments, context):
        """
        Execute a file.
        """
        (target, parent) = self._find_node(uid, gids, path)

        if target.may_execute(uid, gids):
            if isinstance(target, FileNode):
                target_source = target.get_source(uid, gids)
                if target_source in registry:
                    return registry[target_source](arguments, context)
                else:
                    with shelve.open(self._db) as db:
                        if target_source in db:
                            if issubclass(db[target_source], Executable):
                                return db[target_source](arguments, context)
                            else:
                                raise RootspaceNotAnExecutableError()
                        else:
                            raise RootspaceNotAnExecutableError()
            else:
                raise RootspaceIsADirectoryError()
        else:
            raise RootspacePermissionError()
