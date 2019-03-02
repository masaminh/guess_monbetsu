"""予想に必要なデータを収集する."""
import csv
from argparse import ArgumentParser
from itertools import chain, repeat

from tqdm import tqdm

import horseracelib.jbis
from cached_access import CachedAccess


def main():
    """メイン関数."""
    parser = ArgumentParser()
    parser.add_argument('-d', '--cachedb', default='data/cache.db')
    parser.add_argument('-c', '--course', default='門別')
    parser.add_argument('start', type=int)
    parser.add_argument('end', type=int)
    parser.add_argument('outfile')
    args = parser.parse_args()

    with CachedAccess(args.cachedb) as access:
        racedaysurl = [x.url for x
                       in access.read_racedays(args.start, args.end, args.course)]

        races = access.read_races(racedaysurl)
        del racedaysurl

        raceurls = [x.url for x in races]
        results = access.read_race_results(raceurls)
        del raceurls

        horseraceresults = chain.from_iterable(x[1] for x in results)
        horseurls = {x.url for x in horseraceresults}
        del horseraceresults
        horseresults = access.read_horse_results(horseurls)
        del horseurls

    access = horseracelib.jbis.Access()

    with open(args.outfile, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for url, train_x, train_y in _iter_train_data(results, horseresults):
            writer.writerow([url] + train_x + train_y)


def _iter_train_data(results, horseresults):
    for race, horses in tqdm(results):
        train_x = []
        train_y = []
        for horse in sorted(horses, key=lambda x: x.no):
            train_y.append(1 if horse.order == '1' else 0)
            horseraces = sorted(
                [
                    x for x in horseresults[horse.url]
                    if (
                        x[0].date < race.date and x[1].order.isdigit() and
                        x[1].weight is not None and x[1].money is not None and
                        x[1].poplar is not None)
                ],
                key=lambda x: x[0].date, reverse=True)[:10]
            for horserace in horseraces:
                distance = horserace[0].distance-race.distance
                sameplace = 1 if horserace[0].course == race.course else 0
                samecondition = 1 if horserace[0].condition == race.condition else 0
                sametrack = 1 if horserace[0].tracktype == race.tracktype else 0

                train_x.extend((
                    horserace[0].horsenum, horserace[1].money, horserace[1].order, distance,
                    horserace[1].poplar, horserace[1].weight, horserace[1].time.total_seconds(
                    ),
                    sameplace, samecondition, sametrack
                ))
            if len(horseraces) < 10:
                train_x.extend([0] * (10 - len(horseraces)) * 10)

        shortnum = 16 - len(train_y)
        if shortnum > 0:
            train_y.extend([0] * shortnum)
            train_x.extend([0] * shortnum * 100)

        if train_x == list(repeat(0.0, 16*10*10)):
            continue

        assert len(train_y) == 16
        assert len(train_x) == 16 * 10 * 10
        yield race.url, train_x, train_y


if __name__ == "__main__":
    main()
