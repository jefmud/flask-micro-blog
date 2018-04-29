# flask-micro-blog
A flask blog with TinyMongo back end.  A naive blog using Flask and TinyMongo and some other tasty bits.

# Intent

Intent: Create a micro-blogging system that utilizes the following concepts/tools

__Flask__ – Armin Ronacher’s Flask Framework, it’s simply the best if you want to build it yourself
and have a great amount of control over what’s going on.

__Jinja2__ – Armin Ronacher’s templating engine (default to Flask)

Armin Ronacher - there's always something new coming out of his site that is worthwhile

https://github.com/mitsuhiko

__Bootstrap 4__ – The premier CSS and javascript framework for producing consistent and fast web-UI. 
I would also like to include Bulma at some point too, because it is simpler and pure CSS.

Seems like it would be fun to experiment with Mongo.  I find myself coming into  a certain class of projects
that would be be described in a document object fashion.  And it's always fun to learn something new.

The Biology and Neuroscience crowd doesn't always have projects/data which fit into nice table-oriented schemas best handled
by RDBMS SQL definition.  There's always this... "Oh, by the way, we want to ask a different question can you tack these extra columns onto
this table..."

I am going to use __TinyMongo__ as it is close enough to PyMongo implementation in case someone wants to take
the blog/CMS to the next level.  Also… I can implement Flask-admin as a quick/raw administrative interface.

https://github.com/schapman1974/tinymongo

__Flask-WTF__ – the slightly "Baroque" but overall excellent form package.
I think my concept of using dict2Form which works quite well, would be pretty strange looking to someone not accustomed
to such a concept.

https://github.com/mehmetkose/dict2form

My hacks (to make the forms pretty and flexible for Bulma and Bootstrap) to Mehmet Kose code might make him unhappy.

__Flask-ckEditor__ – I have written my own macros for this in the past, but I am interested to see what this brings to the table.  This integrates 
