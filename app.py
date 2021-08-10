#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
# init db
db.init_app(app)
migrate = Migrate(app, db);

# DONE: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # DONE: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  # Venues are aggregated by city, so query venue cities and then pull venue data.
  cities = db.session.query(Venue.city, Venue.state).distinct().all()
  data = []
  for city in cities:
    venues = []
    venues_list = db.session.query(Venue.id, Venue.name).filter_by(city = city[0], state = city[1]).all()
    for venue in venues_list:
      count = Show.query.filter_by(venue_id=venue[0]).count()
      venue_obj = {"id": venue[0], "name": venue[1], "num_upcoming_shows": count}
      venues.append(venue_obj)
    data.append({"city": city[0], "state": city[1], "venues": venues})

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  data = []
  query_result = Venue.query.filter(Venue.name.ilike('%' + request.form.get('search_term') + '%')).all()
  print(query_result)
  for venue in query_result:
    count = Show.query.filter_by(venue_id=venue.id).count()
    venue_obj = {
      "id" : venue.id,
      "name" : venue.name,
      "num_upcoming_shows" : count
    }
    data.append(venue_obj);
  response={
    "count": len(query_result),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # DONE: replace with real venue data from the venues table, using venue_id

  # pull venue information as well as separate genres into a list
  queried_venue=Venue.query.get(venue_id);
  queried_venue.genres = queried_venue.genres.split(",")

  # pull data for upcoming and past shows
  upcoming_shows = []
  upcoming_shows_query = db.session.query(Show.start_time, Show.artist_id, Artist.name, Artist.image_link).filter(Show.venue_id==venue_id, Show.start_time > datetime.today()).join(Artist, Show.artist_id == Artist.id).all()
  for show in upcoming_shows_query:
    print(show[0].strftime("%Y-%m-%dT:%H:%M:00.000Z"))
    show_obj = {"artist_id": show[1], "artist_name": show[2], "artist_image_link": show[3], "start_time": show[0].strftime("%Y-%m-%dT%H:%M:00.000Z")}
    upcoming_shows.append(show_obj)
  queried_venue.upcoming_shows = upcoming_shows
  queried_venue.upcoming_shows_count = len(upcoming_shows)

  past_shows = []
  past_shows_query = db.session.query(Show.start_time, Show.artist_id, Artist.name, Artist.image_link).filter(Show.venue_id==venue_id, Show.start_time <= datetime.today()).join(Artist, Show.artist_id == Artist.id).all()
  for show in past_shows_query:
    print(show[0].strftime("%Y-%m-%dT:%H:%M:00.000Z"))
    show_obj = {"artist_id": show[1], "artist_name": show[2], "artist_image_link": show[3], "start_time": show[0].strftime("%Y-%m-%dT%H:%M:00.000Z")}
    past_shows.append(show_obj)
  queried_venue.past_shows = past_shows
  queried_venue.past_shows_count = len(past_shows)

  return render_template('pages/show_venue.html', venue=queried_venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion
  form = VenueForm(request.form)
  error = False
  try:
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    genres = form.genres.data
    genre_string = ",".join(genres)
    seeking_talent = form.seeking_talent.data
    seeking_description = form.seeking_description.data
    venue = Venue(name = name, city = city, state = state, address = address, phone = phone, image_link = image_link, 
    facebook_link = facebook_link, website_link = website_link, genres = genre_string, seeking_talent = seeking_talent, seeking_description = seeking_description)
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback() 
    # DONE: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + name + ' could not be listed.')
  finally:
    db.session.close()
  if error:
    return render_template('forms/new_venue.html', form=form)
  else:
    flash('Venue ' + name + ' was successfully listed!')
    return render_template('pages/home.html')



  

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # DONE: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
    flash('An error occurred. Venue could not be deleted.')
  finally:
    db.session.close()
  return render_template('pages/home.html') 

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # DONE: replace with real data returned from querying the database
  artists_data = Artist.query.all()

  return render_template('pages/artists.html', artists=artists_data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  print(request.form.get('search_term'));
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  # get a list of all artists, then pull num shows for each artist.
  data = []
  query_result = Artist.query.filter(Artist.name.ilike('%' + request.form.get('search_term') + '%')).all()
  print(query_result)
  for artist in query_result:
    count = Show.query.filter_by(artist_id=artist.id).count()
    artist_obj = {
      "id" : artist.id,
      "name" : artist.name,
      "num_upcoming_shows" : count
    }
    data.append(artist_obj);
  response={
    "count": len(query_result),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # DONE: replace with real artist data from the artist table, using artist_id
  queried_artist=Artist.query.get(artist_id);
  queried_artist.genres = queried_artist.genres.split(",")

  return render_template('pages/show_artist.html', artist=queried_artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = db.session.query(Artist).filter_by(id=artist_id).one()
  form.state.default = artist.state
  form.genres.default = artist.genres.split(",")
  form.process()

  # DONE: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # DONE: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  form = ArtistForm(request.form)
  try:
    artist = Artist.query.get(artist_id)
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.website_link = form.website_link.data
    artist.genres = ",".join(form.genres.data)
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close() 
  if error:
    flash('An error occurred. Artist ' + form.name.data + ' could not be edited.')
  else:
    flash('Artist ' + form.name.data + ' was successfully edited!')
  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = db.session.query(Venue).filter_by(id=venue_id).one()
  form.state.default = venue.state
  form.genres.default = venue.genres.split(",")
  form.process()

  # DONE: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # DONE: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  form = VenueForm(request.form)
  try:
    venue = Venue.query.get(venue_id)
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.website_link = form.website_link.data
    venue.genres = ",".join(form.genres.data)
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    
  finally:
    db.session.close() 
  if error:
    flash('An error occurred. Venue ' + form.name.data + ' could not be edited.')
  else:
    flash('Venue ' + form.name.data + ' was successfully edited!')
  return redirect(url_for('show_venue', venue_id=venue_id))
  


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)
  error = False
  try:
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    image_link = form.image_link.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    genres = form.genres.data
    genre_string = ",".join(genres)
    seeking_venue = form.seeking_venue.data
    seeking_description = form.seeking_description.data
    artist = Artist(name = name, city = city, state = state, phone = phone, image_link = image_link, facebook_link = facebook_link,
    website_link = website_link, genres = genre_string, seeking_venue = seeking_venue, seeking_description = seeking_description)
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    # DONE: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    flash('An error occurred. Artist ' + name + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Artist ' + name + ' was successfully listed!')
  return render_template('pages/home.html')
  

  
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # DONE: replace with real venues data.
  shows_data = db.session.query(Show.start_time, Artist.id, Artist.name, Artist.image_link, Venue.id, Venue.name).join(Artist, Show.artist_id == Artist.id).join(Venue, Show.venue_id == Venue.id).all()

  return render_template('pages/shows.html', shows=shows_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # DONE: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)
  error = False
  try:
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    # DONE: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  if error:
    return render_template('/forms/new_show.html', form=form)
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
    return render_template('pages/home.html')

  
  

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
