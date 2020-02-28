import os

DB_CONNECTION = 'mongodb://%s:%s/' % (os.environ['DB_HOST'], os.environ['DB_PORT'])