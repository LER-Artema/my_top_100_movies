import os

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired

load_dotenv('/Users/Artema/Desktop/my_envs/my_envs_100_movies.env')

api_key = os.getenv('api_key')
url = 'https://api.themoviedb.org/3/search/movie'
requests.get(url=url, params={'api_key': api_key, 'query': ''})

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', "sqlite:///movies.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)


# formulario de edición de rating
class RatingForm(FlaskForm):
    rating = FloatField(label='Rating', validators=[DataRequired()])
    review = StringField(label='Review', validators=[DataRequired()])
    submit = SubmitField(label="Edit")


# formulario de añadido de título
class AddForm(FlaskForm):
    title = StringField(label='Movie Title', validators=[DataRequired()])
    submit = SubmitField(label="Add")


# tabla de base datos
class Movie(db.Model):
    __tablename__ = 'Movie'

    id = db.Column(db.Integer(), primary_key=True, nullable=False, unique=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer(), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float(), nullable=True)
    ranking = db.Column(db.Integer(), nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=True)

    def __repr__(self):
        return '%s %s %s %s %s %s %s %s' % (
            self.id, self.title, self.year, self.description, self.rating, self.ranking, self.review, self.img_url)


db.create_all()


@app.route("/", methods=['GET', 'POST'])
def home():
    # devuelve una lista de los objetos de la tabla ordenados de menor a mayor
    movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(movies)):
        # Da un ranking en función de su posición en la lista
        movies[i].ranking = len(movies) - i
    db.session.commit()
    return render_template("index.html", movies=movies)


@app.route("/edit/<int:index>", methods=['GET', 'POST'])
def edit(index):
    login_form = RatingForm()
    # process of submitting the entries
    if login_form.validate_on_submit():
        review = login_form.review.data
        rating = login_form.rating.data
        Movie.query.get(index).rating = int(rating)
        Movie.query.get(index).review = review
        db.session.commit()
        return redirect(url_for('home'))
    # render of the edit page
    movie = Movie.query.get(index)
    print(movie)
    return render_template('edit.html', movie=movie, form=login_form)


@app.route("/add", methods=['GET', 'POST'])
def add():
    # direccionamiento al formulario de búsqueda de película
    login_form = AddForm()
    if login_form.validate_on_submit():
        # api request para encontrar resultados
        data = requests.get(url=url, params={'api_key': api_key, 'query': login_form.title.data}).json()
        data = data['results']
        return render_template('select.html', data=data)
    return render_template("add.html", form=login_form)


@app.route("/delete/<int:index>")
def delete(index):
    # DELETE A RECORD BY ID
    movie_to_delete = Movie.query.get(index)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/update")
def update():
    # utiliza el endpoint correspondiente para sacar información detallada sobre la película
    # utiliza el modulo flask request para obtener información mediante la anchor tag en el documento select
    movie_api_id = request.args.get("id")
    data = requests.get(url=f'https://api.themoviedb.org/3/movie/{movie_api_id}', params={'api_key': api_key}).json()
    db.create_all()
    # creación de nuevo registro en el campo de la tabla
    new_movie = Movie(
        title=data['title'],
        year=data['release_date'].split('-')[0],
        description=data['overview'],
        img_url=f"https://image.tmdb.org/t/p/w500/{data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    # obtención del id en la película para pasar el valor como parámetro
    mov_id = Movie.query.filter_by(title=data['title']).first()
    mov_id = mov_id.id
    # redireccionamiento para añadir rating y review a la película
    return redirect(url_for('edit', index=mov_id))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
