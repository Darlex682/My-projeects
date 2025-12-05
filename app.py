import os
from datetime import datetime
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    owner = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(40), default="Planned", nullable=False)
    description = db.Column(db.Text, default="", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "owner": self.owner,
            "status": self.status,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }


@app.before_first_request
def setup_db():
    db.create_all()


@app.context_processor
def inject_now():
    return {"datetime": datetime}


@app.route("/")
def home():
    total_projects = Project.query.count()
    active = Project.query.filter_by(status="Active").count()
    planned = Project.query.filter_by(status="Planned").count()
    completed = Project.query.filter_by(status="Completed").count()
    return render_template(
        "home.html",
        total_projects=total_projects,
        active=active,
        planned=planned,
        completed=completed,
    )


@app.route("/projects")
def list_projects():
    search = request.args.get("q", "").strip()
    query = Project.query
    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            db.or_(Project.name.ilike(like_pattern), Project.owner.ilike(like_pattern))
        )
    projects = query.order_by(Project.created_at.desc()).all()
    return render_template("projects.html", projects=projects, search=search)


@app.route("/projects/<int:project_id>")
def project_detail(project_id: int):
    project = Project.query.get_or_404(project_id)
    return render_template("project_detail.html", project=project)


@app.route("/projects/new", methods=["GET", "POST"])
def create_project():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        owner = request.form.get("owner", "").strip()
        status = request.form.get("status", "Planned").strip() or "Planned"
        description = request.form.get("description", "").strip()

        if not name or not owner:
            error = "Название и владелец обязательны"
            return render_template("new_project.html", error=error)

        project = Project(
            name=name,
            owner=owner,
            status=status,
            description=description,
        )
        db.session.add(project)
        db.session.commit()
        return redirect(url_for("project_detail", project_id=project.id))

    return render_template("new_project.html")


@app.route("/dashboard")
def dashboard():
    total_projects = Project.query.count()
    by_status = (
        db.session.query(Project.status, db.func.count(Project.id))
        .group_by(Project.status)
        .all()
    )
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    status_summary = {status: count for status, count in by_status}
    return render_template(
        "dashboard.html",
        total_projects=total_projects,
        status_summary=status_summary,
        recent_projects=recent_projects,
    )


@app.route("/api/projects")
def projects_api():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return jsonify([p.to_dict() for p in projects])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
