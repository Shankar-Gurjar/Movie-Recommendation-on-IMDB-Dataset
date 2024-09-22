import json

from flask import (Blueprint, abort, flash, g, jsonify, redirect,
                   render_template, request, session, url_for)

import app.home.helper as helper
from app import db, models, requires_auth

home = Blueprint('home', __name__, url_prefix='/movies')


@home.route('/', methods = ['GET'])
def home_route():
	# TODO: modify rating indexing for updated schema
	uid = session['user_uid'] if 'user_uid' in session else None
	user = db.users.find_one({ 'email' : uid })
	context_kwargs = {
		'title': "Homepage",
		'data': db.movies.find(),
		'user': user,
	}
	return render_template('home/index.html.j2', **context_kwargs)


@home.route('/<imdbid>/', methods=['GET'])
@requires_auth
def mov_info(imdbid):
	# TODO: modify rating indexing for updated schema
	movie = db.movies.find_one({ "imdbID" : imdbid })
	user = db.users.find_one({ 'email' : session['user_uid']})
	if movie is None:
		abort(404)
	top_info = ['Year', 'imdbRating', 'Runtime', 'Genre', 'Director', 'Actors', 'Language']
	more_info = ['Awards', 'imdbVotes', 'imdbID', 'Website', 'Production', 'Country']
	genres = ['Action', 'Animation', 'Comedy', 'Documentary', 'Drama', 'Horror', 'Crime', 'Romance', 'Sci-Fi']
	genres = [(cat, val) for cat, val in zip(genres, movie['onehot'])]
	ratings = movie['Ratings']
	context_kwargs = {
		'title': movie['Title'],
		'movie' : movie,
		'top_info': top_info,
		'more_info': more_info,
		'genres' : genres,
		'ratings': ratings,
		'user': user,
	}
	return render_template('home/movie.html.j2', **context_kwargs)


@home.route('/updateRating/', methods=['POST'])
def update_route():
	try:
		email = session['user_uid']
		rating = float(request.form['rating'])
		imdbID = request.form['imdbID']

		user = db.users.find_one({'email' : email })
		ratings = user['ratings']
		movie = db.movies.find_one({ 'imdbID' : imdbID })
		raters = movie['raters']

		rater_obj = { 'id' : email, 'rating' : rating }  # insert into movie
		rating_obj = { 'id' : imdbID, 'rating' : rating }  # insert into user

		try:
			# check existing
			rating_idx = ratings.index(rating_obj)
			rater_idx = raters.index(rater_obj)
			ratings[rating_idx] = rating_obj
			raters[rater_idx] = rater_obj
		except ValueError:
			# otherwise append
			ratings.append(rating_obj)
			raters.append(rater_obj)
		finally:
			db.users.update_one({
				'_id': user['_id']
			},{
				'$set': {
					'ratings': ratings
				}
			}, upsert=True)
			db.movies.update_one({
				'_id': movie['_id']
			},{
				'$set': {
					'raters': raters
				}
			}, upsert=True)
		return jsonify({ 'status': True })
	except Exception as e:
		return jsonify({
			'status': False,
			'error': f"An error occured {str(e)}",
		})