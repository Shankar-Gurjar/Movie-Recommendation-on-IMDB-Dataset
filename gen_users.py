#!/usr/bin/env python3
"""
12 - 24	    12 - 14	    14 - 24	    24-34   Ratio       Category        Male        Female      Ratio
15	        22	        8	        15	    1	        Animation	    75	        65	        1.153846154
33.5	    35	        32	        30	    1.1166      Comedy	        90	        91	        0.989010989
8.5	        5	        12	        11	    0.7727      Crime	        79	        84	        0.9404761905
4	        0.5	        7.5	        5.5	    0.7272      Horror	        57	        47	        1.212765957
40	        40	        40	        40	    1	        Action	        90	        86	        1.046511628
18	        18	        18	        18	    1	        SciFi	        76	        62          1.225806452
23.5	    20	        27	        27	    0.8703  	Drama	        80	        89	        0.8988764045
10.5        8	        13	        11	    0.9545  	Romance	        55	        77	        0.7142857143
"""
import os
import json
import random
import string
from sys import argv as rd
from math import ceil, floor, log10

from werkzeug.security import generate_password_hash
import pandas as pd
import pymongo

try:
    MONGO_URI = os.environ.get('DATABASE_URL', None)
    client = pymongo.MongoClient(MONGO_URI)
    DATABASE = MONGO_URI.split('/')[-1]
    db = client[DATABASE]
except Exception as e:
    print(f"Couldn't connect to database, check your $DATABASE_URL | {e}")
    exit(-1)

ran_n = lambda n: ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(n))
printj = lambda js: print(json.dumps(js, indent=4))
age_h = lambda ratio: ratio if ratio < 1 else 1 / ratio

data = json.load(open('data_final.json'))
raters = {_['imdbID']: [] for _ in data}
cross_mapping = pd.read_csv('genre_counts.csv')
age_mapping = {
    "Animation": 1,
    "Comedy": 1.116666667,
    "Crime": 0.7727272727,
    "Horror": 0.7272727273,
    "Action": 1,
    "Sci-Fi": 1,
    "Drama": 0.8703703704,
    "Romance": 0.9545454545,
}
gender_mapping = {
    "Animation":    [75, 65],
    "Comedy":   [90, 91],
    "Crime":    [79, 84],
    "Horror":   [57, 47],
    "Action":   [90, 86],
    "Sci-Fi":    [76, 62],
    "Drama":    [80, 89],
    "Romance":  [55, 77],
}
base_genres = ['Action', 'Animation', 'Comedy', 'Drama', 'Horror', 'Crime', 'Romance', 'Sci-Fi']
choices = [
    'Action',
    'Adventure',
    'Animation',
    'Biography',
    'Comedy',
    'Crime',
    'Drama',
    'Family',
    'Fantasy',
    'Film-Noir',
    'History',
    'Horror',
    'Music',
    'Musical',
    'Mystery',
    'Romance',
    'Sci-Fi',
    'Sport',
    'Thriller',
    'War',
    'Western',
]


def gen_genres(n: int, rand: bool=False) -> list:
    """Generate the liked and disliked genres on the basis of statistics

    :param n: int -> The number of genre sets
    :param rand: bool -> whether to use "random" generation
    :return genres: dict -> liked and disliked
    """

    def proc_user(user: list) -> tuple:
        """Process user and calculate gender
        :param user: list -> list of genres and ages
        :return genres, age: tuple -> age genre tuple
        """
        genres = [_ for _, i in user]
        age = 1 if sum([_ for i, _ in user]) > len(genres) / 2 else 0
        return genres, age

    if rand:
        genres = []
        for _ in range(n):
            print(f"Building genres {_}/{n}", end="\r", flush=True)
            likes = set(random.sample(choices, random.randint(0, int(2 * len(choices) / 3))))
            dislikes = list(random.sample(list(set(choices) - likes), random.randint(0, int(len(likes) / 3))))
            genres.append({
                'liked': list(likes),
                'disliked': dislikes
            })
            ages = [str(_ % 2) for _ in range(n)]
    else:
        users = list(range(n))
        male = set(random.sample(users, int(n / 2)))
        female = list(set(users) - male)
        male = list(female)
        categories = {_: {
            'people' : [],
            'count' : 0
        } for _ in choices}

        for category in categories:
            try:
                m_c, f_c = gender_mapping[category]
                idxs = random.sample(male, int(m_c / (m_c + f_c) * n / 2)) \
                                        + random.sample(female, int(f_c / (m_c + f_c) * n / 2))
            except KeyError:
                idxs = []
            finally:
                categories[category] = {
                    'people' : idxs,
                    'count' : len(idxs)
                }
            for i, ref_cat in enumerate(choices):
                samples = int(cross_mapping[category][i] * len(idxs))
                ref_idxs = random.sample(idxs, samples)
                ref_rec = categories[ref_cat]
                ref_rec.update({
                    'people': ref_rec['people'] + ref_idxs,
                    'count': ref_rec['count'] + samples
                })
        for category in categories:
            idxs = categories[category]['people']
            percent_ = age_h(age_mapping[category]) if category in age_mapping else 0.5
            age_1 = random.sample(idxs, int(len(idxs) * percent_))
            categories[category]['people'] = [(_, 1) if _ in age_1 else (_, 0) for _ in idxs]

        genres = [[] for _ in range(n)]
        [genres[idx].append((category, gen)) for category in categories for idx, gen in categories[category]['people']]
        genres = [proc_user(genre) for genre in genres]
        ages = [str(_) for i, _ in genres]
        genres = [_ for _, i in genres]
        liked = [set(_) for _ in genres]
        disliked = [random.sample(list(set(choices) - _), random.randint(0, int(0.40 * len(_)))) for _ in liked]
        genres = [{
            'liked' : list(liked),
            'disliked': disliked
            } for liked, disliked in zip(liked, disliked)
        ]

    return genres, ages


def gen_rating(genres: list) -> dict:
    """Generate movie ratings on the basis of genres liked

    :param genres: list -> list of genres
    :return ratings: dict -> dict of movie ratings
        {
            'imdbID' : val,
            ...
        }
    """
    liked, disliked = genres.values()
    final = []
    movie_set_like = set([_['imdbID'] for _ in data for genre in liked if genre in _['Genre']])
    movie_set_dislike = [_['imdbID'] for _ in data for genre in disliked if genre in _['Genre']]
    movie_set_like = list(movie_set_like - set(movie_set_dislike))
    like_n = 7 + random.randint(-1, 2)
    like_n = like_n if like_n <= len(movie_set_like) else len(movie_set_like)
    like_ids = random.sample(movie_set_like, like_n)

    dis_n = ceil(0.33 * like_n)
    dis_n = dis_n if dis_n <= len(movie_set_dislike) else len(movie_set_dislike)
    dis_n = random.randint(0,  dis_n)
    dislike_ids = random.sample(movie_set_dislike, dis_n)

    liked_movies = [(_['imdbID'], _['imdbRating'], _['Ratings']) for _ in data if _['imdbID'] in like_ids]
    disliked_movies = [(_['imdbID'], _['imdbRating'], _['Ratings']) for _ in data if _['imdbID'] in dislike_ids]

    liked_movies = [(imdbID, [imdbRating] + [_['Value'] for _ in ratings]) for imdbID, imdbRating, ratings in liked_movies]
    disliked_movies = [(imdbID, [imdbRating] + [_['Value'] for _ in ratings]) for imdbID, imdbRating, ratings in disliked_movies]
    for i, movie_t in enumerate([liked_movies, disliked_movies]):
        dev = lambda: -1 * i * random.random() * 3e-2
        for movieID, ratings in movie_t:
            rating = [float(_.split('/')[0]) if '/' in _ else float(_.split('%')[0]) if '%' in _ else float(_) for _ in ratings]
            rating = [_ / (10 ** ceil(log10(_))) for _ in rating]
            rating = (sum(rating) / len(rating) + dev())
            rating += -1 * i * random.random() * 0.5
            rating = 0 if rating < 0 else 1 if rating > 1 else rating
            final.append({
                'id' : movieID,
                'rating': round(10 * rating, 1)
            })
    return final


def gen_users(n: int) -> dict:
    """Generate random users
    :param n: int -> number of users to generate
    :return users: dict -> set of users with unique emails
    {
        'email': 'abc@email.com',
        'password': 'abc',
        'name' : 'abc xyz',
        'gender' : 'male/female',
        'age' : '0/1',
    }
    """
    emails = ['gmail', 'yahoo', 'hotmail', 'icloud']
    genders = ['male', 'female']
    ages = ['0', '1']
    users = []
    genres, ages = gen_genres(n, False)
    for _ in range(n):
        print(f"Building users {_}/{n}", end="\r", flush=True)
        name_ = ran_n(random.randint(5, 10))
        name = name_ + " " + ran_n(random.randint(5, 20))
        password = generate_password_hash(name_)
        email = f"{name_}@{random.choice(emails)}.com"
        raters.update({email: []})
        gender = genders[_ % 2]
        cur_user = {
            'email': email,
            'name': name,
            'age': ages[_],
            'gender': gender,
            'password': password,
            'Genre': genres[_],
            'picture': f"https://www.gravatar.com/avatar/{ran_n(32)}?s=200&d=identicon&r=PG%22"
        }
        cur_user['ratings'] = gen_rating(genres[_])
        [raters[_].append({
            'id': email,
            'rating': val
        }) for _, val in cur_user['ratings'].items()]
        users.append(cur_user)
    return users, raters


def updateMovies(raters: dict) -> None:
    """Update the movie database with the rater references as well

    :param raters: dict -> imdbID <-> list[email]
    :return None:
    """
    db.movies.update_many()


def main():
    users, raters = gen_users(int(rd[1]))
    json.dump(users, open('users.json', 'w'))
    updateMovies(raters)

if __name__ == "__main__":
    main()
