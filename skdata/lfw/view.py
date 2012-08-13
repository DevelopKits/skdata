# Copyright (C) 2012
# Authors: Nicolas Pinto <pinto@alum.mit.edu>

# License: Simplified BSD

from copy import deepcopy

import numpy as np

from skdata.utils import dotdict
from skdata.utils import ImgLoader
from skdata.larray import lmap

import dataset


class BaseView2(object):

    DATASET_CLASS = None

    def __init__(self):

        if self.DATASET_CLASS is None:
            raise NotImplementedError("This is an abstract class")

        # -- build/fetch dataset
        ds = self.DATASET_CLASS()
        folds = ds.view2_folds

        # -- lazy array helper function
        if ds.COLOR:
            loader = ImgLoader(ndim=3, dtype=np.float32, mode='RGB')
        else:
            loader = ImgLoader(ndim=2, dtype=np.float32, mode='L')

        def load_pair(pair):
            left_fname = ds.home('images', ds.IMAGE_SUBDIR, pair[0])
            left = loader(left_fname)
            right_fname = ds.home('images', ds.IMAGE_SUBDIR, pair[1])
            right = loader(right_fname)
            return np.array((left, right), dtype=np.float32)

        # -- for each fold build a lazy "split"
        splits = []
        all_x_fn = None
        all_y_fn = None
        for i, test_fold in enumerate(folds):

            # -- test
            test_fold = np.array(test_fold)

            test_x_fn = test_fold[:, :2]
            split_x_fn = deepcopy(test_x_fn)
            test_x = lmap(load_pair, test_x_fn)

            test_y = test_fold[:, 2].astype(int)
            split_y = deepcopy(test_y)

            if all_x_fn is None:
                all_x_fn = split_x_fn
                all_y = split_y
            else:
                all_x_fn = np.concatenate((all_x_fn, split_x_fn))
                all_y = np.concatenate((all_y, split_y))

            # -- train (filenames)
            train_x_fn = None
            train_y = None
            for j, train_fold in enumerate(folds):
                if j == i:
                    continue
                train_fold = np.array(train_fold)
                _train_x_fn = train_fold[:, :2]
                _train_y = train_fold[:, 2].astype(int)
                if train_x_fn is None:
                    train_x_fn = _train_x_fn
                    train_y = _train_y
                else:
                    train_x_fn = np.concatenate((train_x_fn, _train_x_fn))
                    train_y = np.concatenate((train_y, _train_y))

            split_x_fn = np.concatenate((split_x_fn, train_x_fn))
            split_y = np.concatenate((split_y, train_y))

            split_x = lmap(load_pair, train_x_fn)
            train_x = lmap(load_pair, train_x_fn)

            split = dotdict(
                x=split_x,
                y=split_y,
                train=dotdict(x=train_x, y=train_y),
                test=dotdict(x=test_x, y=test_y),
                )
            splits += [split]

        all_x = lmap(load_pair, all_x_fn)
        all_y = lmap(load_pair, all_y_fn)

        self.dataset = ds
        self.x = all_x
        self.y = all_y
        self.splits = splits


class OriginalView2(BaseView2):
    DATASET_CLASS = dataset.Original


class FunneledView2(BaseView2):
    DATASET_CLASS = dataset.Funneled


class AlignedView2(BaseView2):
    DATASET_CLASS = dataset.Aligned
