#!/usr/bin/env python
import os
import sys
import argparse
from contextlib import contextmanager
import packetweaver.core.controllers.exceptions as ex
import packetweaver.core.controllers.app_ctrl as appctrl


@contextmanager
def cd(newdir):
    """ Context manager function to securely cd in a directory"""
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


def build_parser():
    parser = argparse.ArgumentParser(description="""Packet Weaver""")
    parser.add_argument(
        '--config', '-c', action='store', type=str, default='pw.ini',
        dest='config_filename'
    )
    sp = parser.add_subparsers(help='Inline commands', dest='subcmd')
    for cmd_name in ['run', 'start', 'exploit', 'use']:
        help_msg = 'Run commands'
        if cmd_name != 'use':
            help_msg += ' (use command alias)'
        sp_run = sp.add_parser(cmd_name, help=help_msg)
        sp_run.add_argument(
            '--ability', '-a',
            action='store', type=str, dest='ability_name', required=True,
            help='Module path of a module to use during this run'
        )
        sp_run.add_argument(
            '--package', '-p',
            action='store', type=str, dest='package_name', required=True,
            help='Module path of a module to use during this run'
        )

    sp.add_parser('show', help='Display a list of available modules')
    sp.add_parser('list',
                  help='Display a list of available modules (show alias)')
    sp.add_parser('update', help='Not yet implemented')
    sp.add_parser('interactive', help='Interactive mode')
    return parser


if __name__ == '__main__':
    args, rem_args = build_parser().parse_known_args()

    # Change to the current directory to make relative path reference of
    # internal files working (i.e: pw.ini)
    base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    with cd(base_dir):
        try:
            app = appctrl.AppCtrl(args.config_filename, args, rem_args)
            app.execute()
        except ex.ExitPw:
            pass
