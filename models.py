from datetime import datetime

from database import db


class Class(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    schedule = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    exams = db.relationship('Exam', backref='class_ref', lazy=True)
    enrollments = db.relationship('ClassEnrollment', backref='class_ref', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'instructor_id': self.instructor_id,
            'schedule': self.schedule,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }


class ClassEnrollment(db.Model):
    __tablename__ = 'class_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'class_id': self.class_id,
            'student_id': self.student_id,
            'status': self.status,
            'enrolled_at': self.enrolled_at.isoformat()
        }


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

class Exam(db.Model):
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='draft')

    questions = db.relationship('Question', backref='exam', lazy=True)
    enrollments = db.relationship('ExamEnrollment', backref='exam', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'created_by': self.created_by,
            'class_id': self.class_id,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=True)  # Agora pode ser null
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Novo campo
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # multiple_choice, single_choice, true_false, essay
    points = db.Column(db.Numeric(5,2), nullable=False, default=1.0)
    order_number = db.Column(db.Integer, nullable=True)  # Pode ser null para questões do banco
    category = db.Column(db.String(100))  # Novo campo para categorizar questões
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    is_public = db.Column(db.Boolean, default=True)  # Novo campo para visibilidade
    expected_answer = db.Column(db.Text)  # Campo para resposta esperada (gabarito do professor) para questões dissertativas
    auto_correction_enabled = db.Column(db.Boolean, default=False)  # Campo para habilitar correção automática
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    alternatives = db.relationship('Alternative', backref='question', lazy=True)
    answers = db.relationship('Answer', backref='question', lazy=True)
    exam_questions = db.relationship('ExamQuestion', backref='question', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'created_by': self.created_by,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'points': float(self.points),
            'order_number': self.order_number,
            'category': self.category,
            'difficulty': self.difficulty,
            'is_public': self.is_public,
            'expected_answer': self.expected_answer,
            'auto_correction_enabled': self.auto_correction_enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'alternatives': [alt.to_dict() for alt in self.alternatives]
        }

class Alternative(db.Model):
    __tablename__ = 'alternatives'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    alternative_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    order_number = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'question_id': self.question_id,
            'alternative_text': self.alternative_text,
            'is_correct': self.is_correct,
            'order_number': self.order_number
        }

class ExamEnrollment(db.Model):
    __tablename__ = 'exam_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(50), default='pending')
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    total_points = db.Column(db.Numeric(5,2), default=0)  # Pontuação obtida pelo estudante
    max_points = db.Column(db.Numeric(5,2), default=0)    # Pontuação máxima possível da prova
    percentage = db.Column(db.Numeric(5,2), default=0)    # Percentual de acerto
    completed_at = db.Column(db.DateTime)  # Data/hora de finalização da prova
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    answers = db.relationship('Answer', backref='enrollment', lazy=True)
    monitoring_events = db.relationship('MonitoringEvent', backref='enrollment', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'student_id': self.student_id,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_points': float(self.total_points) if self.total_points else 0,
            'max_points': float(self.max_points) if self.max_points else 0,
            'percentage': float(self.percentage) if self.percentage else 0,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat()
        }

class Answer(db.Model):
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('exam_enrollments.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    answer_text = db.Column(db.Text)
    selected_alternatives = db.Column(db.JSON)  # Array de IDs das alternativas selecionadas
    points_earned = db.Column(db.Numeric(5,2))
    similarity_score = db.Column(db.Numeric(5,2))  # Campo para armazenar o score de similaridade da correção automática
    correction_method = db.Column(db.String(50))  # Campo para armazenar o método de correção usado (manual, auto, etc.)
    feedback = db.Column(db.Text)  # Campo para feedback do professor na correção manual
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'enrollment_id': self.enrollment_id,
            'question_id': self.question_id,
            'answer_text': self.answer_text,
            'selected_alternatives': self.selected_alternatives,
            'points_earned': float(self.points_earned) if self.points_earned else None,
            'similarity_score': float(self.similarity_score) if self.similarity_score else None,
            'correction_method': self.correction_method,
            'feedback': self.feedback,
            'created_at': self.created_at.isoformat()
        }

class MonitoringEvent(db.Model):
    __tablename__ = 'monitoring_events'
    
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('exam_enrollments.id'))
    event_type = db.Column(db.String(50), nullable=False)
    event_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'enrollment_id': self.enrollment_id,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'created_at': self.created_at.isoformat()
        }

class ExamQuestion(db.Model):
    __tablename__ = 'exam_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    points = db.Column(db.Numeric(5,2), nullable=False)  # Pontuação específica para esta prova
    order_number = db.Column(db.Integer, nullable=False)
    question_snapshot = db.Column(db.JSON)  # Snapshot da questão no momento da criação da prova
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'question_id': self.question_id,
            'points': float(self.points),
            'order_number': self.order_number,
            'question_snapshot': self.question_snapshot,
            'created_at': self.created_at.isoformat()
        } 

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # exam_reminder, result_available, suspicious_activity, etc.
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    data = db.Column(db.JSON)  # Dados adicionais específicos do tipo de notificação
    is_read = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)

    # Relacionamento com usuário
    user = db.relationship('User', backref='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None
        } 