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

class PlatformEvaluation(db.Model):
    __tablename__ = 'platform_evaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Avaliações gerais (escala 1-5)
    design_rating = db.Column(db.Integer, nullable=False)
    colors_rating = db.Column(db.Integer, nullable=False)
    layout_rating = db.Column(db.Integer, nullable=False)
    responsiveness_rating = db.Column(db.Integer, nullable=False)
    
    # Navegação e Usabilidade
    navigation_rating = db.Column(db.Integer, nullable=False)
    menus_rating = db.Column(db.Integer, nullable=False)
    loading_speed_rating = db.Column(db.Integer, nullable=False)
    instructions_rating = db.Column(db.Integer, nullable=False)
    
    # Funcionalidades
    registration_rating = db.Column(db.Integer, nullable=False)
    login_rating = db.Column(db.Integer, nullable=False)
    class_enrollment_rating = db.Column(db.Integer, nullable=False)
    exam_taking_rating = db.Column(db.Integer, nullable=False)
    results_rating = db.Column(db.Integer, nullable=False)
    
    # Experiência específica
    registration_ease = db.Column(db.String(20), nullable=False)  # very_easy, easy, regular, difficult, very_difficult
    registration_problems = db.Column(db.Text)
    login_intuitive = db.Column(db.Boolean, nullable=False)
    login_comments = db.Column(db.Text)
    
    # Navegação na turma
    class_finding_easy = db.Column(db.Boolean, nullable=False)
    class_finding_comments = db.Column(db.Text)
    class_process_clear = db.Column(db.Boolean, nullable=False)
    class_process_comments = db.Column(db.Text)
    
    # Realização da prova
    exam_instructions_clear = db.Column(db.Boolean, nullable=False)
    exam_instructions_comments = db.Column(db.Text)
    timer_visible = db.Column(db.Boolean, nullable=False)
    timer_comments = db.Column(db.Text)
    question_navigation_easy = db.Column(db.Boolean, nullable=False)
    question_navigation_comments = db.Column(db.Text)
    answer_area_adequate = db.Column(db.Boolean, nullable=False)
    answer_area_comments = db.Column(db.Text)
    exam_finish_difficulty = db.Column(db.Boolean, nullable=False)
    exam_finish_comments = db.Column(db.Text)
    
    # Resultados
    results_clear = db.Column(db.Boolean, nullable=False)
    results_comments = db.Column(db.Text)
    essay_feedback_useful = db.Column(db.Boolean)
    essay_feedback_comments = db.Column(db.Text)
    
    # Problemas encontrados
    technical_errors = db.Column(db.Boolean, nullable=False)
    technical_errors_description = db.Column(db.Text)
    functionality_issues = db.Column(db.Boolean, nullable=False)
    functionality_issues_description = db.Column(db.Text)
    
    # Dificuldades de uso
    confusion_moments = db.Column(db.Boolean, nullable=False)
    confusion_description = db.Column(db.Text)
    missing_features = db.Column(db.Boolean, nullable=False)
    missing_features_description = db.Column(db.Text)
    
    # Sugestões
    platform_changes = db.Column(db.Text)
    desired_features = db.Column(db.Text)
    ux_suggestions = db.Column(db.Text)
    
    # Avaliação final
    recommendation = db.Column(db.String(30), nullable=False)  # definitely_yes, probably_yes, maybe, probably_no, definitely_no
    general_impression = db.Column(db.String(20), nullable=False)  # excellent, good, regular, bad, very_bad
    additional_comments = db.Column(db.Text)
    
    # Informações técnicas
    device_type = db.Column(db.String(20), nullable=False)  # desktop, tablet, smartphone
    browser = db.Column(db.String(50), nullable=False)
    operating_system = db.Column(db.String(50), nullable=False)
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com usuário
    user = db.relationship('User', backref='platform_evaluations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'user_role': self.user.role if self.user else None,
            
            # Avaliações gerais
            'design_rating': self.design_rating,
            'colors_rating': self.colors_rating,
            'layout_rating': self.layout_rating,
            'responsiveness_rating': self.responsiveness_rating,
            
            # Navegação e Usabilidade
            'navigation_rating': self.navigation_rating,
            'menus_rating': self.menus_rating,
            'loading_speed_rating': self.loading_speed_rating,
            'instructions_rating': self.instructions_rating,
            
            # Funcionalidades
            'registration_rating': self.registration_rating,
            'login_rating': self.login_rating,
            'class_enrollment_rating': self.class_enrollment_rating,
            'exam_taking_rating': self.exam_taking_rating,
            'results_rating': self.results_rating,
            
            # Experiência específica
            'registration_ease': self.registration_ease,
            'registration_problems': self.registration_problems,
            'login_intuitive': self.login_intuitive,
            'login_comments': self.login_comments,
            
            # Navegação na turma
            'class_finding_easy': self.class_finding_easy,
            'class_finding_comments': self.class_finding_comments,
            'class_process_clear': self.class_process_clear,
            'class_process_comments': self.class_process_comments,
            
            # Realização da prova
            'exam_instructions_clear': self.exam_instructions_clear,
            'exam_instructions_comments': self.exam_instructions_comments,
            'timer_visible': self.timer_visible,
            'timer_comments': self.timer_comments,
            'question_navigation_easy': self.question_navigation_easy,
            'question_navigation_comments': self.question_navigation_comments,
            'answer_area_adequate': self.answer_area_adequate,
            'answer_area_comments': self.answer_area_comments,
            'exam_finish_difficulty': self.exam_finish_difficulty,
            'exam_finish_comments': self.exam_finish_comments,
            
            # Resultados
            'results_clear': self.results_clear,
            'results_comments': self.results_comments,
            'essay_feedback_useful': self.essay_feedback_useful,
            'essay_feedback_comments': self.essay_feedback_comments,
            
            # Problemas
            'technical_errors': self.technical_errors,
            'technical_errors_description': self.technical_errors_description,
            'functionality_issues': self.functionality_issues,
            'functionality_issues_description': self.functionality_issues_description,
            
            # Dificuldades
            'confusion_moments': self.confusion_moments,
            'confusion_description': self.confusion_description,
            'missing_features': self.missing_features,
            'missing_features_description': self.missing_features_description,
            
            # Sugestões
            'platform_changes': self.platform_changes,
            'desired_features': self.desired_features,
            'ux_suggestions': self.ux_suggestions,
            
            # Avaliação final
            'recommendation': self.recommendation,
            'general_impression': self.general_impression,
            'additional_comments': self.additional_comments,
            
            # Informações técnicas
            'device_type': self.device_type,
            'browser': self.browser,
            'operating_system': self.operating_system,
            
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 