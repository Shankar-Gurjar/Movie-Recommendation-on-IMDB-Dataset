#!/usr/bin/env python3
"""
    :brief: Script to download IMDB ids
    :author: Akshat C
    :date: 11/02/19
"""
import re
from random import sample
from multiprocessing import Pool
import json

from bs4 import BeautifulSoup
import numpy as np
import requests

BASE_URL = "https://www.imdb.com/search/title"
keys = {
    'groups': 'top_250',
    'sort': 'user_rating,desc',
}
GENRES = [
    'action',
    'animation',
    'comedy',
    'documentary',
    'drama',
    'horror',
    'crime',
    'romance',
    'sci-fi',
]

def make_genres(genres: list) -> list:
    """Creates combination of genres from the list

    :return genre_set: list -> list of lists of genres
    """
    gen_len = len(genres)
    perms = np.array(np.meshgrid(*[[0, 1] for _ in
                                  range(gen_len)])).T.reshape(-1, gen_len)
    perms = np.ndarray.tolist(perms)[1:]  # remove NULL value
    return list(map(lambda x: [GENRES[_] for
                               _, val in enumerate(x) if val], perms))


def get_body(flags: list) -> tuple:
    """Given genres, return an IMDB ID and the one hot
    encoding

    :param flags: list -> the genres to search for
    :return id, hot_flags: tuple -> the IMDB id + flags
    """
    genres = ','.join(flags)
    keys['genres'] = genres
    print("Fetching", genres)
    text = requests.get(BASE_URL, params=keys).text
    onehot = [1 if _ in flags else 0 for _ in GENRES]
    return text, onehot


def extract_ids(body: str, onehot: list) -> list:
    """Extract the IMDB id and title

    :param body: str -> html response
    :param onehot: list -> onehot encoding
    :return tuple: (imdb_id, name, onehot) -> params
    """
    print("Extracting", onehot)
    soup = BeautifulSoup(body).find('div', {'id': "main"})
    headers = soup.findAll('h3', {'class': "lister-item-header"})
    hrefs = [_.find('a') for _ in headers]
    return {
        'onehot' : onehot,
        'movies' : [
            {
                'id' : _['href'].split('/')[2],
                'name' : _.text
            } for _ in hrefs]
    }


def main():
    genre_set = make_genres(GENRES)

    pool = Pool(8)
    p_output = pool.map_async(get_body, genre_set).get()
    records = pool.starmap_async(extract_ids, p_output).get()
    pool.close()
    json.dump(records, open('records.json', 'w'))


if __name__ == "__main__":
    main()
