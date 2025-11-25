
from .vault_db import db_manager
from .auth_models import User
from .vault_models import (
    Base,
    Movie,
    Celebrity,
    MovieBrief,
    BestMovies,
    Recommendations,
    HotComment,
    Review,
    Area,
    Type,
    Tag,
    Language,
    movie_director,
    movie_actor,
    movie_scenarist,
    movie_area,
    movie_type,
    movie_tag,
    movie_language,
    celebrity_area
)

from .vault_models import Base

def main():
    Base.metadata.create_all(db_manager.engine)

if __name__ == '__main__':
    raise SystemExit(main())