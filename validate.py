"""テストデータを使って予想する."""

import csv
from argparse import ArgumentParser

from keras.models import load_model

from cached_access import CachedAccess
from utility import read_data


def main():
    """メイン関数."""
    parser = ArgumentParser()
    parser.add_argument('testfile')
    parser.add_argument('outfile')
    parser.add_argument('-m', '--model', default='data/monbetsu.h5')
    parser.add_argument('-d', '--cachedb', default='data/cache.db')
    args = parser.parse_args()

    model = load_model(args.model)

    x_tests, _, urls = read_data(args.testfile)

    with CachedAccess(args.cachedb) as access:
        race_results = {x[0].url: x for x in access.read_race_results(urls)}

    with open(args.outfile, 'w') as file:
        writer = csv.writer(file)

        for x_test, url in zip(x_tests, urls):
            _, horseresults = race_results[url]
            horseresults.sort(key=lambda x: x.no)
            pred = model.predict(x_test.reshape(1, 1600))[0]
            result = list(zip(((x.no, x.order) for x in horseresults), pred))
            result.sort(key=lambda x: x[1], reverse=True)
            writer.writerow(
                [url] +
                list(x[0][0] for x in result[0:4]) + list(x[0][1] for x in result[0:4]))


if __name__ == "__main__":
    main()
