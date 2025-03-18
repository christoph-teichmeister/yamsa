# Import a DB dump from render

1. Download dump from [here](https://dashboard.render.com/d/dpg-chmhpfqk728oa7bkgdkg-a/recovery)
2. Copy .sql dump into db-container using the following command: `docker cp /path/to/dump/dump.sql yamsa_database:/dump.sql`
3. Inside the db-docker-container run the following command: `psql -f /dump.sql --dbname=yamsa_db --username=yamsa-postgres-user --host=localhost --port=5432`