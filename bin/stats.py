from collections import OrderedDict
from datetime import datetime
import json
import re

import numpy as np
import pandas as pd
from pandas import DataFrame, Index, Series


DATE_PATTERN = re.compile(r'(\d{2}):(\d{2}), (\d{1,2})\. (\S{3})\.? (\d{4})')

MONTHS = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun',
          'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']


def load(fn="results/rechtsextremismus.json"):
    data = None
    with open(fn) as f:
        data = json.load(f)
    return data


def is_IPv4(string):
    # e.g. "23.123.0.42"
    pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    return re.match(pattern, string) is not None


def is_IPv6(string):
    # e.g. '2001:628:404:31:58c0:f621:1aea:e7f5'
    elem = r"[0-9a-f]{0,4}"
    pattern = r"{}:{}:{}:{}:{}:{}:{}:{}".format(elem, elem, elem, elem,
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
        return datetime(int(year), mon, int(day), int(hour), int(minute))
    except Exception as e:
        # Whatever, we return None anyway..
        print(e)
        pass
    return None


def page_stats(data):
    entries = [(i["user"], i["pagename"]) for i in data]
    page_count = len({i[1] for i in entries})
    s = f"""
    Anzahl Seiten:\t {page_count}
    """
    return s


def user_stats(data):
    # Count number of entries.
    entry_count = len(data)
    anon_count = len([i["user"] for i in data if is_IP(i["user"])])
    reg_count = entry_count - anon_count
    # Count number of users.
    user_set = {i["user"] for i in data}
    all_users = len(user_set)
    anon_users = len([u for u in user_set if is_IP(u)])
    reg_users = all_users - anon_users

    s = f"""
    Anzahl revs:\t {entry_count}
    # anon. revs:\t {anon_count}
    # reg. revs:\t {reg_count}
    % of anon:\t\t {(anon_count / entry_count * 100):.3}%
    ----
    Anzahl users:\t {all_users}
    # anon. users:\t {anon_users}
    # reg. users:\t {reg_users}
     % of anon:\t\t {(anon_users / all_users * 100):.3}%
    """
    return s


def time_stats(data):
    entries = [(i['user'], parse_date(i['date'])) for i in data]
    return ""


def edit_size_stats(data):
    entries = [(i['user'], parse_size(i['change_size'])) for i in data]
    return ""


def general_stats(data):
    """Extract:
    • Number of pages
    • Number of edits
    • Number of anonymous edits
    • Proportion of anonymous edits
    • Number of unique users (non-anonymous)
    """
    if len(data) == 0:
        return  {}
    edit_count = len(data)
    page_count = len({e['pagename'] for e in data})
    user_count = len({e['user'] for e in data if not is_IP(e['user'])})
    anon_edit_count = len([e for e in data if is_IP(e['user'])])
    anon_edit_prop = anon_edit_count / edit_count
    return {
        "edit_count": edit_count,
        "page_count": page_count,
        "user_count": user_count,
        "anon_edit_count": anon_edit_count,
        "anon_edit_prop": anon_edit_prop,
    }


def filter_irrelevant(data):
    """Filter out edits which are very small or instantly reverted."""


def stats_by_category(data):
    """
    • Number of pages per category
    • Number of edits per category
    • Number of anonymous edits
    • Proportion of anonymous edits
    • Number of unique users (non-anonymous)
    """
    cats = {e["category"] for e in data}
    return {
        cat: general_stats([e for e in data if e['category'] == cat])
        for cat in cats
    }


def stats_by_page(data):
    """Accumulate stats by page:
    • Number of pages per page
    • Number of edits per page
    • Number of anonymous edits
    • Proportion of anonymous edits
    • Number of unique users (non-anonymous)
    """
    pages = {e['pagename'] for e in data}
    return {
        page: general_stats([e for e in data if e['pagename'] == page])
        for page in pages
    }


""" def order_by_anon_prop(data):
    data = OrderedDict(data)
    data = sorted(data.items(), key=lambda x: x[1]['anon_edit_prop'])
    return data """


def combine_dfs(d1, d2):
    return d1.append(d2)


def to_dataframe(data):
    return DataFrame(data)


def add_is_IP(data):
    """Compute and add a new column to the `DataFrame` which contains info
    about wether the user name is just an IP address.
    """
    data['is_IP'] = data['user'].map(is_IP)
    return data



def add_revert_heuristic(data):
    """This is much better than my previous try, but it still depends on the
    data frame being sorted by date and the edits of each page being grouped
    together.
    """
    df_1 = data[['pagename', 'int_change_size']]
    df_2 = df_1.shift(-1).add_prefix('next_')
    merged = pd.concat([df_1, df_2], axis=1)

    def is_revert(name, change, next_name, next_change):
        """Do the actual work."""
        pass
    def is_reverted(name, change, next_name, next_change):
        pass
    
    reverts = merged.apply(
        lambda x: is_revert(x.pagename, x.int_change_size, x.next_pagename,
                            x.next_int_change_size),
        axis=1)
    reverted = merged.apply(
        lambda x: is_reverted(x.pagename, x.int_change_size, x.next_pagename,
                              x.next_int_change_size),
        axis=1)
    data['probably_revert'] = reverts
    data['probably_reverted'] = reverted
    return data


""" 
def add_reverted(data): """
    """Compute and add a new column to the `DataFrame` which indicates if
    an edit is 'probably an revert' or 'probably got reverted'. This is based
    on the assumption, that an edit that has the exact inverse of the previous
    edit as its change_size, probably reverts its predecessor.

    Note: this depends heavily on the concrete shape of the dataframe!! 
    It currently looks like this:
    0 => Index
    1 => category
    2 => change_size
    3 => date
    4 => history_size
    5 => minor
    6 => pagename
    7 => revert
    8 => subcat
    9 => user
    10 => datetime
    11 => int_change_size
    12 => is_IP

    Note also that this depends on the edits being sorted in such a way, that
    all the edits of each page are consecutive.

    All in all, this code is kind of ugly, maybe I will find a better way in
    the future...
    """
   """  prev_change_size = 0
    prev_pagename = None
    reverts = [False]
    reverted = []

    # For every edit, check if it probably reverts the previous one.
    # Then, save its change_size to make it possible to check the next.
    for (idx, _, _, _, _, _, pagename, revert, _, _, _, int_change_size, _) in data.itertuples():
        if revert:
            # If revert is already set, trust it.
            reverts.append(True)
            reverted.append(True)
        elif pagename != prev_pagename and prev_pagename is not None:
            # If we are on a new page, add default values, because we can not know
            # wether the first edit is a revert.
            reverts.append(False)
            reverted.append(False)
        else:
            # Our actual heuristic..
            guess = (int_change_size + prev_change_size) == 0
            reverts.append(guess)
            reverted.append(guess)
        # Always update the size of the last change and the last pagename.
        prev_change_size = int_change_size
        prev_pagename = pagename
    
    # We can not know if the very last edit got reverted.
    reverted.append(False)

    assert(data.shape[0] == len(reverts))
    data['probably_revert'] = reverts
    data['probably_reverted'] = reverted
    return data """


def normalize_change_size(data):
    data['change_size'].fillna(value=0, inplace=True)
    return data


def main():
    # Load most recent data.
    d1 = load("results/Geschichte_der_Malerei.json")
    d2 = load("results/Rest.json")
    data = combine_dfs(to_dataframe(d1), to_dataframe(d2))

    # Add derivative data columns.
    data['datetime'] = data['date'].map(parse_date)
    data['change_size'] = data['change_size'].map(int)
    data['is_IP'] = data['user'].map(is_IP)

    return data