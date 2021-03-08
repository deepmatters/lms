# Deep Matters LMS

Deep Matters LMS is a minimal Learning Management System written in Python using Flask framework. The databases are PostgreSQL and MongoDB. The interface is mostly presented in Thai language.

## Key features

- Authors can use the front-end to create/edit/delete courses, learning modules, and tests with answer keys and feedback for incorrect answers. Author can also access a list of enrolled learners.
- Learners can enroll and proceed to each module until completion. A module starts with a content page (primarily presented by a Youtube embedded video) then follows by a multiple-choice test.
- Once a learner passed the last module, one can request for a certificate to be issued. The certificate will contain name and other information specified during the customisation of code.
- Adaptive design. Good for mobile devices!

## How to customise and deploy

- Clone the repository.
- Manually create `app/static/cert` directory because it's excluded in .gitignore as to prevent publishing cert images in Github. This directory is used to store cert images.
- Manually create and configure `config.py` with your own credentials: `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI` (Postgres), `DB_CERT_URI` (MongoDB), and various SMTP email configuration for password recovery sub-system.  Put it in the root (same directory as `lms.py`).
- Customise `route.py` to your need. Pay attention to CAPITAL-LETTER PARAGRAPHS IN DOCSTRING. They will mostly need configuration. This is a chance to customise static content such as `home` and `about` view as well. Also cutomise AWS S3 URL in `cert-issue.html`.
- Develop, upload, and customise a certificate template for each course. Please refer to `cert_issued` function in `route.py`. Need to configure image drawing location which might need some trial-and-error before getting the right position.
- Deploy on your own server. We suggest creating a Python virtual environment (venv) and install needed packages using `pip install -r requirements.txt` in an activated virtual environment. Then configure `gunicorn` instance and `nginx` configuration.
- Setup the database by 1) migrating the postgres database using instruction in `models.py` 2) Setup a MongoDB database and collection with coresponding information in `config.py` and various locations in `route.py`.
- Sign up the first user, then in Postgres, manually set the `role` column for this user as `author` to assign this user as a course author.
- Use an `author` user to create courses, modules, and tests.
- That's it!

## Example of config.py

```
class Config(object):
    SECRET_KEY = 'mysecretkey'
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://my_postgres_uri:port/dbname'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_CERT_URI = 'mongodb+srv://my_mongodb_uri'
    MAIL_SERVER = 'my_smtp_server'
    MAIL_PORT = 587
    MAIL_USERNAME = 'my_smtp_mail_username'
    MAIL_PASSWORD = 'my_smtp_mail_password'
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
```
Tip: don't include `config.py` in git because it will risk being exposed to the public. Put it in `.gitignore` (we already did it for you!) and create one manually on the server when deployed.

## Bug fix, development, and improvement

The software is provided AS-IS under MIT license, and we acknowledge that there are non-optimised or inefficient codes. If you encounter bugs, or have development ideas for improvement, please don't hesitate to create a pull request, or send us questions or ideas to the email in the following section. Please note that this is not a dedicated open-source project. We simply release the source code for public benefit while focusing on internal use, therefore we might not be able to actively engage in development discussion as much as other major open-source projects do.

## A bit of a background

We originally created Deep Matters LMS to solve a practical problem. Previously we had developed a minimal e-learning system, but for each deployment it required extensive coding especially in navigation and test feedback part. It also does not allow a non-technical author to manage the course on his/her own. Deep Matters LMS was primarily designed to fix these two problems, by allowing front-end management of courses and learning content. It also has a built-in certificate issuer and verifier sub-system which was previously provided in a separated system.

The system is aimed to empower social impact and educational organisations in Thailand to be able to provide e-learning services to their beneficiaries and clients. We will be happy to discuss how this system could be used to support your social impact goals. Please contact chitpong [at] changefusion [dot] org for more information.