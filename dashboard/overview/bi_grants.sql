-- S11A grants already applied only to the new managed BI role.
-- Credential creation uses a generated value from the ignored local file;
-- never put a real password in this template or command history.
GRANT CONNECT ON DATABASE movielens_btl TO movielens_bi_reader;
GRANT USAGE ON SCHEMA dw TO movielens_bi_reader;
GRANT SELECT ON dw.v_ml_ratings,dw.v_ml_movies TO movielens_bi_reader;
-- No base table DML, CREATE, role membership, ownership, or default grants.
-- Existing PUBLIC TEMP is disclosed in the privilege evidence; not changed here.
