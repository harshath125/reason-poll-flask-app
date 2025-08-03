import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv 
from models import db, Poll, Response, User
# --- MODIFIED: Import the updated analysis function ---
from analysis import analyze_sentiment, extract_keywords, generate_option_summary
import json
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a-very-secret-key-for-dev')

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'reasonpoll.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# --- MODIFIED: The results route now generates a summary for each option ---
@app.route("/results/<int:poll_id>")
def results(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    responses = poll.responses
    total_votes = len(responses)
    options = poll.get_options_list()
    
    vote_counts = {option: 0 for option in options}
    sentiment_data = {option: {"Positive": 0, "Negative": 0, "Neutral": 0} for option in options}
    reasons_by_option = {option: [] for option in options}

    for response in responses:
        if response.selected_option in options:
            vote_counts[response.selected_option] += 1
            sentiment_data[response.selected_option][response.sentiment] += 1
            if response.reason_text:
                reasons_by_option[response.selected_option].append(response.reason_text)

    # --- NEW: Generate a local summary for each option ---
    option_summaries = {}
    for option, reasons in reasons_by_option.items():
        option_summaries[option] = generate_option_summary(option, reasons)

    vote_counts_json = json.dumps(vote_counts)
    sentiment_data_json = json.dumps(sentiment_data)

    return render_template(
        "result.html", poll=poll, total_votes=total_votes, vote_counts=vote_counts,
        vote_counts_json=vote_counts_json, sentiment_data_json=sentiment_data_json,
        option_summaries=option_summaries
    )

# (All other routes remain the same)
# ...
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))
        role = 'admin' if User.query.count() == 0 else 'user'
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        if role == 'admin': flash('Congratulations! As the first user, you have admin privileges.', 'success')
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
        login_user(user, remember=True)
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/")
def home():
    polls = Poll.query.order_by(Poll.created_at.desc()).all()
    return render_template("index.html", polls=polls)

@app.route("/poll/<int:poll_id>", methods=["GET", "POST"])
@login_required
def vote(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    existing_vote = Response.query.filter_by(user_id=current_user.id, poll_id=poll.id).first()
    if existing_vote:
        flash("You have already voted in this poll.", "error")
        return redirect(url_for('results', poll_id=poll_id))
    if request.method == "POST":
        selected_option = request.form.get("option")
        reason = request.form.get("reason", "").strip()
        if not selected_option:
            flash("You must select an option to vote.", "error")
            return redirect(url_for("vote", poll_id=poll_id))
        sentiment = analyze_sentiment(reason)
        keywords_list = extract_keywords(reason)
        keywords_str = ','.join(keywords_list)
        new_response = Response(
            poll_id=poll.id, user_id=current_user.id, selected_option=selected_option, 
            reason_text=reason, sentiment=sentiment, keywords=keywords_str
        )
        db.session.add(new_response)
        db.session.commit()
        flash("Your vote has been counted. Thank you!", "success")
        return redirect(url_for("results", poll_id=poll_id))
    return render_template("vote.html", poll=poll)

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if current_user.role != 'admin':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('home'))
    if request.method == "POST":
        question = request.form.get("question")
        options_str = request.form.get("options")
        options_list = [opt.strip() for opt in options_str.split(',') if opt.strip()]
        if not question or len(options_list) < 2:
            flash("A question and at least two comma-separated options are required.", "error")
            return redirect(url_for("admin"))
        new_poll = Poll(question=question, options=','.join(options_list), creator_id=current_user.id)
        db.session.add(new_poll)
        db.session.commit()
        flash("Poll created successfully!", "success")
        return redirect(url_for("home"))
    return render_template("admin.html")

if __name__ == "__main__":
    app.run(debug=True)
