#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import pipes
import click

from . import _common, cli, __version__

UTIL_NAME = 'pairsam_markasdup'

@cli.command()
@click.argument(
    'pairsam_path', 
    type=str,
    required=False)
@click.option(
    "-o", "--output", 
    type=str, 
    default="", 
    help='output .pairsam file.'
        ' If the path ends with .gz, the output is bgzip-compressed.'
        ' By default, the output is printed into stdout.')

def markasdup(pairsam_path, output):
    '''tag all pairsam entries with a duplicate tag.

    PAIRSAM_PATH : input .pairsam file. If the path ends with .gz, the input is
    gzip-decompressed. By default, the input is read from stdin.
    '''
    instream = (_common.open_bgzip(pairsam_path, mode='r') 
                if pairsam_path else sys.stdin)
    outstream = (_common.open_bgzip(output, mode='w') 
                 if output else sys.stdout)
 
    header, pairsam_body_stream = _common.get_header(instream)
    header = _common.append_pg_to_sam_header(
        header,
        {'ID': UTIL_NAME,
         'PN': UTIL_NAME,
         'VN': __version__,
         'CL': ' '.join(sys.argv)
         })

    outstream.writelines(header)

    for line in pairsam_body_stream:
        cols = line[:-1].split('\v')
        cols[_common.COL_PTYPE] = 'DD'
        
        for i in (_common.COL_SAM1,
                  _common.COL_SAM2):
                
            # split each sam column into sam entries, tag and assemble back
            cols[i] = _common.SAM_ENTRY_SEP.join(
                [mark_sam_as_dup(sam) 
                 for sam in cols[i].split(_common.SAM_ENTRY_SEP)
                ])

        outstream.write('\v'.join(cols))
        outstream.write('\n')

    if instream != sys.stdin:
        instream.close()
    if outstream != sys.stdout:
        outstream.close()

def mark_sam_as_dup(sam):
    '''Tag the binary flag and the optional pair type field of a sam entry
    as a PCR duplicate.'''
    samcols = sam.split('\t')
    samcols[1] = str(int(samcols[1]) | 1024)

    for j in range(11, len(samcols)):
        if samcols[j].startswith('Yt:Z:'):
            samcols[j] = 'Yt:Z:DD'
    return '\t'.join(samcols)


if __name__ == '__main__':
    markasdup()
