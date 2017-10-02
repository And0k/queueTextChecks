# run this after docker-compose up:
# docker-compose run —rm web python instance/db_create.py

import asyncpg
import asyncio
from args import get_cfg
cfg = get_cfg()

# Execute a statement to create a new table.
async def create_tbl():
    # Establish a connection to an existing database
    conn = await asyncpg.connect('postgresql://postgres@localhost/' + cfg['POSTGRES_DB'],
                                 user=cfg['POSTGRES_USER'], password=cfg['POSTGRES_PASSWORD'])

    await conn.execute('''
        CREATE TABLE text__n_errors(
            id serial PRIMARY KEY,
            text text,
            n_errors integer,
            t_accepted timestamp
        );
    ''')


ioloop = asyncio.get_event_loop()
ioloop.run_until_complete(create_tbl())
ioloop.close()

"""
to control
docker exec -it 5a7164db8057 psql text__n_errors -U test -W admin

or run  SQL:
docker cp ./localfile.sql containername:/container/path/file.sql
docker exec containername -u postgresuser psql dbname postgresuser -f /container/path/file.sql

to restore:
docker exec -i app_db_1 psql -U postgres < app_development.back


---- here ----
import docker
client = docker.from_env()

env=   ["POSTGRES_USER=user",
    "POSTGRES_PASSWORD=password123"]
client.containers.run(
    "postgresql",
    environment= env,
    name="postgres",
    ports={"5432/tcp":5432},
    restart_policy={"Name": 'always'}, detach=True)
client.images.get
"""

# Trash #######################################################################

"""
from configparser import ConfigParser
from itertools import chain as itertools_chain
FILE= './instance/.env'
config = ConfigParser()
config.optionxform = str
add_section_header= config.read_file(itertools_chain(['[env_section]'], FILE))

"""