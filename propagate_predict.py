#!/usr/bin/env python

import numpy as np
import os
import tempfile

import tsh; logger = tsh.create_logger(__name__)
from utils import read_listfile, read_weightsfile, read_propagatorfile, write_listfile, clean_args

from propagate_train import method_table, get_weights

def propagate(method_name, method_args, predictions, dissim, output_dir=None):
    args = method_args.copy()
    label_name = args['truth'] + '_labels'
    labels = args[label_name]
    print 'Using weights bandwidth: %f' % args['bandwidth']
    weights = get_weights(dissim, args['bandwidth'])
    propagated = method_table[method_name]['function'](predictions, weights, labels=labels, output_dir=output_dir, **args)
    args['propagate_method'] = method_name
    return args, propagated


def propagate_predict(modelname, dissimname, predictionsname, outdir=None):
    if outdir == None:
        outdir = tempfile.mkdtemp(dir=os.curdir, prefix='out')
    else:
        if not os.path.exists(outdir):
            tsh.makedirs(outdir)
    args = {}
    predictions_meta, predictions = read_listfile(predictionsname)
    args.update(predictions_meta)
    dissim_meta, sample_ids, dissim = read_weightsfile(dissimname)
    assert (predictions['id'] == np.array(sample_ids)).all()
    assert predictions_meta['input_name'] == dissim_meta['input_name'], \
            'Expecting same input names (%s x %s)' % (predictions_meta['input_name'], dissim_meta['input_name'])
    inputname = predictions_meta['input_name']
    args.update(dissim_meta)
    model = read_propagatorfile(modelname)
    args.update(model['meta'])
    method_name = model['propagator']['method_name']
    del model['propagator']['method_name']
    args.update(model['propagator'])
    args, prop = propagate(method_name, args, predictions, dissim, output_dir=outdir)
    clean_args(args)
    del args['cv_results']
    write_listfile(os.path.join(outdir, inputname + '-propagated.csv.gz'), prop, **args)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Propagates labels using predictions and dissimilarities.')
    parser.add_argument('-m', '--model', dest='model', required=True, action='store', default=None, help='Model file.')
    parser.add_argument('-d', '--dissimilarities', dest='dissim', required=True, action='store', default=None, help='Dissimilarity file.')
    parser.add_argument('-p', '--predictions', dest='predictions', required=True, action='store', default=None, help='Predictions file.')
    parser.add_argument('-o', '--output', dest='output', required=False, action='store', default=None, help='Output directory.')
    opts = parser.parse_args()
    propagate_predict(opts.model, opts.dissim, opts.predictions, opts.output)
