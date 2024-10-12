CREATE ROLE repl_user with REPLICATION ENCRYPTED PASSWORD '14852';
SELECT pg_create_physical_replication_slot('replication_slot');
CREATE TABLE hba ( lines text );
COPY hba FROM '/var/lib/postgresql/data/pg_hba.conf';
INSERT INTO hba (lines) VALUES ('host replication all 0.0.0.0/0 md5');
COPY hba TO '/var/lib/postgresql/data/pg_hba.conf';
SELECT pg_reload_conf();
CREATE TABLE IF NOT EXISTS emails (
	id SERIAL PRIMARY KEY,
	email VARCHAR(100) NOT NULL
);
CREATE TABLE IF NOT EXISTS phones (
	id SERIAL PRIMARY KEY,
	phone VARCHAR(25) NOT NULL
);
INSERT INTO emails (email) VALUES ('steamk44@gmail.com');
INSERT INTO phones (phone) VALUES ('89049999999');
