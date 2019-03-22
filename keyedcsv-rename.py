#!/usr/bin/env python3
import argparse
import os

import keyedcsv


def main():
    parser = argparse.ArgumentParser(
        description='Rename primary key in CSVFILE from SRCKEY to DSTKEY and '
                    'write the result file content to OUTFILE. For security '
                    'concern, CSVFILE and OUTFILE must not be the same.')
    parser.add_argument('csvfile', metavar='CSVFILE')
    parser.add_argument('outfile', metavar='OUTFILE')
    parser.add_argument('srckey', metavar='SRCKEY')
    parser.add_argument('dstkey', metavar='DSTKEY')
    args = parser.parse_args()

    csvfile = os.path.normpath(args.csvfile)
    outfile = os.path.normpath(args.outfile)
    try:
        if csvfile == outfile or os.path.samefile(csvfile, outfile):
            raise ValueError('CSVFILE ({}) and OUTFILE ({}) must not be '
                             'the same file'.format(csvfile, outfile))
    except FileNotFoundError:
        pass
    er = keyedcsv.ExprRecord(csvfile)
    er.rename_pk(args.srckey, args.dstkey)
    with open(outfile, 'w') as _outfile:
        _outfile.write(str(er))


if __name__ == '__main__':
    main()
