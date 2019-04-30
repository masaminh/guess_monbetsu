"""作成済みモデルを使用して予想する."""
from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime

from keras.models import load_model
import numpy

import horseracelib.jbis as jbis


def main():
    """メイン関数."""
    parser = ArgumentParser()
    parser.add_argument('-m', '--model', default='data/monbetsu.h5')
    parser.add_argument('infile')
    parser.add_argument('date', type=valid_date)
    parser.add_argument('distance', type=int)
    parser.add_argument('condition', choices=['良', '稍重', '重', '不良'])
    args = parser.parse_args()

    model = load_model(args.model)

    with open(args.infile, 'r') as file:
        urls = [line.strip() for line in file]

    access = jbis.Access()
    train_x = []

    for url in urls:
        horseresult = access.get_racelist_by_horseurl(url)

        horseraces = sorted(
            [
                x for x in horseresult
                if (
                    x[0].date < args.date and x[1].order.isdigit() and
                    x[1].weight is not None and x[1].money is not None and
                    x[1].poplar is not None)
            ],
            key=lambda x: x[0].date, reverse=True)[:10]

        for horserace in horseraces:
            distance = horserace[0].distance - args.distance
            sameplace = 1 if horserace[0].course == '門別' else 0
            samecondition = 1 if horserace[0].condition == args.condition else 0
            sametrack = 1 if horserace[0].tracktype == 'ダート' else 0

            train_x.extend((
                horserace[0].horsenum, horserace[1].money, horserace[1].order, distance,
                horserace[1].poplar, horserace[1].weight, horserace[1].time.total_seconds(
                ),
                sameplace, samecondition, sametrack
            ))
        if len(horseraces) < 10:
            train_x.extend([0] * (10 - len(horseraces)) * 10)

    shortnum = 16 - len(urls)
    if shortnum > 0:
        train_x.extend([0] * shortnum * 100)

    x_test = numpy.array(train_x)
    pred = model.predict(x_test.reshape(1, 1600))[0]

    for i, score in zip(range(len(urls)), pred):
        print(i+1, score)


def valid_date(arg):
    """引数から日付を取得する.

    Arguments:
        arg {str} -- 日付文字列

    Raises:
        argparse.ArgumentTypeError: 日付と解釈できない文字列

    Returns:
        date -- 日付への変換結果

    """
    try:
        return datetime.strptime(arg, "%Y-%m-%d").date()
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(arg)
        raise ArgumentTypeError(msg)


if __name__ == "__main__":
    main()
