"""予想に必要なデータを収集する."""
import csv
import sqlite3
from argparse import ArgumentParser
from contextlib import closing
from datetime import timedelta
from itertools import chain, repeat

from tqdm import tqdm

import horseracelib.jbis
from horseracelib.utility import HorseResult, RaceCalendar, RaceInfo


def main():
    """メイン関数."""
    p = ArgumentParser()
    p.add_argument('-d', '--cachedb', default='cache.db')
    p.add_argument('-c', '--course', default='門別')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    p.add_argument('outfile')
    args = p.parse_args()

    access = horseracelib.jbis.Access()

    with closing(sqlite3.connect(
            args.cachedb, detect_types=sqlite3.PARSE_DECLTYPES)) as conn:
        conn.row_factory = sqlite3.Row

        racedaysurl = [
            x.url
            for x in _read_racedays(conn, access, args.start, args.end, args.course)]
        races = _read_races(conn, access, racedaysurl)
        del racedaysurl

        raceurls = [x.url for x in races]
        results = _read_race_results(conn, access, raceurls)
        del raceurls

        horseraceresults = chain.from_iterable(x[1] for x in results)
        horseurls = {x.url for x in horseraceresults}
        del horseraceresults
        horseresults = _read_horse_results(conn, access, horseurls)
        del horseurls

    with open(args.outfile, 'w', newline='') as csvfile:
        w = csv.writer(csvfile)
        for url, train_x, train_y in _iter_train_data(results, horseresults):
            w.writerow([url] + train_x + train_y)


def _read_racedays(conn, access, start, end, course):

    def get_month_racedays(yearmonth):
        year, month = divmod(yearmonth, 100)
        c = conn.cursor()
        c.execute(
            'SELECT date,course,url FROM iter_race_calendar '
            'WHERE year=? AND month=? ORDER BY date',
            (year, month)
        )
        racedays = [
            RaceCalendar(r['date'], r['course'], r['url'])
            for r in c.fetchall()]
        if not racedays:
            racedays = list(access.iter_race_calendar(year, month))
            c.executemany(
                'INSERT INTO iter_race_calendar '
                '(year,month,date,course,url) '
                'VALUES (?,?,?,?,?)',
                ((year, month, x.date, x.course, x.url) for x in racedays))
            conn.commit()

        return racedays

    def iter_monthrange(start, end):
        yearmonth = start

        while yearmonth <= end:
            yield yearmonth

            year, month = divmod(yearmonth, 100)
            if month >= 12:
                yearmonth = (year + 1) * 100 + 1
            else:
                yearmonth += 1

    return list(
        x for x in (chain.from_iterable(
            get_month_racedays(m)
            for m in tqdm(list(iter_monthrange(start, end)))))
        if x.course == course)


def _read_races(conn, access, urls):
    def get_day_races(url):
        c = conn.cursor()
        c.execute(
            'SELECT date,course,raceno,racename,tracktype,distance,'
            'condition,horsenum,url FROM iter_races_by_url '
            'WHERE dayurl=? ORDER BY date', (url,))
        races = [
            RaceInfo(
                r['date'], r['course'], r['raceno'], r['racename'],
                r['tracktype'], r['distance'], r['condition'],
                r['horsenum'], r['url'])
            for r in c.fetchall()]
        if not races:
            races = list(access.iter_races_by_url(url))
            c.executemany(
                'INSERT INTO iter_races_by_url '
                '(dayurl,date,course,raceno,racename,tracktype,'
                'distance,condition,horsenum,url) '
                'VALUES (?,?,?,?,?,?,?,?,?,?)',
                ((url, x.date, x.course, x.raceno, x.racename,
                  x.tracktype, x.distance, x.condition,
                  x.horsenum, x.url) for x in races))
            conn.commit()

        return races

    return list(chain.from_iterable(
        get_day_races(url)
        for url in tqdm(urls)))


def _read_race_results(conn, access, urls):
    def get_race_results(url):
        c = conn.cursor()
        c.execute(
            'SELECT date,course,raceno,racename,tracktype,distance,'
            'condition,horsenum,url '
            'FROM get_race_result_by_url_raceinfo '
            'WHERE url=?', (url,))
        r = c.fetchone()
        if r:
            raceinfo = RaceInfo(
                r['date'], r['course'], r['raceno'], r['racename'],
                r['tracktype'], r['distance'], r['condition'],
                r['horsenum'], r['url'])
            c.execute(
                'SELECT horseorder,name,poplar,'
                'weight,time,url,money,no '
                'FROM get_race_result_by_url_horse '
                'WHERE raceurl=?', (url,))
            horseresult = [
                HorseResult(
                    r['horseorder'], r['name'], r['poplar'], r['weight'],
                    timedelta(seconds=r['time']) if r['time'] else None,
                    r['url'], r['money'], r['no'])
                for r in c.fetchall()
            ]
        else:
            raceinfo, horseresult = access.get_race_result_by_url(url)
            c.execute(
                'INSERT INTO get_race_result_by_url_raceinfo '
                '(date,course,raceno,racename,tracktype,distance,'
                'condition,horsenum,url) VALUES (?,?,?,?,?,?,?,?,?)',
                (raceinfo.date, raceinfo.course,
                 raceinfo.raceno, raceinfo.racename,
                 raceinfo.tracktype, raceinfo.distance,
                 raceinfo.condition, raceinfo.horsenum, raceinfo.url))
            c.executemany(
                'INSERT INTO get_race_result_by_url_horse '
                '(raceurl,horseorder,name,poplar,weight,time,url,'
                'money,no) VALUES (?,?,?,?,?,?,?,?,?)',
                ((url, x.order, x.name, x.poplar, x.weight,
                  x.time.total_seconds() if x.time else None,
                  x.url, x.money, x.no)
                 for x in horseresult)
            )
            conn.commit()

        return raceinfo, horseresult

    return [get_race_results(url) for url in tqdm(urls)]


def _read_horse_results(conn, access, urls):
    def get_horse_results(url):
        c = conn.cursor()
        c.execute(
            'SELECT '
            'date,course,raceno,racename,tracktype,distance,'
            'condition,horsenum,raceurl,horseorder,name,poplar,'
            'weight,time,url,money,no '
            'FROM get_racelist_by_horseurl '
            'WHERE url=? ORDER BY date', (url,))
        results = [
            (
                RaceInfo(
                    r['date'], r['course'], r['raceno'], r['racename'],
                    r['tracktype'], r['distance'], r['condition'],
                    r['horsenum'], r['raceurl']),
                HorseResult(
                    r['horseorder'], r['name'], r['poplar'], r['weight'],
                    timedelta(seconds=r['time']) if r['time'] else None,
                    r['url'], r['money'], r['no']))
            for r in c.fetchall()
        ]
        if not results:
            results = access.get_racelist_by_horseurl(url)
            c.executemany(
                'INSERT INTO get_racelist_by_horseurl '
                '(date,course,raceno,racename,tracktype,distance,'
                'condition,horsenum,raceurl,horseorder,name,poplar,'
                'weight,time,url,money,no) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                ((r.date, r.course, r.raceno, r.racename,
                  r.tracktype, r.distance, r.condition,
                  r.horsenum, r.url, h.order, h.name, h.poplar,
                  h.weight,
                  h.time.total_seconds() if h.time else None,
                  h.url, h.money, h.no)
                 for r, h in results))
            conn.commit()

        return results

    result = {
        url: get_horse_results(url)
        for url in tqdm(sorted(list(urls)))
    }
    return result


def _iter_train_data(results, horseresults):
    for race, horses in tqdm(results):
        train_x = []
        train_y = []
        for h in sorted(horses, key=lambda x: x.no):
            train_y.append(1 if h.order == '1' else 0)
            horseraces = sorted(
                [
                    x for x in horseresults[h.url]
                    if (
                        x[0].date < race.date and x[1].order.isdigit() and
                        x[1].weight is not None and x[1].money is not None and
                        x[1].poplar is not None)
                ],
                key=lambda x: x[0].date, reverse=True)[:10]
            for r in horseraces:
                distance = r[0].distance-race.distance
                sameplace = 1 if r[0].course == race.course else 0
                samecondition = 1 if r[0].condition == race.condition else 0
                sametrack = 1 if r[0].tracktype == race.tracktype else 0

                train_x.extend((
                    r[0].horsenum, r[1].money, r[1].order, distance,
                    r[1].poplar, r[1].weight, r[1].time.total_seconds(),
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
