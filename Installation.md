# Installation

Follow these steps to set up the Online Polls and Surveys Application.

**1. Clone the Repository**

   ```
   git clone https://github.com/niichapats/ku-polls.git
   ```
   
**2. Navigate to the project's directory**
   ```
   cd ku-polls
   ```

**3. Create a virtual environment**
```
python3 -m venv env
```

**4. Activate the virtual environment**
   - On MS Window
   ```commandline
    \env\Scripts\activate
   ```
   - On macOS and Linux
   ```commandline
    source env/bin/activate
   ```
   
**5. Install the required packages**
```commandline
pip install -r requirements.txt
```

**6. Configure Environment Variables**
   * On MS Window use
      ```commandline
       copy sample.env .env
      ```
   * On macOS and Linux use
     ```commandline
      cp sample.env .env
     ```

**7. Run migrations**
```commandline
python3 manage.py migrate
```

**8. Install data from data fixtures**
```commandline
python3 manage.py loaddata data/polls-v4.json data/votes-v4.json data/users.json
```

**9. Run tests**
```commandline
python3 manage.py test
```
