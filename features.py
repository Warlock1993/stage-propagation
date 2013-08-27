#!/usr/bin/env python

import numpy as np
import os
import tempfile

import tsh; logger = tsh.create_logger(__name__)
from utils import read_argsfile, read_listfile, write_listfile, clean_args
from features_chaincode import get_chaincode_features, prepare_chaincode_features

def get_pregenerated_features(sample, feature_names=None, **kwargs):
    assert feature_names is not None
    return np.array([ sample[f] for f in feature_names ], dtype=np.float64)


def prepare_pregenerated_features(data, features=None, **kwargs):
    return {}


method_table = {
        'pregenerated': { 'function': get_pregenerated_features, 'prepare': prepare_pregenerated_features },
        'chaincode': { 'function': get_chaincode_features, 'prepare': prepare_chaincode_features }
        }


def compute_features(method_name, method_args, data, output_dir=None):
    cache = {}
    args = method_args.copy()
    additional_args = method_table[method_name]['prepare'](data, output_dir=output_dir, **args)
    args.update(additional_args)
    feature_names = args['feature_names']
    #del args['feature_names']
    compute_fn = method_table[method_name]['function']
    N = len(data)
    d = len(feature_names)
    _f = np.zeros((N, d), dtype=np.float64)
    for i in range(N):
        _f[i, :] = compute_fn(data[i], cache=cache, **args)
    features = np.core.records.fromarrays(
            [data['id']] + [_f[:, i] for i in range(_f.shape[1])],
            dtype=zip(['id'] + feature_names, [data.dtype['id']] + [np.float64] * d))
    args['feature_method'] = method_name
    return args, features


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Computes features for all the input data.')
    parser.add_argument('-c', '--config', dest='config', required=False, action='store', default=None, help='Path to the config file')
    parser.add_argument('-m', '--method', dest='method', required=True, action='store', choices=method_table.keys(), default=None, help='Method name.')
    parser.add_argument('-a', '--args', dest='args', required=False, action='store', default=None, help='Method arguments file.')
    parser.add_argument('-l', '--list', dest='list', required=True, action='store', default=None, help='List file.')
    parser.add_argument('-o', '--output', dest='output', required=False, action='store', default=None, help='Output directory.')
    opts = parser.parse_args()
    if opts.output == None:
        outdir = tempfile.mkdtemp(dir=os.curdir, prefix='out')
        logger.info('Output directory %s', outdir)
    else:
        outdir = opts.output
        if not os.path.exists(outdir):
            tsh.makedirs(outdir)
    config = tsh.read_config(opts, __file__)
    meta, data = read_listfile(opts.list)
    args = meta
    if opts.args != None:
        args.update(read_argsfile(opts.args))
    args, features = compute_features(opts.method, args, data, output_dir=outdir)
    clean_args(args)
    write_listfile(os.path.join(outdir, 'feats.csv'), features, **args)
