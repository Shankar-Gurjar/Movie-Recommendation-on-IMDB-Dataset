#!/usr/bin/env python3
"""
    :brief: Script to get movie data from omdbApi
    :author: Akshat C
    :date: 11/02/19
"""
from multiprocessing import Pool
import json

import requests

BASE_URL = "https://www.omdbapi.com/"
config = {
    'apikey': '5a8ba10e',
    'plot': 'short',
    'r': 'json',
}


def fetch_data(id: str, onehot: list) -> dict:
    """Fetch adats from for each IMDBid from API

    :param id: str -> IMDB id of the movie
    :param onehot: str -> count encoding of the genres
    :return: dict of data of each movie
    """
    config['i'] = id
    print("Processing", id, end="\r", flush=True)
    res = requests.get(BASE_URL, params=config).json()
    res['onehot'] = onehot
    res['raters'] = []
    return res


def main():
    idt = json.load(open('idt.json'))
    comb_list = [(id, _['tags']) for id, _ in idt.items()]

    pool = Pool(8)
    data = pool.starmap_async(fetch_data, comb_list).get()
    pool.close()
    json.dump(data, open('data_final.json','w'))


if __name__ == "__main__":
    main()

