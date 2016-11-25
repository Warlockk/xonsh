# -*- coding: utf-8 -*-
"""Implements the xonsh history backend via sqlite3."""
import builtins
import os
import sqlite3
import time

from xonsh.history.base import HistoryBase
import xonsh.tools as xt


def _xh_sqlite_get_conn():
    data_dir = builtins.__xonsh_env__.get('XONSH_DATA_DIR')
    data_dir = xt.expanduser_abs_path(data_dir)
    db_file = os.path.join(data_dir, 'xonsh-history.sqlite')
    return sqlite3.connect(db_file)


def _xh_sqlite_create_history_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xonsh_history
             (inp TEXT,
              rtn INTEGER,
              tsb REAL,
              tse REAL
             )
    """)


def _xh_sqlite_insert_command(cursor, cmd):
    cursor.execute("""
        INSERT INTO xonsh_history VALUES(?, ?, ?, ?)
    """, (cmd['inp'].rstrip(), cmd['rtn'], cmd['ts'][0], cmd['ts'][1]))


def _xh_sqlite_get_records(cursor):
    cursor.execute('SELECT inp FROM xonsh_history ORDER BY tsb')
    return cursor.fetchall()


def xh_sqlite_append_history(cmd):
    with _xh_sqlite_get_conn() as conn:
        c = conn.cursor()
        _xh_sqlite_create_history_table(c)
        _xh_sqlite_insert_command(c, cmd)
        conn.commit()


def xh_sqlite_items():
    with _xh_sqlite_get_conn() as conn:
        c = conn.cursor()
        _xh_sqlite_create_history_table(c)
        return _xh_sqlite_get_records(c)


class SqliteHistory(HistoryBase):
    def __init__(self, gc=True, **kwargs):
        super().__init__(gc=gc, **kwargs)
        self.last_cmd_inp = None

    def append(self, cmd):
        opts = builtins.__xonsh_env__.get('HISTCONTROL')
        if 'ignoredups' in opts and cmd['inp'].rstrip() == self.last_cmd_inp:
            # Skipping dup cmd
            return
        if 'ignoreerr' in opts and cmd['rtn'] != 0:
            # Skipping failed cmd
            return
        self.last_cmd_inp = cmd['inp'].rstrip()
        t = time.time()
        xh_sqlite_append_history(cmd)
        print('history cmd: {} took {:.4f}s'.format(cmd, time.time() - t))

    def flush(self, at_exit=False):
        print('TODO: SqliteHistory flush() called')

    def items(self):
        for item in xh_sqlite_items():
            yield {'inp': item[0]}
