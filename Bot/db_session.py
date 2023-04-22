import sqlalchemy
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

SqlAlchemyBase = orm.declarative_base()

__factory = None


class Image(SqlAlchemyBase):
    __tablename__ = 'images'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    key_word = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    link = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    rating = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)


def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")

    engine = sqlalchemy.create_engine(conn_str, echo=False)
    print(engine)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()


def main():
    global_init("../data/riddles.db")
    session = create_session()
    image = Image(key_word='дота', link='../data/images/deathgun.png', rating='100')
    session.add(image)
    image = Image(key_word='1', link='https://i.pinimg.com/originals/42/67/3e/42673e608003f60330c9cb36c1f7ff90.jpg', rating='90')
    session.add(image)
    image = Image(key_word='2', link='../data/images/2.png', rating='2')
    session.add(image)
    image = Image(key_word='3', link='../data/images/3.png', rating='3')
    session.add(image)
    session.commit()


if __name__ == '__main__':
    main()
