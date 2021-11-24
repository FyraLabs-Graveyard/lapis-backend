-- everything here will be in the public schema


CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    password VARCHAR(255),
    email VARCHAR(255) NOT NULL,
    created TIMESTAMP,
    last_login TIMESTAMP,
    token VARCHAR(255) NOT NULL,
    -- permission field is optional _char
    permissions char[] DEFAULT '{}'::char[]
);
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    token VARCHAR(255),
    created TIMESTAMP,
    -- link to user
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS builds (
    -- build id is an integer that increments by 1 for each build
    -- name is the name of the package
    -- description is a short description of the package
    -- source is the source file or link used to start the build
    -- status is the status of the build (pending, running, success, failure)
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL,
    source VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    duration INT,
    -- output is a json object that contains the output of the build, containing files, logs, etc
    output jsonb
);
CREATE TABLE IF NOT EXISTS tasks (
    -- available tasks for the workers, it's a battle royale between the workers for who gets to do what
    -- id can be any integer, but it should be unique
    id INTEGER PRIMARY KEY,
    -- type can have the following values:
    --   mock: a task for the mock RPM builder
    --   image: image building task, heavier than mock
    --   repo: a task for createrepo
    --   mock-chain: a mock chain build task. builds the RPMs in a chain, designed for packages that depend on
    type VARCHAR(255) NOT NULL,
    -- build_id is the id of the build that this task is for
    build_id INTEGER NOT NULL,
    FOREIGN KEY (build_id) REFERENCES builds(id),
    -- status can have the following values:
    --   pending: the task is waiting to be picked up by a worker
    --   running: the task is currently being processed by a worker
    --   success: the task was successfully completed
    --   failure: the task failed
    status VARCHAR(255) NOT NULL,
    worker_id INTEGER,
    --payload is a json object that contains the payload of the task, containing files, logs, etc
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS workers (
    -- id is similar to user id
    id INTEGER PRIMARY KEY,
    -- name is the name of the worker
    name VARCHAR(255) NOT NULL,
    -- type can be an array of the tasks it can do
    type VARCHAR(255) NOT NULL,
    --FOREIGN KEY (type) REFERENCES tasks(type),
    -- status can have the following values:
    --   idle: the worker is idle and waiting for a task
    --   busy: the worker is busy and working on a task
    --   offline: the worker is offline and not available for tasks
    status VARCHAR(255) NOT NULL,
    -- last_seen is the last time the worker was seen
    last_seen TIMESTAMP,
    -- last_task is the last task the worker was working on
    last_task INTEGER,
    -- Token: a unique token that is used to authenticate the worker
    token VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS buildroots (
    -- id is a unique integer for each buildroot
    id SERIAL PRIMARY KEY,
    -- name is the name of the buildroot
    name VARCHAR(255) NOT NULL,
    -- status can have the following values:
    --   ready: the buildroot is ready to be used
    --   building: the buildroot is currently building
    --   offline: the buildroot is offline and not available for builds
    status VARCHAR(255) NOT NULL,
    -- last_used is the last time the buildroot was used
    last_used TIMESTAMP,
    -- last_build is the last build that was built on the buildroot
    last_build INTEGER
);
