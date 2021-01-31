from flask import Blueprint,redirect,render_template,request,flash,url_for
from flask_login import login_required,logout_user,login_user,current_user
from flaskblog import db,bcrpyt
from flaskblog.models import User, Post
from flaskblog.users.forms import RegistrationForm,LoginForm,UpdateAccountForm,ResetPasswordForm,RequestResetForm
from flaskblog.users.utils import save_date,send_reset_mail

users = Blueprint('users',__name__)

@users.route("/register",methods=['POST','GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrpyt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created!',category='success')
        return redirect(url_for('users.login'))
    return render_template('register.html',title='Register',form=form)

@users.route("/login",methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in!", category='success')
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrpyt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            #flash("You have been logged in!",category='success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash("Login unsuccesfull",category='danger')
    return render_template('login.html',title='Login',form=form)

@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@users.route("/account",methods=['POST','GET'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_date(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash(f"Account has been updated",category='success')
        return redirect(url_for('users.account'))
    elif request.method=='GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        posts = Post.query.order_by(Post.date_posted.desc()).filter_by(author=current_user).all()
    image_file = url_for('static',filename= 'profile_pics/' + current_user.image_file)
    return render_template('account.html',title='Account', image_file=image_file, form=form,posts=posts)

@users.route("/user/<string:username>", methods=['GET'])
def user_posts(username):
    page = request.args.get('page',1,type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts=Post.query.filter_by(author=user)\
                    .order_by(Post.date_posted.desc())\
                    .paginate(per_page=5,page=page)
    return render_template('user_post.html',title='User Posts',posts=posts, user=user)

@users.route("/reset_password",methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form=RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_mail(user)
        flash("An email has been sent to reset the passoword",category='info')
        redirect(url_for("users.login"))
    return render_template('resetrequest.html',title='Reset Password',form=form)


@users.route("/reset_password/<token>",methods=['GET','POST'])
def reset_token(token):
    user = User.verify_reset_token(token)
    if not user:
        flash("That is an invalid or expired link",category='warning')
        return redirect(url_for('users.reset_request'))
    form=ResetPasswordForm()
    if form.validate_on_submit():
        print(form.password.data)
        hashed_password = bcrpyt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your password has been updated!',category='success')
        return redirect(url_for('users.login'))
    return render_template('reset_password.html',title='Reset Password',form=form)