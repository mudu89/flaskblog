import os
import secrets
from PIL import Image
from flask import url_for
from flask_mail import Message
from flaskblog import mail
from flask import current_app as app

def save_date(form_picture):
    random_hex = secrets.token_hex(8)
    _,fext = os.path.splitext(form_picture.filename)
    output_size=(125,125)
    picture_path=os.path.join(app.root_path,'static/profile_pics',random_hex+fext)
    i=Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return random_hex+fext

#_external=True -> to get the absolute URL
def send_reset_mail(user):
    token = user.get_reset_token()
    msg = Message("Password Reset Request", sender='noreply@gmail.com', recipients=[user.email])
    msg.body=f''' To reset the password, visit the following link:
{url_for('users.reset_token',token=token,_external=True)}
If you did not make this request ignore this email
'''
    mail.send(msg)
    return
