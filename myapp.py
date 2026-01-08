from flask import Flask, render_template, request, redirect, session, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'secret123'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'socialmedia'

mysql = MySQL(app)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def format_mention(text):
    words = text.split()
    new = []
    for w in words:
        if w.stratswith('@'):
            uname = w[1:]
            new.append(f'<a href="/search/{uname}">@{uname}</a>')
        else:
            new.append(w)
    return ''.join(new)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        e = request.form['email']
        p = generate_password_hash(request.form['password'])

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(username, email, password) VALUES(%s, %s, %s)", (u,e,p))
        mysql.connection.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        e = request.form['email']
        p = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (e,))
        user = cur.fetchone()

        if user and check_password_hash(user[3], p):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/')
        return render_template('login.html')
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login')
    
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT posts.*, users.username,
        (SELECT COUNT(*) FROM likes_post WHERE post_id = post.id) AS like_count,
        (SELECT COUNT(*) FROM comments WHERE post_id = post.id) AS comment_count
        FROM posts 
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.id DESC
    """)
    posts = cur.fetchall()

    posts = list(posts)
    for i in range(len(posts)):
        posts[i] = list(posts[i])
        posts[i][2] = format_mention(posts[i][2])

    cur.execute("""
        SELECT comments.*, users.username,
        (SELECT COUNT(*) FROM likes_comment WHERE comment_id = comments.id) AS lc
        FROM comments
        JOIN users ON comments.user_id = users.id
    """)
    comments = cur.fetchall()

    return render_template('home.html', posts=posts, comments=comments)

@app.route('/post', method=['POST'])
def post():
    file = request.files['file']
    caption = request.form['caption']
    ptype = request.form['type']

    filename = file.filename
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO posts(user_id, caption, file, type) VALUES(%s, %s, %s, %s)", 
        (session['user_id'], caption, filename, ptype)
    )
    mysql.connection.commit()
    return redirect('/')

@app.route('/like/<int:post_id>')
def like(post_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id FROM likes_post WHERE post_id=%s AND user_id=%s", 
        (post_id, session['user_id']))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO likes_post(post_id, user_id) VALUES(%s, %s)", 
            (post_id, session['user_id']))
        mysql.connection.commit()
    return redirect('/')

@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    text = request.form['comment']
    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO comments(post_id, user_id, comment) VALUES(%s, %s, %s)",
        (post_id, session['user_id'], text)
    )
    mysql.connection.commit()
    return redirect('/')

@app.route('/like_comment/<int:cid>')
def like_comment(cid):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id FROM likes_comment WHERE comment_id=%s AND user_id=%s", 
        (cid, session['user_id'])
    )
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO likes_comment(post_id, user_id) VALUES(%s, %s)", 
            (cid, session['user_id'])
        )
        mysql.connection.commit()
    return redirect('/')

@app.route('/delete_post/<int:pid>')
def delete_post(pid):
    cur = mysql.connection.cursor()
    cur.execute(
        "DELETE FROM posts WHERE id=%s AND user_id=%s",
        (pid, session['user_id'])
    )
    mysql.connection.commit()
    return redirect('/')

@app.route('/follow/<int:user_id>')
def follow(user_id):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id FROM follow WHERE follower_id=%s AND following_id=%s)", 
        (session['user_id'], user_id)
    )
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO follow (follower_id, following_id) VALUES(%s, %s)", 
            (session['user_id'], user_id)
        )
    mysql.connection.commit()
    return redirect('/profile/' + str(user_id))

@app.route('/profile/<int:uid>')
def profile(uid):
    cur = mysql.connection.cursor()

    cur.execute("SELECT username FROM users WHERE id=%s", (uid,))
    user = cur.fetchone()

    cur.execute("SELECT COUNT(*) FROM follow WHERE following_id=%s", (uid,))
    followers = cur.fetchone()

    cur.execute("SELECT COUNT(*) FROM follow WHERE follower_id=%s", (uid,))
    following = cur.fetchone()
    
    cur.execute("SELECT * FROM users WHERE user_id=%s ORDER BY id DESC", (uid,))
    posts = cur.fetchone()

    return render_template(
        'profile.html',
        user=user, followers=followers, following=following, posts=posts, uid=uid
    )

@app.route('/chat/<int:uid>', methods=['GET', 'POST'])
def chat(uid):
    if request.method == 'POST':
        msg = request.form['message']
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO chat(sender_id, receiver_id, message) VALUES(%s, %s, %s)", 
            (session['user_id'], uid, msg)
        )
        mysql.connection.commit()

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT * FROM chat 
            WHERE (sender_id=%s AND receiver_id=%s) 
               OR (sender_id=%s AND receiver_id=%s) 
            ORDER BY id
        """, (session['user_id'], uid, uid, session['user_id']))
        chats = cur.fetchall()

        return render_template('chat.html', chats=chats, uid=uid)
    

if __name__ == '__main__':
    app.run(debug=True)