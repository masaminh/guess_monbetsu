"""ユーティリティ."""

import csv
from typing import Tuple

import numpy


def read_data(filename: str) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """訓練データ用CSVを読む.

    Arguments:
        filename {str} -- ファイル名

    Returns:
        Tuple[numpy.ndarray, numpy.ndarray] -- xの配列, yの配列

    """
    x_array = []
    y_array = []
    urls = []

    with open(filename, 'r') as file:
        for row in csv.reader(file):
            x_array.append([float(e) for e in row[1:-16]])
            y_array.append([float(e) for e in row[-16:]])
            urls.append(row[0])

    return numpy.array(x_array), numpy.array(y_array), numpy.array(urls)
