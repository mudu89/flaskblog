import os
import secrets
from flask import render_template, url_for, flash,redirect,request,abort
from flaskblog.forms import LoginForm, RegistrationForm, UpdateAccountForm, PostForm
from flaskblog.models import User, Post
from flaskblog import app,db, bcrpyt
from flask_login import login_user,current_user,logout_user,login_required
from PIL import Image

@app.route("/")
@app.route("/home")
@login_required
def home():
    posts = Post.query.all()
    return render_template('home.html',posts=posts, title=None)

@app.route("/about")
def about():
    return render_template('about.html',title=None)

@app.route("/login",methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in!", category='success')
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrpyt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            #flash("You have been logged in!",category='success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash("Login unsuccesfull",category='danger')
    return render_template('login.html',title='Login',form=form)

@app.route("/register",methods=['POST','GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrpyt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created!',category='success')
        return redirect(url_for('login'))
    return render_template('register.html',title='Register',form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/account",methods=['POST','GET'])
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
        return redirect(url_for('account'))
    elif request.method=='GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        posts = Post.query.all()
    image_file = url_for('static',filename= 'profile_pics/' + current_user.image_file)
    return render_template('account.html',title='Account', image_file=image_file, form=form,posts=posts)

def save_date(form_picture):
    random_hex = secrets.token_hex(8)
    _,fext = os.path.splitext(form_picture.filename)
    output_size=(125,125)
    picture_path=os.path.join(app.root_path,'static/profile_pics',random_hex+fext)
    i=Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return random_hex+fext

@app.route("/new/post",methods=['GET','POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post has been created !",category='success')
        return redirect(url_for('home'))
    return render_template('create_post.html',title='New Post',
                           form=form, legend='New Post')

@app.route("/post/<int:post_id>",methods=['GET'])
@login_required
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html',title=post.title,post=post)

@app.route("/post/<int:post_id>/update",methods=['GET','POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author!= current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Your Post has been updated!",category='success')
        return redirect(url_for('post',post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html',title='Update Post',
                           form=form, legend='Update Post')

@app.route("/post/<int:post_id>/delete",methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author!= current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted!",'success')
    return redirect(url_for('home'))