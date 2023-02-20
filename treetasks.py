#!/usr/bin/python

from src.config import Config
from src.application import TreeTasksApplication
from src.treeparser import TaskTreeParserXML, TaskTreeParserJSON, convert_parser
from curses import wrapper
import os.path
import sys

import logging
import argparse

#logging.basicConfig(filename='treetasks.log', encoding='utf-8', level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

default_treefile = "~/.treetasks.xml"
default_lastopened = "~/.treetasks.last"
default_config = "~/.treetasks.ini"


def parser_from_name(name):
    if name == 'json':
        return TaskTreeParserJSON
    elif name == 'xml':
        return TaskTreeParserXML
    else:
        print("No valid parser given. Valid parsers: xml, json")
        return None

def action_convert(args):
    try:
        open(args.input, mode='r')
    except FileNotFoundError:
        print("Input file is not existing")
        return
    except PermissionError:
        print("No permission to open the input file")
        return

    try:
        open(args.output, mode='r')
    except FileNotFoundError:
        pass
    else:
        print("Output file exists. Override? (y/n) ", end='')
        sys.stdout.flush()
        answer = sys.stdin.read(1)
        if answer != 'y':
            return

    try:
        open(args.output, mode='w')
    except PermissionError:
        print("Output file is write protected")
        return

    parser_in = parser_from_name(args.input_fmt)
    parser_out = parser_from_name(args.output_fmt)

    if parser_in is None or parser_out is None:
        return
    
    convert_parser(args.input, args.output, parser_in, parser_out)

def action_normal(args):
    if args.files is None:
        try:
            with open(os.path.expanduser(default_lastopened), mode="r") as f:
                args.files = [os.path.relpath(p) for p in f.read().splitlines()]
        except FileNotFoundError:
            args.files = [os.path.expanduser(default_treefile)]

    if not args.log is None:
        logging.basicConfig(filename=args.log, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', force=True)
    else:
        logging.disable()

    def run(stdscr):
        Config.load(args.config)

        app = TreeTasksApplication(stdscr)

        for treefile in args.files:
            if os.path.expanduser(treefile) == os.path.expanduser(default_treefile):
                name = "def"
            else:
                name = None

            app.tm.open_tree(treefile)

        store_state = app.run()

        if not store_state is None:
            try:
                # assumes store_state is always a list of tree file paths
                with open(os.path.expanduser(default_lastopened), mode="w") as f:
                    for tree_path in store_state:
                        f.write(os.path.abspath(tree_path) + "\n")
            except (FileNotFoundError, PermissionError, NotADirectoryError):
                logging.info("Could not store last opened files")


    wrapper(run)

parser = argparse.ArgumentParser(description='Manage tasks in a tree structure')
subparsers = parser.add_subparsers(help='sub-commands')

parser_convert = subparsers.add_parser('convert',
        help='Convert a file by opening it with one parser and saving it with another')
parser.add_argument('-f', '--files', action='extend', nargs='+',
        help='The tree file to open. Can be specified multiple times. Default: ' + default_treefile)
parser.add_argument('-c', '--config', default=os.path.expanduser(default_config),
        help='The config file to use. Default: ' + default_config)
parser.add_argument('-l', '--log', action='store_const', const='treetasks.log', help='Output a log to treetasks.log')
parser.set_defaults(func=action_normal)

parser_convert.add_argument('--input-fmt', help='The parser name to convert from. Currently available: xml, json', required=True)
parser_convert.add_argument('--output-fmt', help='The parser name to convert to. Currently available: xml, json', required=True)
parser_convert.add_argument('--input', help='The input file when converting', required=True)
parser_convert.add_argument('--output', help='The output file when converting', required=True)
parser_convert.set_defaults(func=action_convert)

args = parser.parse_args()
args.func(args)
