"""キャッシュ化したjbis.Access."""
import sqlite3
from datetime import timedelta
from itertools import chain
from typing import List, Tuple, Dict

from tqdm import tqdm

import horseracelib.jbis
from horseracelib.utility import HorseResult, RaceCalendar, RaceInfo


class CachedAccess:
    """キャッシュ化したjbis.Access."""

    def __init__(self, cachedb: str):
        """コンストラクタ.

        Arguments:
            cachedb {str} -- キャッシュファイルへのパス.
        """
        self.cachedb = cachedb
        self.access = None
        self.conn = None

    def __enter__(self):
        """with文で指定された際に呼び出される."""
        self.access = horseracelib.jbis.Access()
        self.conn = sqlite3.connect(
            self.cachedb, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row
        return self

    def __exit__(self, ex_type, ex_value, trace):
        """with文のスコープから抜けた際に呼び出される."""
        self.conn.close()

    def read_racedays(self, start: int, end: int, course: str) -> List[RaceCalendar]:
        """レースカレンダーを取得する.

        Arguments:
            start {int} -- 取得開始年月 2018年1月なら201801
            end {int} -- 取得終了年月 2018年1月なら201801
            course {str} -- 取得対象競馬場名

        Returns:
            List[RaceCalendar] -- 開催日情報

        """
        def get_month_racedays(yearmonth):
            year, month = divmod(yearmonth, 100)
            cur = self.conn.cursor()
            cur.execute(
                'SELECT date,course,url FROM iter_race_calendar '
                'WHERE year=? AND month=? ORDER BY date',
                (year, month)
            )
            racedays = [
                RaceCalendar(r['date'], r['course'], r['url'])
                for r in cur.fetchall()]
            if not racedays:
                racedays = list(self.access.iter_race_calendar(year, month))
                cur.executemany(
                    'INSERT INTO iter_race_calendar '
                    '(year,month,date,course,url) '
                    'VALUES (?,?,?,?,?)',
                    ((year, month, x.date, x.course, x.url) for x in racedays))
                self.conn.commit()

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

    def read_races(self, urls: List[str]) -> List[RaceInfo]:
        """レース一覧を取得する.

        Arguments:
            urls {List[str]} -- 取得元になる日単位でのURL一覧

        Returns:
            List[RaceInfo] -- レース情報のリスト

        """
        def get_day_races(url):
            cur = self.conn.cursor()
            cur.execute(
                'SELECT date,course,raceno,racename,tracktype,distance,'
                'condition,horsenum,url FROM iter_races_by_url '
                'WHERE dayurl=? ORDER BY date', (url,))
            races = [
                RaceInfo(
                    r['date'], r['course'], r['raceno'], r['racename'],
                    r['tracktype'], r['distance'], r['condition'],
                    r['horsenum'], r['url'])
                for r in cur.fetchall()]
            if not races:
                races = list(self.access.iter_races_by_url(url))
                cur.executemany(
                    'INSERT INTO iter_races_by_url '
                    '(dayurl,date,course,raceno,racename,tracktype,'
                    'distance,condition,horsenum,url) '
                    'VALUES (?,?,?,?,?,?,?,?,?,?)',
                    ((url, x.date, x.course, x.raceno, x.racename,
                      x.tracktype, x.distance, x.condition,
                      x.horsenum, x.url) for x in races))
                self.conn.commit()

            return races

        return list(chain.from_iterable(
            get_day_races(url)
            for url in tqdm(urls)))

    def read_race_results(self, urls: List[str]) -> List[Tuple[RaceInfo, List[HorseResult]]]:
        """レース結果を取得する.

        Arguments:
            urls {List[str]} -- [description]

        Returns:
            List[Tuple[RaceInfo, List[HorseResult]]] -- レース結果

        """
        def get_race_results(url):
            cur = self.conn.cursor()
            cur.execute(
                'SELECT date,course,raceno,racename,tracktype,distance,'
                'condition,horsenum,url '
                'FROM get_race_result_by_url_raceinfo '
                'WHERE url=?', (url,))
            row = cur.fetchone()
            if row:
                raceinfo = RaceInfo(
                    row['date'], row['course'], row['raceno'], row['racename'],
                    row['tracktype'], row['distance'], row['condition'],
                    row['horsenum'], row['url'])
                cur.execute(
                    'SELECT horseorder,name,poplar,'
                    'weight,time,url,money,no '
                    'FROM get_race_result_by_url_horse '
                    'WHERE raceurl=?', (url,))
                horseresult = [
                    HorseResult(
                        row['horseorder'], row['name'], row['poplar'], row['weight'],
                        timedelta(seconds=row['time']
                                  ) if row['time'] else None,
                        row['url'], row['money'], row['no'])
                    for row in cur.fetchall()
                ]
            else:
                raceinfo, horseresult = self.access.get_race_result_by_url(url)
                cur.execute(
                    'INSERT INTO get_race_result_by_url_raceinfo '
                    '(date,course,raceno,racename,tracktype,distance,'
                    'condition,horsenum,url) VALUES (?,?,?,?,?,?,?,?,?)',
                    (raceinfo.date, raceinfo.course,
                     raceinfo.raceno, raceinfo.racename,
                     raceinfo.tracktype, raceinfo.distance,
                     raceinfo.condition, raceinfo.horsenum, raceinfo.url))
                cur.executemany(
                    'INSERT INTO get_race_result_by_url_horse '
                    '(raceurl,horseorder,name,poplar,weight,time,url,'
                    'money,no) VALUES (?,?,?,?,?,?,?,?,?)',
                    ((url, x.order, x.name, x.poplar, x.weight,
                      x.time.total_seconds() if x.time else None,
                      x.url, x.money, x.no)
                     for x in horseresult)
                )
                self.conn.commit()

            return raceinfo, horseresult

        return [get_race_results(url) for url in tqdm(urls)]

    def read_horse_results(self, urls: List[str]) -> Dict[str, List[Tuple[RaceInfo, HorseResult]]]:
        """馬のレース結果を取得する.

        Arguments:
            urls {List[str]} -- 馬のURL

        Returns:
            Dict[str, List[Tuple[RaceInfo, HorseResult]]] -- 馬ごとのレース結果

        """
        def get_horse_results(url):
            cur = self.conn.cursor()
            cur.execute(
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
                for r in cur.fetchall()
            ]
            if not results:
                results = self.access.get_racelist_by_horseurl(url)
                cur.executemany(
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
                self.conn.commit()

            return results

        result = {
            url: get_horse_results(url)
            for url in tqdm(sorted(list(urls)))
        }
        return result
