from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Playlist, Base, PlaylistSong, User

engine = create_engine('sqlite:///musicplaylist.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Uplifting happy go luck music playlist
playlist1 = Playlist(name="Uplifting songs", user_id=1,)

session.add(playlist1)
session.commit()

playlistSong1 = PlaylistSong(name="Rise up", artist="Andra Day",
                     time="$4.13", genre="pop", playlist=playlist1)

session.add(playlistSong1)
session.commit()


playlistSong2 = PlaylistSong(name="Stronger", artist="Kelly Clarkson",
                     time="3.50", genre="pop", playlist=playlist1)

session.add(playlistSong2)
session.commit()

playlistSong3 = PlaylistSong(name="ain't no mountain high enough", artist="Marvin Gaye and tammi terrell",
                     time="2.50", genre="RnB", playlist=playlist1)

session.add(playlistSong3)
session.commit()

playlistSong4 = PlaylistSong(name="Your love keeps lifting me higher", artist="jackie wilson",
                     time="$2.57", genre="RnB", playlist=playlist1)

session.add(playlistSong4)
session.commit()

playlistSong5 = PlaylistSong(name="Roar", artist="Katy Perry",
                     time="$4.10", genre="Pop", playlist=playlist1)

session.add(playlistSong5)
session.commit()

playlistSong6 = PlaylistSong(name="Happy", artist="Pharrell",
                     time="$1.99", genre="Pop", playlist=playlist1)

session.add(playlistSong6)
session.commit()

# Romantic music playlist
playlist2 = Playlist(name="Romantic music")

session.add(playlist2)
session.commit()

playlistSong1 = PlaylistSong(name="Won't go home without you", artist="Maroon 5",
                     time="3.50", genre="pop", playlist=playlist2)

session.add(playlistSong1)
session.commit()


playlistSong2 = PlaylistSong(name="Stronger", artist="Kelly Clarkson",
                     time="3.50", genre="pop", playlist=playlist2)

session.add(playlistSong2)
session.commit()

playlistSong3 = PlaylistSong(name="My heart will go on", artist="Celine Dion",
                     time="3.40", genre="pop", playlist=playlist2)

session.add(playlistSong3)
session.commit()

playlistSong4 = PlaylistSong(name="I will always love you", artist="Whitney Houston",
                     time="2.57", genre="RnB", playlist=playlist2)

session.add(playlistSong4)
session.commit()

# angry workout playlist
playlist3 = Playlist(name="Angry Workout")

session.add(playlist2)
session.commit()

playlistSong1 = PlaylistSong(name="real n***** roll call", artist="Lil Jon and Ice cube",
                     time="4.25", genre="rap", playlist=playlist3)

session.add(playlistSong1)
session.commit()


playlistSong2 = PlaylistSong(name="Voices", artist="Rev theory",
                     time="3.50", genre="rock", playlist=playlist3)

session.add(playlistSong2)
session.commit()

playlistSong3 = PlaylistSong(name="Party boyz", artist="Shop Boyz",
                     time="3.35", genre="rap", playlist=playlist3)

session.add(playlistSong3)
session.commit()

playlistSong4 = PlaylistSong(name="No love", artist="Eminem",
                     time="4.30", genre="rap", playlist=playlist3)

session.add(playlistSong4)
session.commit()

# dance songs
playlist4 = Playlist(name="Dance songs")

session.add(playlist4)
session.commit()

playlistSong1 = PlaylistSong(name="rock your body", artist="Justin Timberlake",
                     time="4.25", genre="pop", playlist=playlist4)

session.add(playlistSong1)
session.commit()

playlistSong2 = PlaylistSong(name="All about that bass", artist="Megan Trainor",
                     time="4.25", genre="pop", playlist=playlist4)
					 
session.add(playlistSong2)
session.commit()

print "added new song to playlist"
