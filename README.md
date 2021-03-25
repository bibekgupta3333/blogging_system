# Blogging System(BlogPost) 

## How to run system (local development setup)

- Firstof all download python and version must be greater than 3.9
- download project from git. 
  ``` 
  git clone https://github.com/bibekgupta3333/blogging_system
  ```
- Then install poetry in main project area.
  ``` 
  pip install poetry 
  ```
- Install all packages from poetry lock file in main project area.
  ``` 
  poetry shell
  poetry install
  ```
- Then go into project area where there is manage.py. 
  ``` 
  cd blogging_system
  python manage.py runserver 
  ```
- Then open in browser.
  ``` 
  localhost:8000 
  ```
