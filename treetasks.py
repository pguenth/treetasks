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
logging.basicConfig(filename='treetasks.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', force=True)

default_treefile = "~/.treetasks.xml"
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
        args.files = [os.path.expanduser(default_treefile)]

    def run(stdscr):
        Config.load(args.config)

        app = TreeTasksApplication(stdscr)

        for treefile in args.files:
            if os.path.expanduser(treefile) == os.path.expanduser(default_treefile):
                name = "def"
            else:
                name = None

            app.tm.open_tree(treefile)

        app.run()

    wrapper(run)

parser = argparse.ArgumentParser(description='Manage tasks in a tree structure')
subparsers = parser.add_subparsers(help='sub-commands')

parser_convert = subparsers.add_parser('convert',
        help='Convert a file by opening it with one parser and saving it with another')
parser.add_argument('-f', '--files', action='extend', nargs='+',
        help='The tree file to open. Can be specified multiple times. Default: ' + default_treefile)
parser.add_argument('-c', '--config', default=os.path.expanduser(default_config),
        help='The config file to use. Default: ' + default_config)
parser.set_defaults(func=action_normal)

parser_convert.add_argument('--input-fmt', help='The parser name to convert from. Currently available: xml, json', required=True)
parser_convert.add_argument('--output-fmt', help='The parser name to convert to. Currently available: xml, json', required=True)
parser_convert.add_argument('--input', help='The input file when converting', required=True)
parser_convert.add_argument('--output', help='The output file when converting', required=True)
parser_convert.set_defaults(func=action_convert)

args = parser.parse_args()
args.func(args)
