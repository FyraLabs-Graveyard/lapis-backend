#Database code for Lapis
import lapis.config as config
import lapis.logger
import lapis.util as util
import psycopg2
import time
import datetime
import json
import os
import secrets

# load schema from SQL file in assets/
def lapis_schema():
    with open(os.path.join(os.path.dirname(__file__), "asset/schema.sql"), "r") as f:
        return f.read()
# copilot commenting intensifies
# ================================
# set up the database
# if the database doesn't exist, create it
# if the database mode is set to local, use the socket
# if the database mode is set to remote, use the host and port
# use config.get('') to get the value of a key
# use config.set('') to set the value of a key
# get the database connection

def connection():
    try:
        if config.get('database_mode') == 'local':
            # use socket
            conn = psycopg2.connect(database=config.get('database'), user=config.get('database_user'), password=config.get('database_password'))
        else:
            conn = psycopg2.connect(database=config.get('database'), user=config.get('database_user'),
                                    password=config.get('database_password'),
                                    sslmode=config.get('database_ssl'), sslkey=config.get('database_ssl_key'),
                                    sslcert=config.get('database_ssl_cert'))
    except Exception as e:
        # error and return null if there's a problem
        print(e)
    finally:
        # now check if the schema exists
        # if it doesn't, create it from the schema file
        # if it does, check if the schema is up to date
        # if it isn't, update it
        # create a schema called lapis if it doesn't exist
        try:
            cursor = conn.cursor()
            lapis.logger.debug(cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)", ["task"]))
            if cursor.fetchone()[0] == 0:
                # schema doesn't exist
                cursor.execute(lapis_schema())
            else:
                # schema exists
                cursor.execute("SELECT version FROM version")
                if cursor.fetchone()[0] == "1.0.0":
                    # schema is up to date
                    pass
                else:
                    # schema is out of date
                    cursor.execute(lapis_schema())
        except Exception as e:
            # error and return null if there's a problem
            lapis.logger.error(e)
            return None
        finally:
            return conn

# now get the schema in the database
# if there's nothing there, create the schema
# if there's something there, check to see if it's the same as the schema in the code
# if it's different, update the schema
# if it's the same, do nothing
# this is to prevent schema changes from breaking the database

def initialize():
    conn = connection()
    if conn is not None:
        print("Initializing database..")
        cursor = conn.cursor()
        cursor.execute(lapis_schema())
        conn.commit()
        conn.close()
# ================================
# database functions
# ================================

# list the current builds, with an optional amount of builds to list
# if no amount is specified, list all the builds
# if an amount is specified, list the most recent builds
class build:
    # Insert build into the database
    def insert(build: json):
        if config.get('debug') == True:
            lapis.logger.debug("Inserting build into database")
            lapis.logger.debug(build)
        try:
            conn = connection()
            cur = conn.cursor()
            build["output"] = json.dumps(build["output"])
            cur.execute("INSERT INTO builds (id,name,description,source,status,started_at,finished_at,duration,output) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (build["id"],
                         build["name"],
                         build["description"],
                         build["source"],
                         build["status"],
                         build["started_at"],
                         build["finished_at"],
                         build["duration"],
                         build["output"]))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            lapis.logger.error("Error inserting build into database: " + str(e))
    
    def remove(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM builds WHERE id=%s", (id,))
        conn.commit()
        cur.close()
        conn.close()
    
    def list(amount=None):
        conn = connection()
        cur = conn.cursor()
        if amount is None:
            cur.execute("SELECT * FROM builds")
        else:
            cur.execute("SELECT * FROM builds ORDER BY id DESC LIMIT %s", (amount,))
        builds = cur.fetchall()
        conn.close()
        return builds

    def get(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM builds WHERE id=%s", (id,))
        build = cur.fetchone()
        conn.close()
        return build

    def update(id, build):
        conn = connection()
        cur = conn.cursor()
        build["output"] = json.dumps(build["output"])
        # only update the fields that are specified
        cur.execute("UPDATE builds SET name=%s, description=%s, source=%s, status=%s, started_at=%s, finished_at=%s, duration=%s, output=%s WHERE id=%s",
                    (build["name"],
                     build["description"],
                     build["source"],
                     build["status"],
                     build["started_at"],
                     build["finished_at"],
                     build["duration"],
                     build["output"],
                     id))
        conn.commit()
        cur.close()
        conn.close()

    def status(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM builds WHERE id=%s", (id,))
        status = cur.fetchone()
        conn.close()
        return status[0]


class tasks:
    def insert(task):
        try:
            conn = connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO tasks (id,type,build_id,status,payload) VALUES (%s,%s,%s,%s,%s)",
                        (task["id"],
                         task["type"],
                         task["build_id"],
                         task["status"],
                         json.dumps(task["payload"])))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            lapis.logger.error("Error inserting task into database: " + str(e))

    def remove(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id=%s", (id,))
        conn.commit()
        cur.close()
        conn.close()

    def list(type="pending"):
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE status=%s", (type,))
        tasks = cur.fetchall()
        conn.close()
        # return tasks as an array of dictionaries
        return tasks

    def get(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id=%s", (id,))
        task = cur.fetchone()
        conn.close()
        return task

    def take(worker_id,id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("UPDATE tasks SET status='running' WHERE id=%s", (id,))
        # assign task to the worker that took it
        cur.execute("UPDATE tasks SET worker_id=%s WHERE id=%s", (lapis.worker.id, id))
        conn.commit()
        cur.close()
        conn.close()

    def update(id, task):
        conn = connection()
        cur = conn.cursor()
        # only update the fields that are specified
        cur.execute("UPDATE tasks SET status=%s, payload=%s WHERE id=%s",
                    (task["status"],
                     json.dumps(task["payload"]),
                     id))
        conn.commit()
        cur.close()
        conn.close()

class workers:
    # Workers should update their last seen time (ping the server) every now and then
    def ping(token):
        conn = connection()
        cur = conn.cursor()
        cur.execute("UPDATE workers SET last_seen=NOW() WHERE token=%s", (token,))
        conn.commit()
        cur.close()
        conn.close()

    def insert(worker):
        lapis.logger.debug
        try:
            conn = connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO workers (id,name,type,status,token) VALUES (%s,%s,%s,%s,%s)",
                        (worker["id"],
                         worker["name"],
                         worker["type"],
                         worker["status"],
                         worker["token"]))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            lapis.logger.error("Error inserting worker into database: " + str(e))

    def remove(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM workers WHERE id=%s", (id,))
        conn.commit()
        cur.close()
        conn.close()

    def list():
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM workers")
        workers = cur.fetchall()
        conn.close()
        return workers

    def get(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM workers WHERE id=%s", (id,))
        worker = cur.fetchone()
        conn.close()
        return worker

    # Chekov's gun, it's a surprise tool that'll help us later.
    def get_by_token(token):
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM workers WHERE token=%s", (token,))
        worker = cur.fetchone()
        conn.close()
        return worker
    
    def update(id, worker):
        conn = connection()
        cur = conn.cursor()
        # only update the fields that are specified
        cur.execute("UPDATE workers SET name=%s, type=%s, status=%s, token=%s WHERE id=%s",
                    (worker["name"],
                     worker["type"],
                     worker["status"],
                     worker["token"],
                     id))
        conn.commit()
        cur.close()
        conn.close()


class user:
    def insert(user):
        try:
            conn = connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (id,name,email,password) VALUES (%s,%s,%s,%s)",
                        (user["id"],
                         user["name"],
                         user["email"],
                         user["password"]))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            lapis.logger.error("Error inserting user into database: " + str(e))

    def remove(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id=%s", (id,))
        conn.commit()
        cur.close()
        conn.close()

    def list():
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        conn.close()
        return users

    def get(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=%s", (id,))
        user = cur.fetchone()
        conn.close()
        return user

    def update(id, user):
        conn = connection()
        cur = conn.cursor()
        # only update the fields that are specified
        cur.execute("UPDATE users SET name=%s, email=%s, password=%s WHERE id=%s",
                    (user["name"],
                     user["email"],
                     user["password"],
                     id))
        conn.commit()
        cur.close()
        conn.close()

class buildroot:
    def insert(buildroot):
        try:
            conn = connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO buildroots (id,name,type,status) VALUES (%s,%s,%s,%s)",
                        (buildroot["id"],
                         buildroot["name"],
                         buildroot["type"],
                         buildroot["status"]))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            lapis.logger.error("Error inserting buildroot into database: " + str(e))

    def remove(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM buildroots WHERE id=%s", (id,))
        conn.commit()
        cur.close()
        conn.close()

    def list():
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM buildroots")
        buildroots = cur.fetchall()
        conn.close()
        return buildroots

    def get(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM buildroots WHERE id=%s", (id,))
        buildroot = cur.fetchone()
        conn.close()
        return buildroot

    def update(id, buildroot):
        conn = connection()
        cur = conn.cursor()
        # only update the fields that are specified
        cur.execute("UPDATE buildroots SET name=%s, type=%s, status=%s WHERE id=%s",
                    (buildroot["name"],
                     buildroot["type"],
                     buildroot["status"],
                     id))
        conn.commit()
        cur.close()
        conn.close()

class sessions:
    def add(session):
        conn = connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO sessions (id,user_id,token,created) VALUES (%s,%s,%s,%s)",
                    (session["id"],
                     session["user_id"],
                     session["token"],
                     session["created"]))
        conn.commit()
        cur.close()
        conn.close()
    # Kick the user out of the session by UID
    def kick(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM sessions WHERE user_id=%s", (id,))
        conn.commit()
        cur.close()
        conn.close()
    # list sessions by UID
    def list(id):
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sessions WHERE user_id=%s", (id,))
        sessions = cur.fetchall()
        conn.close()
        return sessions
    # list all sessions
    def list_all():
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sessions")
        sessions = cur.fetchall()
        conn.close()
        return sessions
    # get session by token
    def get(token):
        conn = connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sessions WHERE token=%s", (token,))
        session = cur.fetchone()
        conn.close()
        return session