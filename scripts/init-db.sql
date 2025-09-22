-- Database initialization script for The Plugs
-- This script runs when PostgreSQL container starts for the first time

-- Create additional databases for testing
CREATE DATABASE the_plugs_test;
GRANT ALL PRIVILEGES ON DATABASE the_plugs_test TO the_plugs_user;

-- Create extensions
\c the_plugs;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create indexes for better performance (will be managed by Alembic later)
-- These are just examples and will be replaced by proper migrations
-- Set up database configuration
ALTER DATABASE the_plugs SET timezone TO 'UTC';
ALTER DATABASE the_plugs_test SET timezone TO 'UTC';

-- Create read-only user for reporting (optional)
-- CREATE USER the_plugs_readonly WITH PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE the_plugs TO the_plugs_readonly;
-- GRANT USAGE ON SCHEMA public TO the_plugs_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO the_plugs_readonly;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO the_plugs_readonly;


