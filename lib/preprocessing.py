from datetime import datetime as dt
import json
import re

import numpy as np
import pandas as pd
from pandas import DataFrame, Index, Series


DATE_PATTERN = re.compile(r'(\d{2}):(\d{2}), (\d{1,2})\. (\S{3})\.? (\d{4})')

MONTHS = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun',
          'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']


def read(fns=["results/rechtsextremismus.json"]):
    df = None
    for fn in fns:
        with open(fn) as f:
            if df is None:
                df = DataFrame(json.load(f))
            else:
                df = df.append(DataFrame(json.load(f)))
    return df


def is_IPv4(string):
    # e.g. "23.123.0.42"
    pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    return re.match(pattern, string) is not None


def is_IPv6(string):
    # e.g. '2001:628:404:31:58c0:f621:1aea:e7f5'
    elem = r"[0-9a-f]{0,4}"
    pattern = r"^{}:{}:{}:{}:{}:{}:{}:{}$".format(elem, elem, elem, elem,
                                                elem, elem, elem, elem)
    return re.match(pattern, string) is not None


def is_IP(string):
    return is_IPv4(string) or is_IPv6(string)


def parse_size(string):
    """Given a string like `"(-48)"`, return an `int`
    of the edit size. It can be null.
    """
    if string == "null":
        return 0
    try:
        return int(string[1:-1])
    except ValueError:
        return 0


def parse_date(string):
    """Given a string like `"12:02, 28. M\u00e4r. 2018"`, or
    "`18:33, 1. Apr. 2019`",
    create a proper python datetime object.
    """
    match = re.match(DATE_PATTERN, string)
    try:
        hour, minute, day, mon, year = match.groups()
        mon = MONTHS.index(mon) + 1
        return dt(int(year), mon, int(day), int(hour), int(minute))
    except Exception as e:
        # Whatever, we return None anyway..
        print(e)
        pass
    return None


def revert_heuristic(name, change, cmp_name, cmp_change, early_dt, late_dt,
                     later_revert):
    # Always respect the revert marker, if present, but make sure that NaN
    # values are treated as falsey values.
    if later_revert is True:
        return True
    if name != cmp_name:
        return False
    if late_dt < early_dt:
        msg = (f'{name} and {cmp_name} are in the wrong order. {late_dt} is '
               f'earlier than {early_dt}.')
        raise ValueError(msg)
    return change + cmp_change == 0


def probably_revert(data):
    """"""
    orig = data[['pagename', 'change_size', 'date', 'revert']]
    prev = orig.shift(-1).add_prefix('prev_')
    merged = pd.concat([orig, prev], axis=1)
    return merged.apply(
        lambda x: revert_heuristic(
            x.pagename, x.change_size, x.prev_pagename, x.prev_change_size,
            x.prev_date, x.date, x.revert),
        axis=1
    )


def probably_reverted(data):
    """"""
    orig = data[['pagename', 'change_size', 'date', 'revert']]
    next_ = orig.shift(1).add_prefix('next_')
    merged = pd.concat([orig, next_], axis=1)
    return merged.apply(
        lambda x: revert_heuristic(
            x.pagename, x.change_size, x.next_pagename, x.next_change_size,
            x.date, x.next_date, x.next_revert),
        axis=1
    )


def normalize_change_size(data):
    data['change_size'].fillna(value=0, inplace=True)
    return data


def load_data():
    # Load most recent data.
    files = ["results/Geschichte_der_Malerei.json",
             "results/Rest.json",]
    data = (read(files)
        .assign(
            date=lambda x: x['date'].map(parse_date),
            is_ip=lambda x: x['user'].map(is_IP),
            change_size=lambda x:x['change_size'].astype(int))
        .assign(
            probably_revert=lambda x: probably_revert(x),
            probably_reverted=lambda x: probably_reverted(x),
        )
    )
    return data
