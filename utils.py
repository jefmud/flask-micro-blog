import re
from functools import wraps
from flask import session, redirect, request, url_for
from html.parser import HTMLParser
import random, string

def slugify(s):
    """
    Simplifies ugly strings into something URL-friendly.
    >>> print slugify("[Some] _ Article's Title--")
    some-articles-title
    CREDIT - Dolph Mathews (http://blog.dolphm.com/slugify-a-string-in-python/)

    My modification, allow slashes as pseudo directory.
    slug=/people/dirk-gently => people/dirk-gently
    """

    # "[Some] _ Article's Title--"
    # "[some] _ article's title--"
    s = s.lower()

    # "[some] _ article's_title--"
    # "[some]___article's_title__"
    for c in [' ', '-', '.']:
        s = s.replace(c, '_')

    # "[some]___article's_title__"
    # "some___articles_title__"
    #s = re.sub('\W', '', s)
    s = re.sub('[^a-zA-Z0-9_/]','',s)

    # multiple slashew replaced with single slash
    s = re.sub('[/]+', '/', s)

    # remove leading slash
    s = re.sub('^/','', s)

    # remove trailing slash
    s = re.sub('/$','', s)

    # "some___articles_title__"
    # "some   articles title  "
    s = s.replace('_', ' ')

    # "some   articles title  "
    # "some articles title "
    s = re.sub('\s+', ' ', s)

    # "some articles title "
    # "some articles title"
    s = s.strip()

    # "some articles title"
    # "some-articles-title"
    s = s.replace(' ', '-')

    # a local addition, protects against someone trying to mess with slugless url
    s = re.sub('^page/','page-',s)

    return s

def form2object(form, obj):
    """copy field data from form to an object -- return the object"""
    for field in form:
        obj[field.name] = field.data
    return obj

def object2form(obj, form):
    """copy object data to the form fields -- return the form)"""
    for field in form:
        field.data = obj.get(field.name)
    return form

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not(session.get('is_authenticated')):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not(session.get('is_admin')):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def password_generator(size=8, chars=string.ascii_letters + string.digits):
    """
    Returns a string of random characters, useful in generating temporary
    passwords for automated password resets.
    
    size: default=8; override to provide smaller/larger passwords
    chars: default=A-Za-z0-9; override to provide more/less diversity
    
    Credit: Ignacio Vasquez-Abrams
    Source: http://stackoverflow.com/a/2257449
    """
    return ''.join(random.choice(chars) for i in range(size))