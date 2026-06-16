import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Task, TaskProof

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Setup Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Helper to check allowed file extensions
    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    # Route: Home/Redirect
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            elif current_user.role == 'HOD':
                return redirect(url_for('hod_dashboard'))
            elif current_user.role == 'Manager':
                return redirect(url_for('manager_dashboard'))
            elif current_user.role == 'Employee':
                return redirect(url_for('employee_dashboard'))
        return redirect(url_for('login'))

    # Route: Login
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'GET' and current_user.is_authenticated:
            return redirect(url_for('index'))
            
        if request.method == 'POST':
            if current_user.is_authenticated:
                logout_user()
                
            email = request.form.get('email')
            password = request.form.get('password')
            remember = True if request.form.get('remember') else False
            
            user = User.query.filter_by(email=email).first()
            
            if not user or not user.check_password(password):
                flash('Invalid email or password.', 'error')
                return redirect(url_for('login'))
                
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('index'))
            
        return render_template('login.html')

    # Route: Logout
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    # Route: Admin Dashboard
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        if current_user.role != 'Admin':
            flash('Access denied.', 'error')
            return redirect(url_for('index'))
            
        users = User.query.filter(User.role != 'Admin').all()
        
        # Get list of unique departments
        departments = [d[0] for d in db.session.query(User.department).distinct() if d[0]]
        if "Housekeeping" not in departments: departments.append("Housekeeping")
        if "Maintenance" not in departments: departments.append("Maintenance")
        if "Kitchen" not in departments: departments.append("Kitchen")
        if "Laundry" not in departments: departments.append("Laundry")
        if "Front Office" not in departments: departments.append("Front Office")
        
        # Simple stats for overview
        total_tasks = Task.query.count()
        completed_tasks = Task.query.filter(Task.status.in_(['Completed', 'Approved'])).count()
        pending_tasks = Task.query.filter(Task.status == 'Pending').count()
        in_progress_tasks = Task.query.filter(Task.status == 'In Progress').count()
        
        return render_template(
            'dashboard_admin.html', 
            users=users, 
            departments=sorted(list(set(departments))),
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            pending_tasks=pending_tasks,
            in_progress_tasks=in_progress_tasks
        )

    # Action: Create User (Admin only)
    @app.route('/admin/user/create', methods=['POST'])
    @login_required
    def admin_create_user():
        if current_user.role != 'Admin':
            return jsonify({'success': False, 'message': 'Access denied.'}), 403
            
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        department = request.form.get('department')
        
        if not name or not email or not password or not role or not department:
            flash('All fields are required.', 'error')
            return redirect(url_for('admin_dashboard'))
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'error')
            return redirect(url_for('admin_dashboard'))
            
        new_user = User(name=name, email=email, role=role, department=department)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'User {name} successfully created.', 'success')
        return redirect(url_for('admin_dashboard'))

    # Route: HOD Dashboard
    @app.route('/hod')
    @login_required
    def hod_dashboard():
        if current_user.role != 'HOD':
            flash('Access denied.', 'error')
            return redirect(url_for('index'))
            
        dept = current_user.department
        
        # Get employees of HOD's department
        employees = User.query.filter_by(role='Employee', department=dept).all()
        
        # Get all tasks created by this HOD OR assigned to their department employees
        emp_ids = [emp.id for emp in employees]
        tasks = Task.query.filter(
            (Task.assigned_by_id == current_user.id) | 
            (Task.assigned_to_id.in_(emp_ids))
        ).order_by(Task.created_at.desc()).all()
        
        # Stats
        total = len(tasks)
        pending = sum(1 for t in tasks if t.status == 'Pending')
        in_progress = sum(1 for t in tasks if t.status == 'In Progress')
        completed = sum(1 for t in tasks if t.status in ['Completed', 'Approved'])
        
        return render_template(
            'dashboard_hod.html',
            employees=employees,
            tasks=tasks,
            total=total,
            pending=pending,
            in_progress=in_progress,
            completed=completed
        )

    # Route: Manager Dashboard
    @app.route('/manager')
    @login_required
    def manager_dashboard():
        if current_user.role != 'Manager':
            flash('Access denied.', 'error')
            return redirect(url_for('index'))
            
        # Managers can assign tasks to ANY Employee in the hotel
        employees = User.query.filter_by(role='Employee').all()
        
        # Tasks assigned by this manager or global tasks
        tasks = Task.query.order_by(Task.created_at.desc()).all()
        
        # Tasks requiring verification (status is Completed, or proof status is Pending)
        # Note: We can filter tasks that are Completed and need review
        pending_approvals = Task.query.filter(Task.status == 'Completed').all()
        
        # Stats
        total = len(tasks)
        pending = sum(1 for t in tasks if t.status == 'Pending')
        in_progress = sum(1 for t in tasks if t.status == 'In Progress')
        completed = sum(1 for t in tasks if t.status == 'Approved')
        awaiting_approval = len(pending_approvals)
        active_count = sum(1 for t in tasks if t.status in ['Pending', 'In Progress', 'Rejected', 'Awaiting Handover'])
        
        # Get list of unique departments for dependent dropdowns
        departments = [d[0] for d in db.session.query(User.department).distinct() if d[0]]
        if "Housekeeping" not in departments: departments.append("Housekeeping")
        if "Maintenance" not in departments: departments.append("Maintenance")
        if "Kitchen" not in departments: departments.append("Kitchen")
        if "Laundry" not in departments: departments.append("Laundry")
        if "Front Office" not in departments: departments.append("Front Office")
        departments = sorted(list(set(departments)))
        
        return render_template(
            'dashboard_manager.html',
            employees=employees,
            tasks=tasks,
            pending_approvals=pending_approvals,
            total=total,
            pending=pending,
            in_progress=in_progress,
            completed=completed,
            awaiting_approval=awaiting_approval,
            active_count=active_count,
            departments=departments
        )

    # Route: Employee Dashboard
    @app.route('/employee')
    @login_required
    def employee_dashboard():
        if current_user.role != 'Employee':
            flash('Access denied.', 'error')
            return redirect(url_for('index'))
            
        tasks = Task.query.filter_by(assigned_to_id=current_user.id).order_by(Task.deadline.asc()).all()
        
        pending_tasks = [t for t in tasks if t.status in ['Pending', 'In Progress', 'Rejected']]
        completed_tasks = [t for t in tasks if t.status in ['Completed', 'Approved']]
        
        overdue_count = sum(1 for t in pending_tasks if t.is_overdue())
        pending_count = sum(1 for t in pending_tasks if t.status in ['Pending', 'Rejected'])
        in_progress_count = sum(1 for t in pending_tasks if t.status == 'In Progress')
        
        # Get HOD for the current user's department
        hod = None
        if current_user.department:
            hod = User.query.filter_by(role='HOD', department=current_user.department).first()
        
        return render_template(
            'dashboard_employee.html',
            pending_tasks=pending_tasks,
            completed_tasks=completed_tasks,
            overdue_count=overdue_count,
            pending_count=pending_count,
            in_progress_count=in_progress_count,
            hod=hod
        )

    # Action: Create Task (HOD and Manager)
    @app.route('/task/create', methods=['POST'])
    @login_required
    def create_task():
        if current_user.role not in ['HOD', 'Manager']:
            flash('Unauthorized task creation.', 'error')
            return redirect(url_for('index'))
            
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        location = request.form.get('location')
        assigned_to_id = request.form.get('assigned_to')
        priority = request.form.get('priority', 'Medium')
        deadline_str = request.form.get('deadline')
        
        if not title or not deadline_str:
            flash('Task title and deadline are required.', 'error')
            return redirect(url_for('index'))
            
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                flash('Invalid deadline format.', 'error')
                return redirect(url_for('index'))
                
        if deadline < datetime.utcnow():
            flash('Deadline cannot be in the past.', 'error')
            return redirect(url_for('index'))
                
        # Validate that if HOD, assigned employee is in the same department
        assigned_to_id = int(assigned_to_id) if assigned_to_id else None
        if assigned_to_id and current_user.role == 'HOD':
            emp = User.query.get(assigned_to_id)
            if not emp or emp.department != current_user.department:
                flash('You can only assign tasks to employees within your department.', 'error')
                return redirect(url_for('index'))
                
        new_task = Task(
            title=title,
            description=description,
            category=category,
            location=location,
            assigned_to_id=assigned_to_id,
            assigned_by_id=current_user.id,
            priority=priority,
            status='Pending',
            deadline=deadline
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        flash('Task successfully created and assigned.', 'success')
        return redirect(url_for('index'))

    # Action: Reassign Task (Manager and HOD)
    @app.route('/task/reassign/<int:task_id>', methods=['POST'])
    @login_required
    def reassign_task(task_id):
        if current_user.role not in ['Manager', 'HOD']:
            flash('Access denied.', 'error')
            return redirect(url_for('index'))
            
        task = Task.query.get_or_404(task_id)
        
        # HOD department check
        if current_user.role == 'HOD':
            # Check if task is associated with HOD's department
            # Since HOD can only assign tasks to their own department employees, the new assignee must be in HOD's dept.
            pass
            
        new_assignee_id = request.form.get('assigned_to')
        if not new_assignee_id:
            flash('Assignee is required.', 'error')
            return redirect(url_for('index'))
            
        new_assignee = User.query.get_or_404(int(new_assignee_id))
        
        if current_user.role == 'HOD' and new_assignee.department != current_user.department:
            flash('You can only reassign tasks within your department.', 'error')
            return redirect(url_for('hod_dashboard'))
            
        task.assigned_to_id = new_assignee.id
        
        # If task was completed/approved/handover, reset back to Pending
        if task.status in ['Approved', 'Completed', 'Awaiting Handover']:
            task.status = 'Pending'
            
        db.session.commit()
        flash(f'Task reassigned to {new_assignee.name}.', 'success')
        
        # Redirect back to HOD or Manager dashboard
        if current_user.role == 'HOD':
            return redirect(url_for('hod_dashboard'))
        return redirect(url_for('manager_dashboard'))

    # Action: Start Task (Employee sets status to In Progress)
    @app.route('/task/start/<int:task_id>', methods=['POST'])
    @login_required
    def start_task(task_id):
        if current_user.role != 'Employee':
            return jsonify({'success': False, 'message': 'Only employees can work on tasks.'}), 403
            
        task = Task.query.get_or_404(task_id)
        if task.assigned_to_id != current_user.id:
            return jsonify({'success': False, 'message': 'This task is not assigned to you.'}), 403
            
        task.status = 'In Progress'
        db.session.commit()
        flash('Task status updated to In Progress. Time to excel!', 'success')
        return redirect(url_for('employee_dashboard'))

    # Action: Upload Before Photo (Employee)
    @app.route('/task/upload_before/<int:task_id>', methods=['POST'])
    @login_required
    def upload_before(task_id):
        if current_user.role != 'Employee':
            return jsonify({'success': False, 'message': 'Unauthorized.'}), 403
            
        task = Task.query.get_or_404(task_id)
        if task.assigned_to_id != current_user.id:
            return jsonify({'success': False, 'message': 'This task is not assigned to you.'}), 403
            
        if 'before_photo' not in request.files:
            flash('No file selected.', 'error')
            return redirect(url_for('employee_dashboard'))
            
        file = request.files['before_photo']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('employee_dashboard'))
            
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"task_{task.id}_before_{int(datetime.utcnow().timestamp())}.{ext}"
            
            # Make sure upload folder exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Store in DB
            proof = TaskProof.query.filter_by(task_id=task.id).first()
            if not proof:
                proof = TaskProof(task_id=task.id, before_image_path=filename, approval_status='Pending')
                db.session.add(proof)
            else:
                proof.before_image_path = filename
                
            task.status = 'In Progress' # Keep In Progress when before uploaded
            db.session.commit()
            
            flash('Before photo successfully uploaded.', 'success')
        else:
            flash('Allowed file formats: PNG, JPG, JPEG, WEBP.', 'error')
            
        return redirect(url_for('employee_dashboard'))

    # Action: Upload After Photo & Complete Task (Employee)
    @app.route('/task/upload_after/<int:task_id>', methods=['POST'])
    @login_required
    def upload_after(task_id):
        if current_user.role != 'Employee':
            return jsonify({'success': False, 'message': 'Unauthorized.'}), 403
            
        task = Task.query.get_or_404(task_id)
        if task.assigned_to_id != current_user.id:
            return jsonify({'success': False, 'message': 'This task is not assigned to you.'}), 403
            
        proof = TaskProof.query.filter_by(task_id=task.id).first()
        if not proof or not proof.before_image_path:
            flash('Please upload a "Before" photo first.', 'warning')
            return redirect(url_for('employee_dashboard'))
            
        if 'after_photo' not in request.files:
            flash('No file selected.', 'error')
            return redirect(url_for('employee_dashboard'))
            
        file = request.files['after_photo']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('employee_dashboard'))
            
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"task_{task.id}_after_{int(datetime.utcnow().timestamp())}.{ext}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            proof.after_image_path = filename
            proof.approval_status = 'Pending'
            proof.uploaded_at = datetime.utcnow()
            proof.employee_notes = request.form.get('employee_notes')
            
            task.status = 'Completed' # Set to Completed awaiting manager review
            db.session.commit()
            
            flash('Task submitted successfully! Awaiting manager verification.', 'success')
        else:
            flash('Allowed file formats: PNG, JPG, JPEG, WEBP.', 'error')
            
        return redirect(url_for('employee_dashboard'))

    # Action: Shift Handover Task (Employee)
    @app.route('/task/handover/<int:task_id>', methods=['POST'])
    @login_required
    def handover_task(task_id):
        if current_user.role != 'Employee':
            return jsonify({'success': False, 'message': 'Unauthorized.'}), 403
            
        task = Task.query.get_or_404(task_id)
        if task.assigned_to_id != current_user.id:
            return jsonify({'success': False, 'message': 'This task is not assigned to you.'}), 403
            
        if 'progress_photo' not in request.files:
            flash('Progress photo is required for handover.', 'warning')
            return redirect(url_for('employee_dashboard'))
            
        file = request.files['progress_photo']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('employee_dashboard'))
            
        notes = request.form.get('employee_notes', '')
        if not notes:
            flash('Handover notes are required.', 'warning')
            return redirect(url_for('employee_dashboard'))
            
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"task_{task.id}_progress_{int(datetime.utcnow().timestamp())}.{ext}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            proof = TaskProof.query.filter_by(task_id=task.id).first()
            if not proof:
                proof = TaskProof(task_id=task.id, progress_image_path=filename, employee_notes=notes, approval_status='Pending')
                db.session.add(proof)
            else:
                proof.progress_image_path = filename
                proof.employee_notes = notes
                
            task.status = 'Awaiting Handover'
            db.session.commit()
            flash('Shift handover request successfully submitted to your manager.', 'success')
        else:
            flash('Allowed file formats: PNG, JPG, JPEG, WEBP.', 'error')
            
        return redirect(url_for('employee_dashboard'))

    # Action: Quick Complete Low Priority Task (Employee)
    @app.route('/task/quick_complete/<int:task_id>', methods=['POST'])
    @login_required
    def quick_complete(task_id):
        if current_user.role != 'Employee':
            return jsonify({'success': False, 'message': 'Only employees can complete tasks.'}), 403
            
        task = Task.query.get_or_404(task_id)
        if task.assigned_to_id != current_user.id:
            return jsonify({'success': False, 'message': 'This task is not assigned to you.'}), 403
            
        if task.priority != 'Low':
            flash('Only low priority tasks can be completed without photos.', 'warning')
            return redirect(url_for('employee_dashboard'))
            
        task.status = 'Completed'
        db.session.commit()
        
        # Ensure a task proof object exists for standard completion checks
        proof = TaskProof.query.filter_by(task_id=task.id).first()
        notes = request.form.get('employee_notes')
        if not proof:
            proof = TaskProof(task_id=task.id, approval_status='Pending', uploaded_at=datetime.utcnow(), employee_notes=notes)
            db.session.add(proof)
        else:
            proof.uploaded_at = datetime.utcnow()
            proof.approval_status = 'Pending'
            proof.employee_notes = notes
        db.session.commit()
        
        flash('Task quick completed! Awaiting manager verification.', 'success')
        return redirect(url_for('employee_dashboard'))

    # Action: Approve Task (Manager only)
    @app.route('/task/approve/<int:task_id>', methods=['POST'])
    @login_required
    def approve_task(task_id):
        if current_user.role != 'Manager':
            return jsonify({'success': False, 'message': 'Access denied.'}), 403
            
        task = Task.query.get_or_404(task_id)
        proof = TaskProof.query.filter_by(task_id=task.id).first()
        
        task.status = 'Approved'
        if proof:
            proof.approval_status = 'Approved'
            proof.comments = None
            
        db.session.commit()
        flash('Task completion successfully approved.', 'success')
        return redirect(url_for('manager_dashboard'))

    # Action: Reject Task (Manager only)
    @app.route('/task/reject/<int:task_id>', methods=['POST'])
    @login_required
    def reject_task(task_id):
        if current_user.role != 'Manager':
            return jsonify({'success': False, 'message': 'Access denied.'}), 403
            
        task = Task.query.get_or_404(task_id)
        proof = TaskProof.query.filter_by(task_id=task.id).first()
        comment = request.form.get('comment', 'Requirements not fully met.')
        
        task.status = 'Rejected' # Resets status back to Rejected (Employee sees feedback and can re-upload after photos)
        if proof:
            proof.approval_status = 'Rejected'
            proof.comments = comment
            
        db.session.commit()
        flash('Task rejected. Feedback has been sent to the employee.', 'warning')
        return redirect(url_for('manager_dashboard'))

    # JSON Endpoint: Performance Reports (Admin, HOD, and Manager)
    @app.route('/api/reports-data')
    @login_required
    def reports_data():
        if current_user.role not in ['Admin', 'HOD', 'Manager']:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Get tasks counts grouped by status
        statuses = db.session.query(Task.status, db.func.count(Task.id)).group_by(Task.status).all()
        status_counts = {s[0]: s[1] for s in statuses}
        
        # Performance by Department
        # Summing tasks by user departments
        tasks = Task.query.all()
        dept_data = {}
        for t in tasks:
            dept = t.assignee.department if t.assignee else 'Unassigned'
            if dept not in dept_data:
                dept_data[dept] = {'total': 0, 'completed': 0, 'pending': 0}
            dept_data[dept]['total'] += 1
            if t.status in ['Completed', 'Approved']:
                dept_data[dept]['completed'] += 1
            else:
                dept_data[dept]['pending'] += 1
                
        # SLA Overview and Average Resolution Time
        now = datetime.utcnow()
        met = 0
        breached = 0
        dept_durations = {}
        
        for t in tasks:
            proof = t.proofs[0] if t.proofs else None
            # SLA logic
            if t.status in ['Completed', 'Approved']:
                completion_time = proof.uploaded_at if (proof and proof.uploaded_at) else t.created_at
                if completion_time <= t.deadline:
                    met += 1
                else:
                    breached += 1
            else:
                if t.deadline < now:
                    breached += 1
                else:
                    met += 1
            
            # Avg resolution time logic
            if t.status in ['Completed', 'Approved'] and proof and proof.uploaded_at:
                hours = (proof.uploaded_at - t.created_at).total_seconds() / 3600.0
                dept = t.assignee.department if (t.assignee and t.assignee.department) else 'Unassigned'
                if dept not in dept_durations:
                    dept_durations[dept] = []
                dept_durations[dept].append(hours)
                
        dept_avg_resolution = {}
        for dept, hours_list in dept_durations.items():
            dept_avg_resolution[dept] = round(sum(hours_list) / len(hours_list), 1)

        # Performance by Employee (top 5 by completion rate)
        employees = User.query.filter_by(role='Employee').all()
        emp_list = []
        for emp in employees:
            total_emp_tasks = len(emp.tasks_assigned)
            if total_emp_tasks > 0:
                comp_emp_tasks = sum(1 for t in emp.tasks_assigned if t.status in ['Completed', 'Approved'])
                comp_rate = round((comp_emp_tasks / total_emp_tasks) * 100, 1)
                emp_list.append({
                    'name': emp.name,
                    'department': emp.department,
                    'total': total_emp_tasks,
                    'completed': comp_emp_tasks,
                    'rate': comp_rate
                })
        
        # Sort employees by completion rate desc
        emp_list = sorted(emp_list, key=lambda x: x['rate'], reverse=True)[:5]
        
        return jsonify({
            'status_overview': {
                'Pending': status_counts.get('Pending', 0),
                'InProgress': status_counts.get('In Progress', 0),
                'Completed': status_counts.get('Completed', 0),
                'Approved': status_counts.get('Approved', 0),
                'Rejected': status_counts.get('Rejected', 0),
            },
            'department_performance': dept_data,
            'employee_leaderboard': emp_list,
            'sla_overview': {
                'Met': met,
                'Breached': breached
            },
            'dept_avg_resolution': dept_avg_resolution
        })

    @app.after_request
    def add_header(response):
        # Disable caching for all responses in development
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
