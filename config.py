import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess-h1kqk91ja-2109ak21uaiwk10akkk'