# INF601 - Advanced Programming in Python
# Bunyamin Sari
# Mini Project 3


from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def home():
    return render_template('blog/home.html')


@bp.route('/posts')
@login_required
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))



#Comment CRUD
# Add a route to create a comment
@bp.route('/<int:post_id>/comment/create', methods=('GET','POST'))
@login_required
def create_comment(post_id):
    if request.method == 'POST':
        text = request.form['text']
        error = None

        if not text:
            error = 'Comment text is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO comment (post_id, author_id, text)'
                ' VALUES (?, ?, ?)',
                (post_id, g.user['id'], text)
            )
            db.commit()
            return redirect(url_for('blog.view_post', post_id=post_id))

    return render_template('blog/create_comment.html',post_id=post_id)

# Add a route to update a comment
@bp.route('/comment/<int:comment_id>/update', methods=('GET', 'POST'))
@login_required
def update_comment(comment_id):
    # Get the comment by its ID
    db = get_db()
    comment = db.execute(
        'SELECT c.id, post_id, text, created, author_id, username'
        ' FROM comment c JOIN user u ON c.author_id = u.id'
        ' WHERE c.id = ?',
        (comment_id,)
    ).fetchone()

    # Check if the comment exists
    if comment is None:
        abort(404, f"Comment id {comment_id} doesn't exist.")

    # Check if the current user is the author of the comment
    if comment['author_id'] != g.user['id']:
        abort(403, "You are not the author of this comment.")

    if request.method == 'POST':
        text = request.form['text']
        error = None

        if not text:
            error = 'Comment text is required.'

        if error is not None:
            flash(error)
        else:
            # Update the comment in the database
            db.execute(
                'UPDATE comment SET text = ? WHERE id = ?',
                (text, comment_id)
            )
            db.commit()
            return redirect(url_for('blog.view_post', post_id=comment['post_id']))

    return render_template('blog/update_comment.html', comment=comment)


# Add a route to delete a comment
@bp.route('/comment/<int:comment_id>/delete', methods=('POST',))
@login_required
def delete_comment(comment_id):
    db = get_db()
    comment = db.execute(
        'SELECT c.id, post_id, author_id'
        ' FROM comment c'
        ' WHERE c.id = ?',
        (comment_id,)
    ).fetchone()

    # Check if the comment exists
    if comment is None:
        abort(404, f"Comment id {comment_id} doesn't exist.")

    # Check if the current user is the author of the comment
    if comment['author_id'] != g.user['id']:
        abort(403, "You are not the author of this comment.")

    # Delete the comment from the database
    db.execute('DELETE FROM comment WHERE id = ?', (comment_id,))
    db.commit()

    # Redirect to the post's page where the comment belonged
    return redirect(url_for('blog.view_post', post_id=comment['post_id']))

@bp.route('/post/<int:post_id>')
def view_post(post_id):
    db = get_db()

    # Retrieve the post details
    post = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (post_id,)
    ).fetchone()

    # Retrieve comments associated with the post
    comments = db.execute(
        'SELECT c.id, text, created, author_id, username'
        ' FROM comment c JOIN user u ON c.author_id = u.id'
        ' WHERE c.post_id = ?'
        ' ORDER BY created DESC',
        (post_id,)
    ).fetchall()

    # Render the post and comments in the template
    return render_template('blog/view_post.html', post=post, comments=comments,post_id=post_id)

