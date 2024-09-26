# Developer How-To

### Tools:
1. Download git
   * https://git-scm.com/download/win
2. Download python v3.11
   * https://www.python.org/downloads/release/python-3119/
3. Download PyCharm Community
   * https://www.jetbrains.com/pycharm/download/?section=windows
4. Install Docker
   
---

### Project Setup:
1. Create a local directory, then initialize the directory to use git
    * `git init`
2. Clone github project into your directory
   * `git clone https://github.com/alexp8/cave-bois-fantasy-backend.git`
3. Setup Pycharm interpreter
   * <img src="how-to-images%2Fpycharm%20interpreter.png" alt="Alt text" width="600" height="450">
4. Right click 'backend' and mark as 'Sources Root'
5. Run server
   * from `backend/` enter `docker-compose up -d`

##### Fresh build
- `docker-compose build --no-cache`
- `docker exec -it fantasy_trades_app /bin/bash`
- `docker logs fantasy_trades_app`
- 
##### Migration Commands
- `python manage.py showmigrations`
- `python manage.py makemigrations`
- `python manage.py migrate`
- `python manage.py shell`

---

#### Tip
   * Disable "Use non-modal commit interface"
   * <img src="how-to-images/git non_modal.png" alt="Alt text" width="500" height="250">