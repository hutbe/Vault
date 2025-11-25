from datetime import datetime
from sqlalchemy import Column, Integer, BIGINT, String, Text, Numeric, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship
from typing import Dict, Any

Base = declarative_base()

# Association tables for many-to-many relationships
movie_director = Table('movie_director', Base.metadata,
                       Column('movie_id', Integer, ForeignKey('movie.id')),
                       Column('director_id', Integer, ForeignKey('celebrity.id'))
                       )

movie_actor = Table('movie_actor', Base.metadata,
                    Column('movie_id', Integer, ForeignKey('movie.id')),
                    Column('actor_id', Integer, ForeignKey('celebrity.id'))
                    )

movie_scenarist = Table('movie_scenarist', Base.metadata,
                        Column('movie_id', Integer, ForeignKey('movie.id')),
                        Column('scenarist_id', Integer, ForeignKey('celebrity.id'))
                        )

movie_area = Table('movie_area', Base.metadata,
                   Column('movie_id', Integer, ForeignKey('movie.id')),
                   Column('area_id', Integer, ForeignKey('area.id'))
                   )

movie_type = Table('movie_type', Base.metadata,
                   Column('movie_id', Integer, ForeignKey('movie.id')),
                   Column('type_id', Integer, ForeignKey('type.id'))
                   )

movie_tag = Table('movie_tag', Base.metadata,
                  Column('movie_id', Integer, ForeignKey('movie.id')),
                  Column('tag_id', Integer, ForeignKey('tag.id'))
                  )

movie_language = Table('movie_language', Base.metadata,
                       Column('movie_id', Integer, ForeignKey('movie.id')),
                       Column('language_id', Integer, ForeignKey('language.id'))
                       )

celebrity_area = Table('celebrity_area', Base.metadata,
                       Column('celebrity_id', Integer, ForeignKey('celebrity.id')),
                       Column('area_id', Integer, ForeignKey('area.id'))
                       )


class Movie(Base):
    __tablename__ = 'movie'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    directors = Column(String(255))
    scenarists = Column(String(500))
    actors = Column(String(255))
    style = Column(String(255))
    year = Column(Integer)
    release_date = Column(String(200))
    area = Column(String(255))
    language = Column(String(255))
    length = Column(Integer)
    other_names = Column(String(255))
    score = Column(Numeric(3, 1))
    rating_number = Column(Numeric(10, 0))
    synopsis = Column(Text)
    imdb = Column(String(20))
    poster_name = Column(String(120))
    filePath = Column(String(255))
    fileUrl = Column(String(255))
    is_downloaded = Column(Boolean, default=False)
    download_link = Column(String(250))
    create_date = Column(DateTime, default=datetime.now)
    lastWatch_date = Column(DateTime)
    lastWatch_user = Column(String(40))

    # Relationships
    director_list = relationship('Celebrity', secondary=movie_director, backref='directed_movies')
    actor_list = relationship('Celebrity', secondary=movie_actor, backref='acted_movies')
    scenarist_list = relationship('Celebrity', secondary=movie_scenarist, backref='written_movies')
    area_list = relationship('Area', secondary=movie_area, backref='movies')
    type_list = relationship('Type', secondary=movie_type, backref='movies')
    tag_list = relationship('Tag', secondary=movie_tag, backref='movies')
    language_list = relationship('Language', secondary=movie_language, backref='movies')
    hot_comments = relationship('HotComment', backref='movie')
    reviews = relationship('Review', backref='movie')
    recommendations = relationship('Recommendations', foreign_keys='Recommendations.reference_movie_id',
                                   backref='reference_movie')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'directors': self.directors,
            'scenarists': self.scenarists,
            'actors': self.actors,
            'style': self.style,
            'year': self.year,
            'release_date': self.release_date,
            'area': self.area,
            'language': self.language,
            'length': self.length,
            'other_names': self.other_names,
            'score': float(self.score) if self.score else None,
            'rating_number': float(self.rating_number) if self.rating_number else None,
            'synopsis': self.synopsis,
            'imdb': self.imdb,
            'poster_name': self.poster_name,
            'filePath': self.filePath,
            'fileUrl': self.fileUrl,
            'is_downloaded': self.is_downloaded,
            'download_link': self.download_link,
            'create_date': self.create_date.isoformat() if self.create_date else None,
            'lastWatch_date': self.lastWatch_date.isoformat() if self.lastWatch_date else None,
            'lastWatch_user': self.lastWatch_user
        }


class Celebrity(Base):
    __tablename__ = 'celebrity'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    gender = Column(String(10))
    zodiac = Column(String(10))
    living_time = Column(String(100))
    birthday = Column(BIGINT)
    left_day = Column(BIGINT)
    birthplace = Column(String(255))
    occupation = Column(String(255))
    is_director = Column(Boolean, default=False)
    is_scenarist = Column(Boolean, default=False)
    is_actor = Column(Boolean, default=False)
    names_cn = Column(String(255))
    names_en = Column(String(255))
    family = Column(String(500))
    imdb = Column(String(20))
    intro = Column(Text)
    portrait_name = Column(String(120))
    create_date = Column(DateTime, default=datetime.now)

    # Relationships
    area_list = relationship('Area', secondary=celebrity_area, backref='celebrities')
    best_movies = relationship('BestMovies', backref='celebrity')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'zodiac': self.zodiac,
            'living_time': self.living_time,
            'birthday': self.birthday,
            'left_day': self.left_day,
            'birthplace': self.birthplace,
            'occupation': self.occupation,
            'is_director': self.is_director,
            'is_scenarist': self.is_scenarist,
            'is_actor': self.is_actor,
            'names_cn': self.names_cn,
            'names_en': self.names_en,
            'family': self.family,
            'imdb': self.imdb,
            'intro': self.intro,
            'portrait_name': self.portrait_name,
            'create_date': self.create_date.isoformat() if self.create_date else None
        }


class MovieBrief(Base):
    __tablename__ = 'movie_brief'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    score = Column(Numeric(3, 1))
    year = Column(Integer)
    poster_name = Column(String(120))

    # Relationships
    best_movies = relationship('BestMovies', backref='movie_brief')
    recommendations = relationship('Recommendations', backref='movie_brief')

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'score': float(self.score) if self.score else None,
            'year': self.year,
            'poster_name': self.poster_name
        }


class BestMovies(Base):
    __tablename__ = 'best_movies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    celebrity_id = Column(Integer, ForeignKey('celebrity.id'))
    movie_brief_id = Column(Integer, ForeignKey('movie_brief.id'))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'celebrity_id': self.celebrity_id,
            'movie_brief_id': self.movie_brief_id
        }


class Recommendations(Base):
    __tablename__ = 'recommendations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    reference_movie_id = Column(Integer, ForeignKey('movie.id'))
    movie_brief_id = Column(Integer, ForeignKey('movie_brief.id'))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'reference_movie_id': self.reference_movie_id,
            'movie_brief_id': self.movie_brief_id
        }


class HotComment(Base):
    __tablename__ = 'hot_comment'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    movie_id = Column(Integer, ForeignKey('movie.id'))
    content = Column(Text)
    reviewer_name = Column(String(255))
    reviewer_id = Column(String(20))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'movie_id': self.movie_id,
            'content': self.content,
            'reviewer_name': self.reviewer_name,
            'reviewer_id': self.reviewer_id
        }


class Review(Base):
    __tablename__ = 'review'

    id = Column(Integer, primary_key=True, autoincrement=True)
    movie_id = Column(Integer, ForeignKey('movie.id'))
    title = Column(String(255))
    content_short = Column(Text)
    content = Column(Text)
    reviewer_name = Column(String(255))
    reviewer_id = Column(String(20))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'movie_id': self.movie_id,
            'title': self.title,
            'content_short': self.content_short,
            'content': self.content,
            'reviewer_name': self.reviewer_name,
            'reviewer_id': self.reviewer_id
        }


class Area(Base):
    __tablename__ = 'area'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name
        }


class Type(Base):
    __tablename__ = 'type'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name
        }


class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name
        }


class Language(Base):
    __tablename__ = 'language'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30), nullable=False, unique=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name
        }


def main():
    from sqlalchemy import create_engine
    # Create engine for MariaDB
    engine = create_engine('mysql+pymysql://hut:hut123456@127.0.0.1:3306/vault_db')

    # Create all tables
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    raise SystemExit(main())

