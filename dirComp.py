#!/usr/bin/env python

import argparse
import textwrap
import traceback
from pprint import pprint
from typing import Union
from pathlib import Path
from hashlib import md5
from copy import deepcopy
import json


def getPath(root:Union[str,Path], file:Union[str,Path]) -> str:
    file = Path(file)
    if not root.exists():
        raise ValueError('Input root does not exits')
    if not file.exists():
        raise ValueError('Input file does not exits')
    return str(file.relative_to(root))

def getSize(file:Union[str,Path]) -> int:
    file = Path(file)
    if not file.exists():
        raise ValueError('Input file does not exits')
    return file.stat().st_size

def getMD5(file:Union[str,Path]) -> str:
    file = Path(file)
    if not file.exists():
        raise ValueError('Input file does not exits')
    output = ''
    with open(file, 'rb') as f:
        output = md5(f.read()).hexdigest()
    return output

def silent_print(silent:bool, *arg, **kwarg) -> None:
    if not silent:
        print(*arg, **kwarg)

def silent_pprint(silent:bool, *arg, **kwarg) -> None:
    if not silent:
        pprint(*arg, **kwarg)

def dirCompare(
    left_folder:Union[str,Path], right_folder:Union[str,Path],
    comp_path:bool=True, comp_size:bool=False, comp_hash:bool=False,
    silent:bool=False
) -> dict:

    def __loc_calc_path(d, r, i):
        if comp_path: d['path']=getPath(r, i)
    def __loc_calc_size(d, i):
        if comp_size: d['size']=getSize(i)
    def __loc_calc_hash(d, i):
        if comp_hash: d['hash']=getMD5(i)

    if not comp_path and not comp_hash:
        raise ValueError('You must enable at least one of compare path or compare hash')
    key_item = 'hash' if comp_hash else 'path'

    left_folder = Path(left_folder)
    if not left_folder.exists():
        raise ValueError('Input left_folder does not exits')
    right_folder = Path(right_folder)
    if not right_folder.exists():
        raise ValueError('Input right_folder does not exits')

    left_files = sorted([f for f in left_folder.rglob('*') if f.is_file()], key=lambda i:str(i))
    right_files = sorted([f for f in right_folder.rglob('*') if f.is_file()], key=lambda i:str(i))

    output = {'left':{}, 'right':{}, 'same':{}}
    left_buff = dict()

    # calc left folder
    silent_print(silent, 'Analyzing left_folder')
    for lf in left_files:
        silent_print(silent, lf)
        loc_dict = dict()
        __loc_calc_path(loc_dict, left_folder, lf)
        __loc_calc_size(loc_dict, lf)
        __loc_calc_hash(loc_dict, lf)
        key = loc_dict[key_item]
        left_buff[key] = loc_dict
    silent_print(silent, '\n\n')

    # calc right & compare
    silent_print(silent, 'Analyzing right_folder')
    for rf in right_files:
        silent_print(silent, rf)
        loc_dict = dict()
        __loc_calc_path(loc_dict, right_folder, rf)
        __loc_calc_size(loc_dict, rf)
        __loc_calc_hash(loc_dict, rf)

        # compare
        key = loc_dict[key_item]
        if key in left_buff: # same
            output['same'][key] = [deepcopy(left_buff[key]),loc_dict]
            del left_buff[key]
        else: # different
            output['right'][key] = loc_dict
    output['left'] = left_buff

    return output



if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Compare contents of two directories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
        Examples:
          
          compare two folders using their path
            python3 dirComp.py /left/folder /right/folder -p

          compare two folders using their hash
            python3 dirComp.py /left/folder /right/folder -h
          
          * you must provide at lease one of "path" or "hash"

          compare two folders with path, hash, and size info (will use hash as key)
            python3 dirComp.py /left/folder /right/folder -pHs
          
          save output to a file
            python3 dirComp.py /left/folder /right/folder -o comp.json

          silent mode (only print final result) & silent-all mode
            python3 dirComp.py /left/folder /right/folder --silent
            python3 dirComp.py /left/folder /right/folder --silent-all

          verbose mode
            python3 dirComp.py /left/folder /right/folder -v

        ''')
    )

    # positional args
    parser.add_argument('left_folder', metavar='LF', type=str, action='store', help='Left folder path')
    parser.add_argument('right_folder', metavar='RF', type=str, action='store', help='Right folder path')

    # options
    parser.add_argument('-p','--path', action='store_true', help='Compare directory relative path', required=False)
    parser.add_argument('-s','--size', action='store_true', help='Compare file size', required=False)
    parser.add_argument('-H','--hash', action='store_true', help='Compare file md5 hash', required=False)
    parser.add_argument('-o','--output', type=str, action='store', help='Write output to json file', required=False)
    parser.add_argument('--silent', action='store_true', help='Do not print anything, except the final result', required=False)
    parser.add_argument('--silent-all', action='store_true', help='Do not print anything', required=False)
    parser.add_argument('-v','--verbose', action='store_true', help='Enabe verbose print, will override silent', required=False)

    args = parser.parse_args()

    silent = any([args.silent, args.silent_all])
    silent_all = args.silent_all
    if args.verbose:
        silent = False
        silent_all = False
        silent_print(silent, 'Input arguments:', vars(args))
        silent_print(silent, f'{silent = }, {silent_all = }')

    try:
        ret = dirCompare(
            args.left_folder, args.right_folder,
            args.path, args.size, args.hash,
            silent
        )

        silent_pprint(silent_all, ret)

        if 'output' in args and args.output:
            with open(args.output, 'w') as file:
                json.dump(ret, file, indent=2, ensure_ascii=False)
    except KeyboardInterrupt:
        print()
        exit(-1)
    except Exception as err:
        if args.verbose:
            traceback.print_exc()
        print(f'Exception: {err}')
        exit(-1)
