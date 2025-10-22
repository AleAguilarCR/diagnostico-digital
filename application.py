# AWS Elastic Beanstalk requiere que el archivo principal se llame application.py
from app import app as application

if __name__ == "__main__":
    application.run()