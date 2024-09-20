Download PGAdmin
- https://www.pgadmin.org/download/

Postgres RDS Creation steps:
- `sudo apt update`
- `sudo apt install postgresql postgresql-contrib`
- `sudo systemctl start postgresql`
- `sudo nano /etc/postgresql/16/main/postgresql.conf`, set `listen_addresses = '*'`

Reload
- `sudo systemctl reload postgresql`
- `sudo systemctl status postgresql`

Create user:
- `sudo -u postgres psql`
- `CREATE USER admin WITH PASSWORD '<password>';`
- `CREATE DATABASE fantasy_trades OWNER admin;`
- `GRANT ALL PRIVILEGES ON DATABASE fantasy_trades TO admin;`
- `psql -h your-cloud-server-ip -U clouduser -d cloud_db`
- 

View log
- `sudo tail -f /var/log/postgresql/postgresql-16-main.log`
