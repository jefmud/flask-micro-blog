import re
from functools import wraps
from flask import session, redirect, request, url_for

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