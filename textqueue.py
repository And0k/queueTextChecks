#!/usr/bin/python3

"""
dockers: api(text) -> очередь -> воркеры(worker_status) -> СУБД(text, n_errors)
         api(worker_status) <----/

db:
PostgreSQL

Run it:
su
systemctl start docker
docker-compose -f /home/korzh/Python/PycharmProjects/queueTextChecks/docker-compose.yml up -d

"""

import asyncio
from functools import partial
import datetime
# import aiotarantool_queue
# from aiotarantool_queue.queue import READY
import asynctnt
import asynctnt_queue
import asyncpg
import logging

# my functions
from args import get_cfg
import re_pattern
from utils2init import init_logging

cfg = None # get_cfg(['-T', 'test']) # import defaults for testing
l= None


# Speed up asyncio (https://magic.io/blog/uvloop-blazing-fast-python-networking/)
#import uvloop
#asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def retry_with_delay(fun, msg, fun_timout_s, delay_to_retry_s, n_retries=1):
    """
    Retry to call function with delay if error in function or it is not returns too long
    :param fun:
    :param msg:
    :param fun_timout_s:
    :param delay_to_retry_s: between retries
    :param n_retries:
    :return: what fun returns

    Example:
    retry_with_delay(task.ack,
                     "Error to remove message from queue. Will try later".format(task),
                     cfg['queue_timeout_s'],
                     cfg['queue_delay_to_retry_s'],
                     cfg['queue_n_retries'])
    """
    for n in range(n_retries,-1,-1):
        try:
            return await asyncio.wait_for(fun(), timeout=fun_timout_s)
            # break
        except Exception as e:
            l.warning(msg
                      + " - " + getattr(e, 'message', '') + '\n==> '.join([
                        a for a in e.args if +isinstance(a, str)])
                      + (" - I will try {} times more max".format(n) if n else " - I'm tired to try"))
            if n:
                await asyncio.sleep(delay_to_retry_s)
            else:
                if not __debug__:
                    raise e

def process(text):
    # process text: find errors
    out = re_pattern.r_capital_after_capital_or_not_a_dot.match(text)
    n_errors = len(out)
    return n_errors

# $ docker run --name mytarantool -p3301:3301 -d -v /path/to/my/app:/opt/tarantool \
# tarantool/tarantool:1.8 tarantool /opt/tarantool/app.lua

#################################################################################
# Tarantool


def tarantool_connect():
    """
    Connect to tarantool, change cfg fields
    :return: None
    """
    cfg['queue_IP'] = "127.0.0.1"
    cfg['queue_port'] = 3301

    cfg['queue_conn'] = asynctnt.Connection(
            host=cfg['queue_IP'],
            port=cfg['queue_port'],
        username=cfg['TARANTOOL_USER_NAME'],
        password=cfg['TARANTOOL_USER_PASSWORD'],
            loop=cfg['loop'])
    cfg['loop'].run_until_complete(
        retry_with_delay(
            cfg['queue_conn'].connect,
            "Error connect to {}:{}. Will try later".format(cfg['queue_IP'], cfg['queue_port']),
            cfg['db_timeout_s'],
            cfg['db_delay_to_retry_s'],
            cfg['db_n_retries']))

    cfg['queue'] = asynctnt_queue.Queue(cfg['queue_conn'])
    cfg['tube'] = cfg['queue'].tube(cfg['TARANTOOL_TUBE_NAME'])


async def task_input(text= None):
    """
    1. Interact with user if text is None to get it
    2. Write it to Tarantool queue
    :param cfg:
    :param text:
    :return: None
    """
    try:
        if text is None:
            text = input('Your message >')
        # from aioconsole import ainput
        #
        # async def some_coroutine():
        #     line = await ainput(">>> ")

        # Insert data to queue
        task = retry_with_delay(partial(cfg['tube'].put, {"text": text}),
                         "Error to put message to queue. Will try later",
                         cfg['queue_timeout_s'],
                         cfg['queue_delay_to_retry_s'],
                         cfg['queue_n_retries'])

        l.info("Your message accepted. Its number is " + task.task_id)
        if __debug__:
            await asyncio.wait_for(task_status(cfg['queue'], task.task_id), timeout=cfg['queue_timeout_s'])
    except asyncio.TimeoutError as e:
        l.warning(e)
    except Exception as e:
        l.warning(e)

#################################################################################
# Process Tarantool queue data


async def task_status(task_id):
    try:
        print('search task {}...'.format(task_id))
        # freezes if tarantool not connected
        fu_peek = asyncio.ensure_future(cfg['tube'].peek(task_id))
        task = await asyncio.wait_for(fu_peek, timeout=cfg['queue_timeout_s'])
        print('Task id: {}'.format(task.task_id))
        print('Task status: {}'.format(task.status))
        l.debug('Task status retrieved: {}'.format(task))
    except Exception as e:
        l.warning(e)


async def worker():
    fu_take = asyncio.ensure_future(cfg['tube'].take(.5))
    while True:
        task = retry_with_delay(fu_take,
                         "Error to take message from queue. Will try later",
                         cfg['queue_timeout_s'],
                         cfg['queue_delay_to_retry_s'],
                         cfg['queue_n_retries'])
        #task = await asyncio.wait_for(fu_take, timeout=cfg['queue_timeout_s'])
        if not task:
            break  # no data = nothing to do
        text = task.data['text']
        if not 'n_errors' in task.data:
            n_errors = process(text)

        # move to DB
        try:
            task = retry_with_delay(partial(insert, cfg['db_conn'], text, n_errors),
                                    "Error move message {} to DB. Will try later".format(task.task_id),
                                    cfg['db_timeout_s'],
                                    cfg['db_delay_to_retry_s'],
                                    cfg['db_n_retries'])
        except Exception as e:
            # Return text to queue but with processing result
            task = retry_with_delay(partial(cfg['tube'].put,
                {'text': text, 'n_errors': n_errors, 'Exception':
                    getattr(e, 'message', '') + '\n==> '.join([
                        a for a in e.args if +isinstance(a, str)])}),
                                    "Error put message {} back to queue. Will try later".format(task.task_id),
                                    cfg['queue_timeout_s'],
                                    cfg['queue_delay_to_retry_s'],
                                    cfg['queue_n_retries'])

        retry_with_delay(task.ack,
                         "Error to remove message {} from queue. Will try later".format(task.task_id),
                         cfg['queue_timeout_s'],
                         cfg['queue_delay_to_retry_s'],
                         cfg['queue_n_retries'])


#################################################################################
# DB


def db_connect():
    """
    Connect to existing Postgres DB, change cfg fields
    :return: None
    """
    db_uri = 'postgresql://postgres@localhost/' + cfg['POSTGRES_DB']
    cfg['db_conn'] = cfg['loop'].run_until_complete(
        retry_with_delay(
            partial(
                asyncpg.connect,
                db_uri,
                user=cfg['POSTGRES_USER'], password=cfg['POSTGRES_PASSWORD']),
            "Error connect to {}. Will try later".format(db_uri),
            cfg['db_timeout_s'],
            cfg['db_delay_to_retry_s'],
            cfg['db_n_retries']))

async def insert(conn, text, n_errors):
    """
    Save to Postgres database
    :param conn:
    :param text:
    :param n_errors:
    :return:
    """
    # Insert a record into the existed table.
    asyncio.wait_for( conn.execute(
        'INSERT INTO {POSTGRES_TABLE}(text, n_errors, t_accepted) VALUES($1, $2, $3)'.format_map(cfg),
        text, n_errors, datetime.datetime.now()),
        timeout=cfg['db_timeout_s'])
    """
    INSERT INTO text__n_errors (text, t_accepted) VALUES ('nana-text', '1977-12-20');
    
    id serial PRIMARY KEY,
    text text,
    n_errors integer,
    t_accepted date
    """
    return True

#################################################################################
#################################################################################


def main(arg=None):
    """

    :param arg: returns cfg if arg=='return_cfg' but it will be None if argument passed
    argv[1:] == '-h' or '-v'
    :return:
    """

    global cfg, l
    cfg = get_cfg() #'./instance/.env'
    if not cfg:
        return
    if arg=='return_cfg': # to help testing
        return cfg

    l = init_logging(logging, '.', None, cfg['verbose'])
    l.info('textqueue started')

    t_multiplier = 1
    if __debug__:
        t_multiplier = 1
    cfg['queue_timeout_s'] = 5*t_multiplier
    cfg['queue_delay_to_retry_s'] = 50*t_multiplier
    cfg['queue_n_retries'] = 3

    cfg['db_timeout_s'] = 5*t_multiplier
    cfg['db_delay_to_retry_s'] = 50*t_multiplier
    cfg['db_n_retries'] = 3

    cfg['input_timeout_s'] = 100


    cfg['loop'] = asyncio.get_event_loop()

    # Queue API
    cfg['queue_conn'] = None  # useful for debug
    tarantool_connect()

    cfg['db_conn']= None  # useful for debug
    db_connect()


    text= input('Input one text message [I]/ get status of task on previous message (number)? >')
    if text.isdecimal():
        # Return status of task (number)
        task_id= int(text)
        #t = cfg['loop'].run_until_complete(
        atask = asyncio.wait_for(
            task_status(task_id), timeout = cfg['queue_timeout_s'] )
        asyncio.ensure_future(atask)
    else:
        # Insert data to queue
        text = input('Your message >')
        atask = asyncio.wait_for(task_input(), timeout = cfg['input_timeout_s'])
        asyncio.ensure_future(atask)
    # await asyncio.sleep(delay)
    l.debug('starting loop')
    try:
        cfg['loop'].run_forever()
    finally:
        # Close the connection.
        l.info('exiting...')
        if cfg['queue_conn']:
            cfg['loop'].run_until_complete(asyncio.wait_for(
                cfg['queue_conn'].disconnect(), timeout = cfg['queue_timeout_s']))
        if cfg['db_conn']:
            cfg['loop'].run_until_complete(asyncio.wait_for(
                cfg['db_conn'].close(), timeout = cfg['db_timeout_s']))
        cfg['loop'].run_until_complete(cfg['loop'].shutdown_asyncgens())
        cfg['loop'].close()


if __name__ == '__main__':
    main()


