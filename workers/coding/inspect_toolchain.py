"""Explicit owner inspection of installed tools; never installs or enables project execution."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from skyra_coding.toolchains import inspect_typescript
from skyra_coding.scaffold import _parent


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node',required=True)
    parser.add_argument('--compiler',required=True)
    parser.add_argument('--output',type=Path,help='New absolute .json file; existing files are never overwritten')
    args=parser.parse_args(argv)
    output=args.output
    if output:
        if (not output.is_absolute() or output.suffix.lower()!='.json'
                or output.exists() or output.is_symlink()):
            raise ValueError('Choose a new absolute JSON configuration path')
        _parent(output.parent)
    tools=inspect_typescript(args.node,args.compiler,owner_enabled=True)
    if output:
        with output.open('x',encoding='utf-8',newline='\n') as stream:
            stream.write(json.dumps(tools,sort_keys=True,indent=2)+'\n')
        print(json.dumps({'written':str(output),'node_version':tools['node_version'],
            'compiler_version':tools['compiler_version'],'project_execution_enabled':False}))
    else:print(json.dumps(tools,sort_keys=True,indent=2))


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,RuntimeError) as exc:
        print(json.dumps({'error':'toolchain_inspection_requires_review','error_type':type(exc).__name__}),file=sys.stderr)
        raise SystemExit(1)
