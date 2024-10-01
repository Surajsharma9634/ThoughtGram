from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
import uuid
import random
import string

app = Flask(__name__)

# File paths
USERS_FILE = 'users.json'
POSTS_FILE = 'posts.json'

# Load and save data functions
def load_data(file_path):
    return json.load(open(file_path, 'r')) if os.path.exists(file_path) else {}

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# Load users and posts
users = load_data(USERS_FILE)
posts = load_data(POSTS_FILE)

# Generate a random code for user profiles
def generate_random_code(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Homepage
@app.route('/')
def home():
    username = request.args.get('username')
    if not username:
        return redirect(url_for('login'))
    
    all_posts = sorted(posts.values(), key=lambda x: x['timestamp'], reverse=True)
    return render_template('home.html', username=username, posts=all_posts, users=users)

# Registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        profile_photo = request.files.get('profile_photo')

        if username in users:
            return "Username already exists!"
        
        photo_filename = f'{uuid.uuid4()}.jpg' if profile_photo else None
        if profile_photo:
            profile_photo.save(os.path.join('static/uploads', photo_filename))

        users[username] = {
            'password': password,
            'profile_photo': photo_filename,
            'random_code': generate_random_code()  # Store random code
        }
        save_data(USERS_FILE, users)
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        if username in users and users[username]['password'] == password:
            return redirect(url_for('home', username=username))
        return "Invalid username or password!"
    
    return render_template('login.html')

# Post creation
@app.route('/post', methods=['POST'])
def create_post():
    username = request.form['username']
    content = request.form['content']
    
    post_id = str(uuid.uuid4())
    new_post = {
        'id': post_id,
        'username': username,
        'content': content,
        'likes': 0,
        'comments': [],
        'timestamp': str(uuid.uuid1().time)
    }

    posts[post_id] = new_post
    save_data(POSTS_FILE, posts)
    return redirect(url_for('home', username=username))

# Like a post
@app.route('/like/<post_id>', methods=['POST'])
def like_post(post_id):
    if post_id in posts:
        posts[post_id]['likes'] += 1
        save_data(POSTS_FILE, posts)
        return jsonify({'likes': posts[post_id]['likes']})
    return jsonify({'error': 'Post not found'}), 404

# Comment on a post
@app.route('/comment/<post_id>', methods=['POST'])
def comment_post(post_id):
    username = request.args['username']
    comment = request.form['comment']
    
    if post_id in posts:
        posts[post_id]['comments'].append({'username': username, 'content': comment})
        save_data(POSTS_FILE, posts)
        return redirect(url_for('home', username=username))
    
    return "Post not found!", 404

# Edit a post
@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    username = request.args['username']
    
    if post_id not in posts or posts[post_id]['username'] != username:
        return "Unauthorized or post not found!", 403
    
    if request.method == 'POST':
        posts[post_id]['content'] = request.form['content']
        save_data(POSTS_FILE, posts)
        return redirect(url_for('home', username=username))
    
    post = posts[post_id]
    return render_template('edit_post.html', post=post)

# Delete a post
@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    username = request.args['username']

    if post_id in posts and posts[post_id]['username'] == username:
        del posts[post_id]
        save_data(POSTS_FILE, posts)
        return redirect(url_for('home', username=username))
    
    return "Unauthorized or post not found!", 403

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
