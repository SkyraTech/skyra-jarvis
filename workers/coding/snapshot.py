"""Developer snapshot preparation. Never alters or commits the source repository."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from skyra_coding import Workspace


def main():
    parser=argparse.ArgumentParser(description='Prepare selected text files for Jarvis file operations')
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--destination',type=Path,required=True)
    parser.add_argument('--files',nargs='+',required=True)
    parser.add_argument('--create',nargs='*',default=[],help='Explicit absent paths the model may propose creating')
    args=parser.parse_args()
    try:
        workspace=Workspace.snapshot(args.source,args.destination,args.files,args.create)
    except (OSError,ValueError,UnicodeError):
        parser.error('Unable to prepare a valid selected-file snapshot; no source files modified')
    print(f'Snapshot prepared with {len(workspace.selected)} selected files; no Git changes made.')


if __name__=='__main__':main()
