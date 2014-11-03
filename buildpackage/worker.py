import os

import redis
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']

redis_url = os.getenv('REDISTOGO_URL', 'redis://redistogo:e777ce746dac90d65d926e755bcc1f8f@dab.redistogo.com:9006/')

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()