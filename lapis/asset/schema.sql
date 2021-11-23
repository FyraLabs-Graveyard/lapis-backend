-- lapis.buildroots definition

-- Drop table

-- DROP TABLE buildroots;

CREATE TABLE buildroots (
	id serial4 NOT NULL,
	"name" varchar(255) NOT NULL,
	status varchar(255) NOT NULL,
	last_used timestamp NULL,
	last_build int4 NULL,
	CONSTRAINT buildroots_pkey PRIMARY KEY (id)
);


-- lapis.builds definition

-- Drop table

-- DROP TABLE builds;

CREATE TABLE builds (
	id serial4 NOT NULL,
	"name" varchar(255) NOT NULL,
	description varchar(255) NOT NULL,
	"source" varchar(255) NOT NULL,
	status varchar(255) NOT NULL,
	started_at timestamp NOT NULL,
	finished_at timestamp NULL,
	duration int4 NULL,
	"CREATE TABLE IF NOT EXISTS" _bytea NULL,
	CONSTRAINT builds_pkey PRIMARY KEY (id)
);


-- lapis.users definition

-- Drop table

-- DROP TABLE users;

CREATE TABLE users (
	id int4 NOT NULL,
	username varchar(255) NULL,
	"password" varchar(255) NULL,
	email varchar(255) NULL,
	created timestamp NULL,
	last_login timestamp NULL,
	"token" varchar(255) NULL,
	CONSTRAINT users_pkey PRIMARY KEY (id),
	CONSTRAINT users_username_key UNIQUE (username)
);


-- lapis.workers definition

-- Drop table

-- DROP TABLE workers;

CREATE TABLE workers (
	id int4 NOT NULL,
	"name" varchar(255) NOT NULL,
	"type" varchar(255) NOT NULL,
	status varchar(255) NOT NULL,
	last_seen timestamp NULL,
	last_task int4 NULL,
	"token" varchar(255) NOT NULL,
	CONSTRAINT workers_pkey PRIMARY KEY (id)
);


-- lapis.sessions definition

-- Drop table

-- DROP TABLE sessions;

CREATE TABLE sessions (
	id serial4 NOT NULL,
	user_id int4 NULL,
	"token" varchar(255) NULL,
	created timestamp NULL,
	CONSTRAINT sessions_pkey PRIMARY KEY (id),
	CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)
);


-- lapis.tasks definition

-- Drop table

-- DROP TABLE tasks;

CREATE TABLE tasks (
	id int4 NOT NULL,
	"type" varchar(255) NOT NULL,
	build_id int4 NOT NULL,
	status varchar(255) NOT NULL,
	worker_id int4 NULL,
	payload jsonb NOT NULL,
	"CREATE TABLE IF NOT EXISTS" _bytea NULL,
	CONSTRAINT tasks_pkey PRIMARY KEY (id),
	CONSTRAINT tasks_build_id_fkey FOREIGN KEY (build_id) REFERENCES builds(id),
	CONSTRAINT tasks_worker_id_fkey FOREIGN KEY (worker_id) REFERENCES workers(id)
);