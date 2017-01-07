import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Playlist(Base):
    __tablename__ = 'playlist'
	
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
			'id': self.id,
            'name': self.name,
            
        }


class PlaylistSong(Base):
    __tablename__ = 'playlist_song'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    artist = Column(String(250))
    time = Column(String(8))
    genre = Column(String(250))
    playlist_id = Column(Integer, ForeignKey('playlist.id'))
    playlist = relationship(Playlist)
    user_id = Column(Integer, ForeignKey('user.id'))
	
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'artist': self.artist,
            'id': self.id,
            'time': self.time,
            'genre': self.genre,
        }


engine = create_engine('sqlite:///musicplaylist.db')


Base.metadata.create_all(engine)
