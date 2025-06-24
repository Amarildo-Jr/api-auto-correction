from datetime import datetime

from database import db
from flask import jsonify, request
from flask_jwt_extended import (create_access_token, get_jwt_identity,
                                jwt_required)
from models import (Alternative, Answer, Class, ClassEnrollment, Exam,
                    ExamEnrollment, ExamQuestion, MonitoringEvent, Question,
                    User)
from werkzeug.security import check_password_hash, generate_password_hash


def register_routes(app):
    # Rotas de Autenticação
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            user = User.query.filter_by(email=data['email']).first()
            
            if user and check_password_hash(user.password_hash, data['password']):
                user_id = str(user.id)
                access_token = create_access_token(identity=user_id)
                return jsonify({'token': access_token, 'user': user.to_dict()}), 200
            
            return jsonify({'message': 'Credenciais inválidas'}), 401
        except Exception as e:
            return jsonify({'message': 'Erro no login', 'error': str(e)}), 500

    # Rotas de Usuário
    @app.route('/api/users', methods=['POST'])
    @jwt_required()
    def create_user():
        data = request.get_json()
        new_user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            name=data['name'],
            role=data['role']
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201

    @app.route('/api/users/me', methods=['GET'])
    @jwt_required()
    def get_current_user():
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        return jsonify(user.to_dict()), 200

    # Rotas de Provas
    @app.route('/api/exams', methods=['GET'])
    @jwt_required()
    def list_exams():
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            if user.role == 'student':
                student_classes = ClassEnrollment.query.filter_by(student_id=user_id).all()
                class_ids = [enrollment.class_id for enrollment in student_classes]
                exams = Exam.query.filter(
                    Exam.class_id.in_(class_ids),
                    Exam.status == 'published'
                ).all()
            else:
                exams = Exam.query.filter_by(created_by=user_id).all()
            
            return jsonify([exam.to_dict() for exam in exams]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/exams', methods=['POST'])
    @jwt_required()
    def create_exam():
        try:
            data = request.get_json()
            
            # Converter strings de data para datetime
            start_time_str = data['start_time']
            end_time_str = data['end_time']
            
            # Se não tem timezone, assumir que é local
            if 'T' in start_time_str and '+' not in start_time_str and 'Z' not in start_time_str:
                start_time = datetime.fromisoformat(start_time_str)
            else:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                
            if 'T' in end_time_str and '+' not in end_time_str and 'Z' not in end_time_str:
                end_time = datetime.fromisoformat(end_time_str)
            else:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            
            new_exam = Exam(
                title=data['title'],
                description=data['description'],
                duration_minutes=data['duration_minutes'],
                start_time=start_time,
                end_time=end_time,
                created_by=get_jwt_identity(),
                class_id=data.get('class_id')
            )
            db.session.add(new_exam)
            db.session.commit()
            return jsonify(new_exam.to_dict()), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/exams/<int:exam_id>', methods=['GET'])
    @jwt_required()
    def get_exam(exam_id):
        try:
            exam = Exam.query.get_or_404(exam_id)
            exam_dict = exam.to_dict()
            
            # Carregar questões da prova através da tabela exam_questions
            exam_questions = db.session.query(ExamQuestion, Question)\
                .join(Question, ExamQuestion.question_id == Question.id)\
                .filter(ExamQuestion.exam_id == exam_id)\
                .order_by(ExamQuestion.order_number)\
                .all()
            
            questions_data = []
            for exam_question, question in exam_questions:
                question_dict = question.to_dict()
                # Usar a pontuação específica da prova
                question_dict['points'] = float(exam_question.points)
                question_dict['order_number'] = exam_question.order_number
                questions_data.append(question_dict)
            
            exam_dict['questions'] = questions_data
            
            return jsonify(exam_dict), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/exams/<int:exam_id>', methods=['PUT'])
    @jwt_required()
    def update_exam(exam_id):
        try:
            user_id = get_jwt_identity()
            exam = Exam.query.get_or_404(exam_id)
            
            # Verificar se o usuário tem permissão para editar
            if exam.created_by != int(user_id):
                return jsonify({'error': 'Sem permissão para editar esta prova'}), 403
            
            data = request.get_json()
            
            # Atualizar campos básicos
            if 'title' in data:
                exam.title = data['title']
            if 'description' in data:
                exam.description = data['description']
            if 'duration_minutes' in data:
                exam.duration_minutes = data['duration_minutes']
            if 'class_id' in data:
                exam.class_id = data['class_id']
            
            # Atualizar datas se fornecidas
            if 'start_time' in data:
                start_time_str = data['start_time']
                if 'T' in start_time_str and '+' not in start_time_str and 'Z' not in start_time_str:
                    exam.start_time = datetime.fromisoformat(start_time_str)
                else:
                    exam.start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            
            if 'end_time' in data:
                end_time_str = data['end_time']
                if 'T' in end_time_str and '+' not in end_time_str and 'Z' not in end_time_str:
                    exam.end_time = datetime.fromisoformat(end_time_str)
                else:
                    exam.end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            
            # Gerenciar questões se fornecidas
            if 'questions' in data and 'question_points' in data:
                # Remover todas as questões antigas da prova
                ExamQuestion.query.filter_by(exam_id=exam_id).delete()
                
                # Adicionar novas questões com pontuação personalizada
                questions_data = data['questions']
                question_points = data['question_points']
                
                for i, question_id in enumerate(questions_data):
                    question = Question.query.get(question_id)
                    if question:
                        # Criar snapshot da questão
                        question_snapshot = {
                            'question_text': question.question_text,
                            'question_type': question.question_type,
                            'alternatives': [alt.to_dict() for alt in question.alternatives]
                        }
                        
                        # Usar pontuação personalizada ou padrão
                        points = question_points.get(str(question_id), question.points)
                        
                        exam_question = ExamQuestion(
                            exam_id=exam_id,
                            question_id=question_id,
                            points=points,
                            order_number=i + 1,
                            question_snapshot=question_snapshot
                        )
                        db.session.add(exam_question)
            
            db.session.commit()
            
            # Retornar prova atualizada com questões
            exam_dict = exam.to_dict()
            exam_questions = db.session.query(ExamQuestion, Question)\
                .join(Question, ExamQuestion.question_id == Question.id)\
                .filter(ExamQuestion.exam_id == exam_id)\
                .order_by(ExamQuestion.order_number)\
                .all()
            
            questions_data = []
            for exam_question, question in exam_questions:
                question_dict = question.to_dict()
                question_dict['points'] = float(exam_question.points)
                question_dict['order_number'] = exam_question.order_number
                questions_data.append(question_dict)
            
            exam_dict['questions'] = questions_data
            
            return jsonify(exam_dict), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/exams/<int:exam_id>/questions', methods=['POST'])
    @jwt_required()
    def add_question(exam_id):
        data = request.get_json()
        new_question = Question(
            exam_id=exam_id,
            question_text=data['question_text'],
            question_type=data['question_type'],
            points=data['points'],
            order_number=data['order_number']
        )
        db.session.add(new_question)
        db.session.commit()

        # Se for questão de múltipla escolha, adicionar alternativas
        if data['question_type'] == 'multiple_choice' and 'alternatives' in data:
            for alt_data in data['alternatives']:
                alternative = Alternative(
                    question_id=new_question.id,
                    alternative_text=alt_data['text'],
                    is_correct=alt_data['is_correct'],
                    order_number=alt_data['order_number']
                )
                db.session.add(alternative)
            db.session.commit()

        return jsonify(new_question.to_dict()), 201

    # Rotas de Realização de Provas
    @app.route('/api/exams/<int:exam_id>/enrollment-status', methods=['GET'])
    @jwt_required()
    def get_enrollment_status(exam_id):
        student_id = get_jwt_identity()
        
        enrollment = ExamEnrollment.query.filter_by(
            exam_id=exam_id,
            student_id=student_id
        ).first()
        
        if enrollment:
            # Carregar respostas existentes se estiver em andamento
            if enrollment.status == 'in_progress':
                answers = Answer.query.filter_by(enrollment_id=enrollment.id).all()
                enrollment_data = enrollment.to_dict()
                enrollment_data['existing_answers'] = [answer.to_dict() for answer in answers]
                return jsonify(enrollment_data), 200
            else:
                return jsonify(enrollment.to_dict()), 200
        else:
            return jsonify({'status': 'not_enrolled'}), 200

    @app.route('/api/exams/<int:exam_id>/start', methods=['POST'])
    @jwt_required()
    def start_exam(exam_id):
        student_id = get_jwt_identity()
        
        # Verificar se já existe uma inscrição
        enrollment = ExamEnrollment.query.filter_by(
            exam_id=exam_id,
            student_id=student_id
        ).first()
        
        if enrollment:
            if enrollment.status == 'completed':
                return jsonify({'message': 'Prova já foi finalizada'}), 400
            elif enrollment.status == 'in_progress':
                # Permitir continuar prova em andamento
                # Carregar respostas existentes
                answers = Answer.query.filter_by(enrollment_id=enrollment.id).all()
                enrollment_data = enrollment.to_dict()
                enrollment_data['existing_answers'] = [answer.to_dict() for answer in answers]
                return jsonify(enrollment_data), 200
        else:
            enrollment = ExamEnrollment(
                exam_id=exam_id,
                student_id=student_id
            )
            db.session.add(enrollment)
        
        enrollment.status = 'in_progress'
        if not enrollment.start_time:  # Só definir start_time se ainda não foi definido
            enrollment.start_time = datetime.utcnow()
        db.session.commit()
        
        return jsonify(enrollment.to_dict()), 200

    @app.route('/api/enrollments/<int:enrollment_id>/submit-answer', methods=['POST'])
    @jwt_required()
    def submit_answer(enrollment_id):
        try:
            data = request.get_json()
            enrollment = ExamEnrollment.query.get_or_404(enrollment_id)
            
            if enrollment.status != 'in_progress':
                return jsonify({'message': 'Prova não está em andamento'}), 400
            
            # Verificar se já existe uma resposta para esta questão
            existing_answer = Answer.query.filter_by(
                enrollment_id=enrollment_id,
                question_id=data['question_id']
            ).first()
            
            # Preparar dados das alternativas selecionadas
            selected_alternatives = data.get('selected_alternatives', [])
            if not isinstance(selected_alternatives, list):
                selected_alternatives = [selected_alternatives] if selected_alternatives else []
            
            if existing_answer:
                existing_answer.answer_text = data.get('answer_text')
                existing_answer.selected_alternatives = selected_alternatives
            else:
                new_answer = Answer(
                    enrollment_id=enrollment_id,
                    question_id=data['question_id'],
                    answer_text=data.get('answer_text'),
                    selected_alternatives=selected_alternatives
                )
                db.session.add(new_answer)
            
            db.session.commit()
            return jsonify({'message': 'Resposta salva com sucesso'}), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/enrollments/<int:enrollment_id>/finish', methods=['POST'])
    @jwt_required()
    def finish_exam(enrollment_id):
        try:
            enrollment = ExamEnrollment.query.get_or_404(enrollment_id)
            
            if enrollment.status != 'in_progress':
                return jsonify({'message': 'Prova não está em andamento'}), 400
            
            enrollment.status = 'completed'
            enrollment.end_time = datetime.utcnow()
            
            # Corrigir questões objetivas automaticamente usando pontuação da tabela exam_questions
            answers = Answer.query.filter_by(enrollment_id=enrollment_id).all()
            total_points = 0.0
            
            for answer in answers:
                # Buscar questão e sua pontuação específica na prova
                exam_question = ExamQuestion.query.filter_by(
                    exam_id=enrollment.exam_id,
                    question_id=answer.question_id
                ).first()
                
                if not exam_question:
                    answer.points_earned = 0.0
                    continue
                
                question = Question.query.get(answer.question_id)
                if not question:
                    answer.points_earned = 0.0
                    continue
                
                # Questões dissertativas: tentar correção automática se habilitada
                if question.question_type == 'essay':
                    print(f"🔍 Processando questão dissertativa ID: {question.id}")
                    print(f"   - auto_correction_enabled: {question.auto_correction_enabled}")
                    print(f"   - expected_answer existe: {bool(question.expected_answer)}")
                    print(f"   - answer_text existe: {bool(answer.answer_text)}")
                    
                    if question.auto_correction_enabled and question.expected_answer and answer.answer_text:
                        # Importação local para evitar problemas de dependências não instaladas
                        try:
                            from auto_correction import auto_correction
                            print(f"   - Tentando correção automática...")
                            points_earned, similarity_score = auto_correction.auto_correct_essay(
                                question.expected_answer, 
                                answer.answer_text, 
                                float(exam_question.points)
                            )
                            
                            if points_earned is not None:
                                answer.points_earned = points_earned
                                answer.similarity_score = similarity_score
                                answer.correction_method = 'auto'
                                print(f"   - ✅ Correção automática: {points_earned} pontos (similaridade: {similarity_score})")
                            else:
                                answer.points_earned = None  # Pendente de correção manual
                                answer.correction_method = 'pending'
                                print(f"   - ⏳ Correção automática retornou None - ficou pendente")
                        except ImportError as e:
                            # Se não conseguir importar o módulo de correção automática
                            answer.points_earned = None
                            answer.correction_method = 'pending'
                            print(f"   - ❌ Erro de importação: {e}")
                        except Exception as e:
                            # Qualquer outro erro na correção automática
                            answer.points_earned = None
                            answer.correction_method = 'pending'
                            print(f"   - ❌ Erro na correção automática: {e}")
                    else:
                        answer.points_earned = None  # Pendente de correção manual
                        answer.correction_method = 'pending'
                        print(f"   - ⏳ Condições não atendidas - ficou pendente")
                    
                    # Se não foi corrigida automaticamente, não incluir na pontuação total
                    if answer.points_earned is None:
                        continue
                
                # Para questões objetivas, verificar se há resposta
                if not answer.selected_alternatives:
                    answer.points_earned = 0.0
                    continue
                
                # Garantir que selected_alternatives seja uma lista de inteiros
                selected_alternatives = []
                if answer.selected_alternatives:
                    if isinstance(answer.selected_alternatives, list):
                        selected_alternatives = [int(alt) for alt in answer.selected_alternatives if alt is not None]
                    elif isinstance(answer.selected_alternatives, str):
                        try:
                            import json
                            parsed = json.loads(answer.selected_alternatives)
                            selected_alternatives = [int(alt) for alt in parsed if alt is not None]
                        except:
                            selected_alternatives = []
                
                points_for_question = float(exam_question.points)
                
                if question.question_type in ['single_choice', 'true_false']:
                    # Para escolha única e V/F, deve ter exatamente uma alternativa correta selecionada
                    if len(selected_alternatives) == 1:
                        alternative = Alternative.query.get(selected_alternatives[0])
                        if alternative and alternative.is_correct:
                            answer.points_earned = points_for_question
                        else:
                            answer.points_earned = 0.0
                    else:
                        answer.points_earned = 0.0
                        
                elif question.question_type == 'multiple_choice':
                    # Para múltipla escolha, implementar pontuação baseada em acertos líquidos
                    correct_alternatives = Alternative.query.filter_by(question_id=question.id, is_correct=True).all()
                    all_alternatives = Alternative.query.filter_by(question_id=question.id).all()
                    
                    correct_ids = {alt.id for alt in correct_alternatives}
                    selected_ids = set(selected_alternatives)
                    
                    # Calcular acertos e erros
                    correct_selected = len(correct_ids.intersection(selected_ids))  # Corretas selecionadas
                    incorrect_selected = len(selected_ids - correct_ids)  # Incorretas selecionadas
                    total_correct = len(correct_ids)  # Total de corretas
                    
                    if total_correct > 0:
                        # Acertos líquidos = corretas_selecionadas - incorretas_selecionadas
                        net_correct = correct_selected - incorrect_selected
                        
                        if net_correct > 0:
                            # Pontuação proporcional aos acertos líquidos
                            score_ratio = net_correct / total_correct
                            answer.points_earned = points_for_question * score_ratio
                        else:
                            # Se erros >= acertos, pontuação zero
                            answer.points_earned = 0.0
                    else:
                        answer.points_earned = 0.0
                else:
                    # Tipo de questão desconhecido
                    answer.points_earned = 0.0
                
                # Somar pontos apenas das questões já corrigidas (objetivas)
                if answer.points_earned is not None:
                    total_points += answer.points_earned
            
            # Calcular pontuação máxima possível da prova
            max_points_result = db.session.query(
                db.func.sum(ExamQuestion.points)
            ).filter(ExamQuestion.exam_id == enrollment.exam_id).scalar()
            
            max_points = float(max_points_result) if max_points_result else 0.0
            
            # Calcular percentual
            percentage = (total_points / max_points * 100) if max_points > 0 else 0.0
            
            # Salvar resultados finais no enrollment
            enrollment.total_points = total_points
            enrollment.max_points = max_points
            enrollment.percentage = percentage
            enrollment.completed_at = datetime.utcnow()
            
            db.session.commit()
            
            # Retornar resultado com pontuação
            result = enrollment.to_dict()
            result['answers_count'] = len(answers)
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    # Rotas de Monitoramento
    @app.route('/api/monitoring/event', methods=['POST'])
    @jwt_required()
    def record_monitoring_event():
        data = request.get_json()
        new_event = MonitoringEvent(
            enrollment_id=data['enrollment_id'],
            event_type=data['event_type'],
            event_data=data['event_data']
        )
        db.session.add(new_event)
        db.session.commit()
        return jsonify(new_event.to_dict()), 201

    # Rotas de Turmas
    @app.route('/api/classes', methods=['GET'])
    @jwt_required()
    def list_classes():
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            if user.role == 'student':
                enrollments = ClassEnrollment.query.filter_by(student_id=user_id).all()
                class_ids = [enrollment.class_id for enrollment in enrollments]
                classes = Class.query.filter(Class.id.in_(class_ids)).all()
            else:
                if user.role == 'admin':
                    classes = Class.query.all()
                else:
                    classes = Class.query.filter_by(instructor_id=user_id).all()
            
            # Para professores e admins, adicionar contadores de alunos e solicitações
            classes_with_stats = []
            for class_obj in classes:
                class_data = class_obj.to_dict()
                
                if user.role in ['admin', 'professor']:
                    # Contar alunos com desempenho satisfatório
                    student_count = ClassEnrollment.query.filter_by(
                        class_id=class_obj.id,
                        status='approved'
                    ).count()
                    
                    # Contar solicitações pendentes
                    pending_requests = ClassEnrollment.query.filter_by(
                        class_id=class_obj.id,
                        status='pending'
                    ).count()
                    
                    class_data['student_count'] = student_count
                    class_data['pending_requests'] = pending_requests
                
                classes_with_stats.append(class_data)
            
            return jsonify(classes_with_stats), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/classes/available', methods=['GET'])
    @jwt_required()
    def list_available_classes():
        """Lista turmas disponíveis para estudantes se matricularem"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            if user.role != 'student':
                return jsonify({'error': 'Apenas estudantes podem ver turmas disponíveis'}), 403
            
            # Buscar turmas onde o estudante ainda não está matriculado
            enrolled_classes = ClassEnrollment.query.filter_by(student_id=user_id).all()
            enrolled_class_ids = [enrollment.class_id for enrollment in enrolled_classes]
            
            available_classes = Class.query.filter(
                Class.is_active == True,
                ~Class.id.in_(enrolled_class_ids)
            ).all()
            
            classes_with_instructor = []
            for class_obj in available_classes:
                class_data = class_obj.to_dict()
                instructor = User.query.get(class_obj.instructor_id)
                if instructor:
                    class_data['instructor_name'] = instructor.name
                classes_with_instructor.append(class_data)
            
            return jsonify(classes_with_instructor), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/classes', methods=['POST'])
    @jwt_required()
    def create_class():
        try:
            data = request.get_json()
            new_class = Class(
                name=data['name'],
                description=data.get('description'),
                instructor_id=get_jwt_identity(),
                schedule=data.get('schedule'),
                is_active=data.get('is_active', True)
            )
            db.session.add(new_class)
            db.session.commit()
            return jsonify(new_class.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/classes/<int:class_id>', methods=['GET'])
    @jwt_required()
    def get_class(class_id):
        class_obj = Class.query.get_or_404(class_id)
        return jsonify(class_obj.to_dict()), 200

    @app.route('/api/classes/<int:class_id>', methods=['PUT'])
    @jwt_required()
    def update_class(class_id):
        """Atualizar dados de uma turma"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            class_obj = Class.query.get_or_404(class_id)
            
            # Verificar se é o professor da turma ou admin
            if user.role != 'admin' and class_obj.instructor_id != int(user_id):
                return jsonify({'error': 'Apenas o professor da turma ou admin pode editá-la'}), 403
            
            data = request.get_json()
            
            # Atualizar campos permitidos
            if 'name' in data:
                class_obj.name = data['name']
            if 'description' in data:
                class_obj.description = data['description']
            if 'schedule' in data:
                class_obj.schedule = data['schedule']
            if 'is_active' in data:
                class_obj.is_active = data['is_active']
            
            db.session.commit()
            
            # Retornar dados atualizados com estatísticas
            class_data = class_obj.to_dict()
            if user.role in ['admin', 'professor']:
                student_count = ClassEnrollment.query.filter_by(
                    class_id=class_obj.id,
                    status='approved'
                ).count()
                
                pending_requests = ClassEnrollment.query.filter_by(
                    class_id=class_obj.id,
                    status='pending'
                ).count()
                
                class_data['student_count'] = student_count
                class_data['pending_requests'] = pending_requests
            
            return jsonify(class_data), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/classes/<int:class_id>', methods=['DELETE'])
    @jwt_required()
    def delete_class(class_id):
        """Excluir uma turma"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            class_obj = Class.query.get_or_404(class_id)
            
            # Verificar se é o professor da turma ou admin
            if user.role != 'admin' and class_obj.instructor_id != int(user_id):
                return jsonify({'error': 'Apenas o professor da turma ou admin pode excluí-la'}), 403
            
            # Verificar se há estudantes matriculados
            enrolled_students = ClassEnrollment.query.filter_by(
                class_id=class_id,
                status='approved'
            ).count()
            
            if enrolled_students > 0:
                return jsonify({'error': 'Não é possível excluir turma com estudantes matriculados'}), 400
            
            # Verificar se há provas associadas
            exams_count = Exam.query.filter_by(class_id=class_id).count()
            if exams_count > 0:
                return jsonify({'error': 'Não é possível excluir turma com provas associadas'}), 400
            
            # Remover todas as matrículas (pendentes/rejeitadas)
            ClassEnrollment.query.filter_by(class_id=class_id).delete()
            
            # Remover a turma
            db.session.delete(class_obj)
            db.session.commit()
            
            return jsonify({'message': 'Turma excluída com sucesso'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/classes/<int:class_id>/request-enrollment', methods=['POST'])
    @jwt_required()
    def request_enrollment(class_id):
        """Solicitar participação em uma turma"""
        try:
            student_id = get_jwt_identity()
            user = User.query.get_or_404(student_id)
            
            if user.role != 'student':
                return jsonify({'error': 'Apenas estudantes podem solicitar participação'}), 403
            
            # Verificar se já existe solicitação
            existing_enrollment = ClassEnrollment.query.filter_by(
                class_id=class_id,
                student_id=student_id
            ).first()
            
            if existing_enrollment:
                if existing_enrollment.status == 'pending':
                    return jsonify({'message': 'Solicitação já enviada, aguardando aprovação'}), 400
                elif existing_enrollment.status == 'approved':
                    return jsonify({'message': 'Já matriculado nesta turma'}), 400
                else:  # rejected
                    existing_enrollment.status = 'pending'
                    db.session.commit()
                    return jsonify({'message': 'Nova solicitação enviada'}), 200
            
            enrollment = ClassEnrollment(
                class_id=class_id,
                student_id=student_id,
                status='pending'
            )
            db.session.add(enrollment)
            db.session.commit()
            
            return jsonify({'message': 'Solicitação de participação enviada com sucesso'}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/classes/<int:class_id>/enroll', methods=['POST'])
    @jwt_required()
    def enroll_in_class(class_id):
        """Rota para matrícula direta (compatibilidade)"""
        try:
            student_id = get_jwt_identity()
            
            # Verificar se já está matriculado
            existing_enrollment = ClassEnrollment.query.filter_by(
                class_id=class_id,
                student_id=student_id
            ).first()
            
            if existing_enrollment:
                if existing_enrollment.status == 'approved':
                    return jsonify({'message': 'Já matriculado nesta turma'}), 400
                else:
                    existing_enrollment.status = 'approved'
                    db.session.commit()
                    return jsonify(existing_enrollment.to_dict()), 200
            
            enrollment = ClassEnrollment(
                class_id=class_id,
                student_id=student_id,
                status='approved'
            )
            db.session.add(enrollment)
            db.session.commit()
            
            return jsonify(enrollment.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/classes/<int:class_id>/enrollment-requests', methods=['GET'])
    @jwt_required()
    def list_enrollment_requests(class_id):
        """Listar solicitações de participação pendentes"""
        try:
            user_id = get_jwt_identity()
            class_obj = Class.query.get_or_404(class_id)
            
            # Verificar se é o professor da turma
            if class_obj.instructor_id != int(user_id):
                return jsonify({'error': 'Apenas o professor da turma pode ver as solicitações'}), 403
            
            pending_enrollments = ClassEnrollment.query.filter_by(
                class_id=class_id,
                status='pending'
            ).all()
            
            requests = []
            for enrollment in pending_enrollments:
                student = User.query.get(enrollment.student_id)
                if student:
                    request_data = enrollment.to_dict()
                    request_data['student_name'] = student.name
                    request_data['student_email'] = student.email
                    requests.append(request_data)
            
            return jsonify(requests), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/classes/<int:class_id>/approve-enrollment/<int:enrollment_id>', methods=['POST'])
    @jwt_required()
    def approve_enrollment(class_id, enrollment_id):
        """Aprovar solicitação de participação"""
        try:
            user_id = get_jwt_identity()
            class_obj = Class.query.get_or_404(class_id)
            
            # Verificar se é o professor da turma
            if class_obj.instructor_id != int(user_id):
                return jsonify({'error': 'Apenas o professor da turma pode aprovar solicitações'}), 403
            
            enrollment = ClassEnrollment.query.get_or_404(enrollment_id)
            
            if enrollment.class_id != class_id:
                return jsonify({'error': 'Solicitação não pertence a esta turma'}), 400
            
            enrollment.status = 'approved'
            db.session.commit()
            
            return jsonify({'message': 'Solicitação aprovada com sucesso'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/classes/<int:class_id>/approve-all-enrollments', methods=['POST'])
    @jwt_required()
    def approve_all_enrollments(class_id):
        """Aprovar todas as solicitações de participação pendentes"""
        try:
            user_id = get_jwt_identity()
            class_obj = Class.query.get_or_404(class_id)
            
            # Verificar se é o professor da turma
            if class_obj.instructor_id != int(user_id):
                return jsonify({'error': 'Apenas o professor da turma pode aprovar solicitações'}), 403
            
            pending_enrollments = ClassEnrollment.query.filter_by(
                class_id=class_id,
                status='pending'
            ).all()
            
            approved_count = 0
            for enrollment in pending_enrollments:
                enrollment.status = 'approved'
                approved_count += 1
            
            db.session.commit()
            
            return jsonify({'message': f'{approved_count} solicitações aprovadas com sucesso'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/classes/<int:class_id>/reject-enrollment/<int:enrollment_id>', methods=['POST'])
    @jwt_required()
    def reject_enrollment(class_id, enrollment_id):
        """Rejeitar solicitação de participação"""
        try:
            user_id = get_jwt_identity()
            class_obj = Class.query.get_or_404(class_id)
            
            # Verificar se é o professor da turma
            if class_obj.instructor_id != int(user_id):
                return jsonify({'error': 'Apenas o professor da turma pode rejeitar solicitações'}), 403
            
            enrollment = ClassEnrollment.query.get_or_404(enrollment_id)
            
            if enrollment.class_id != class_id:
                return jsonify({'error': 'Solicitação não pertence a esta turma'}), 400
            
            enrollment.status = 'rejected'
            db.session.commit()
            
            return jsonify({'message': 'Solicitação rejeitada'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/classes/<int:class_id>/students', methods=['GET'])
    @jwt_required()
    def list_class_students(class_id):
        try:
            enrollments = ClassEnrollment.query.filter_by(
                class_id=class_id,
                status='approved'
            ).all()
            students = []
            for enrollment in enrollments:
                student = User.query.get(enrollment.student_id)
                if student:
                    student_data = student.to_dict()
                    student_data['enrolled_at'] = enrollment.enrolled_at.isoformat()
                    students.append(student_data)
            
            return jsonify(students), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    # Rotas de Questões do Banco
    @app.route('/api/questions', methods=['GET'])
    @jwt_required()
    def list_questions():
        """Listar questões do banco (não associadas a provas específicas)"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            if user.role == 'student':
                return jsonify({'error': 'Acesso negado'}), 403
            
            # Filtrar questões do banco considerando visibilidade
            if user.role == 'admin':
                questions = Question.query.filter(Question.exam_id.is_(None)).all()
            else:
                # Professor vê suas próprias questões + questões públicas de outros
                questions = Question.query.filter(
                    Question.exam_id.is_(None),
                    db.or_(
                        Question.created_by == int(user_id),
                        Question.is_public == True
                    )
                ).all()
            
            return jsonify([question.to_dict() for question in questions]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/questions', methods=['POST'])
    @jwt_required()
    def create_question():
        """Criar questão no banco"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            if user.role == 'student':
                return jsonify({'error': 'Apenas professores podem criar questões'}), 403
            
            data = request.get_json()
            
            # Validar tipo de questão
            valid_types = ['single_choice', 'multiple_choice', 'true_false', 'essay']
            if data['question_type'] not in valid_types:
                return jsonify({'error': 'Tipo de questão inválido'}), 400
            
            new_question = Question(
                created_by=user_id,
                question_text=data['question_text'],
                question_type=data['question_type'],
                points=data.get('points', 1.0),
                category=data.get('category'),
                difficulty=data.get('difficulty', 'medium'),
                is_public=data.get('is_public', True),
                expected_answer=data.get('expected_answer'),
                auto_correction_enabled=data.get('auto_correction_enabled', False)
            )
            db.session.add(new_question)
            db.session.commit()

            # Adicionar alternativas para questões objetivas
            if data['question_type'] in ['single_choice', 'multiple_choice', 'true_false'] and 'alternatives' in data:
                for i, alt_data in enumerate(data['alternatives']):
                    alternative = Alternative(
                        question_id=new_question.id,
                        alternative_text=alt_data['text'],
                        is_correct=alt_data['is_correct'],
                        order_number=i + 1
                    )
                    db.session.add(alternative)
                db.session.commit()

            return jsonify(new_question.to_dict()), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/questions/<int:question_id>', methods=['GET'])
    @jwt_required()
    def get_question(question_id):
        """Obter questão específica"""
        try:
            question = Question.query.get_or_404(question_id)
            return jsonify(question.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/questions/<int:question_id>', methods=['PUT'])
    @jwt_required()
    def update_question(question_id):
        """Atualizar questão"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            question = Question.query.get_or_404(question_id)
            
            # Verificar permissão
            if user.role != 'admin' and question.created_by != int(user_id):
                return jsonify({'error': 'Sem permissão para editar esta questão'}), 403
            
            data = request.get_json()
            
            # Atualizar campos
            if 'question_text' in data:
                question.question_text = data['question_text']
            if 'question_type' in data:
                question.question_type = data['question_type']
            if 'points' in data:
                question.points = data['points']
            if 'category' in data:
                question.category = data['category']
            if 'difficulty' in data:
                question.difficulty = data['difficulty']
            if 'expected_answer' in data:
                question.expected_answer = data['expected_answer']
            if 'auto_correction_enabled' in data:
                question.auto_correction_enabled = data['auto_correction_enabled']
            
            question.updated_at = datetime.utcnow()
            
            # Atualizar alternativas se fornecidas
            if 'alternatives' in data and question.question_type == 'multiple_choice':
                # Remover alternativas existentes
                Alternative.query.filter_by(question_id=question_id).delete()
                
                # Adicionar novas alternativas
                for i, alt_data in enumerate(data['alternatives']):
                    alternative = Alternative(
                        question_id=question_id,
                        alternative_text=alt_data['text'],
                        is_correct=alt_data['is_correct'],
                        order_number=i + 1
                    )
                    db.session.add(alternative)
            
            db.session.commit()
            return jsonify(question.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/questions/<int:question_id>', methods=['DELETE'])
    @jwt_required()
    def delete_question(question_id):
        """Excluir questão"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            question = Question.query.get_or_404(question_id)
            
            # Verificar permissão
            if user.role != 'admin' and question.created_by != int(user_id):
                return jsonify({'error': 'Sem permissão para excluir esta questão'}), 403
            
            # Verificar se a questão está sendo usada em alguma prova
            if question.exam_id:
                return jsonify({'error': 'Não é possível excluir questão que está em uso em uma prova'}), 400
            
            # Remover alternativas
            Alternative.query.filter_by(question_id=question_id).delete()
            
            # Remover questão
            db.session.delete(question)
            db.session.commit()
            
            return jsonify({'message': 'Questão excluída com sucesso'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/exams/<int:exam_id>/add-questions', methods=['POST'])
    @jwt_required()
    def add_questions_to_exam(exam_id):
        """Adicionar questões do banco para uma prova usando exam_questions"""
        try:
            user_id = get_jwt_identity()
            exam = Exam.query.get_or_404(exam_id)
            
            # Verificar se é o criador da prova
            if exam.created_by != int(user_id):
                return jsonify({'error': 'Apenas o criador da prova pode adicionar questões'}), 403
            
            data = request.get_json()
            question_ids = data.get('question_ids', [])
            question_points = data.get('question_points', {})
            
            if not question_ids:
                return jsonify({'error': 'Nenhuma questão selecionada'}), 400
            
            # Buscar questões do banco (questões independentes)
            questions = Question.query.filter(
                Question.id.in_(question_ids),
                Question.exam_id.is_(None)  # Apenas questões não vinculadas a provas específicas
            ).all()
            
            if len(questions) != len(question_ids):
                return jsonify({'error': 'Algumas questões não foram encontradas ou já estão vinculadas a outras provas'}), 404
            
            # Buscar última ordem
            last_order = db.session.query(db.func.max(ExamQuestion.order_number)).filter_by(exam_id=exam_id).scalar() or 0
            
            added_questions = []
            for i, question in enumerate(questions):
                # Criar snapshot da questão
                question_snapshot = {
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'alternatives': [alt.to_dict() for alt in question.alternatives]
                }
                
                # Usar pontuação personalizada ou padrão
                points = question_points.get(str(question.id), question.points)
                
                exam_question = ExamQuestion(
                    exam_id=exam_id,
                    question_id=question.id,
                    points=points,
                    order_number=last_order + i + 1,
                    question_snapshot=question_snapshot
                )
                db.session.add(exam_question)
                added_questions.append(question)
            
            db.session.commit()
            
            return jsonify({
                'message': f'{len(added_questions)} questões adicionadas à prova',
                'questions': [q.to_dict() for q in added_questions]
            }), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    # Rotas específicas para estudantes
    @app.route('/api/student/classes', methods=['GET'])
    @jwt_required()
    def get_student_classes():
        """Obter turmas do estudante (matriculadas e solicitações)"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            if user.role != 'student':
                return jsonify({'error': 'Acesso negado'}), 403
            
            # Buscar todas as interações do estudante com turmas
            enrollments = db.session.query(
                ClassEnrollment.id,
                ClassEnrollment.status,
                ClassEnrollment.enrolled_at,
                ClassEnrollment.enrolled_at.label('requested_at'),
                Class.id.label('class_id'),
                Class.name,
                Class.description,
                Class.schedule,
                Class.is_active,
                Class.created_at,
                User.name.label('instructor_name')
            ).join(Class, ClassEnrollment.class_id == Class.id)\
             .join(User, Class.instructor_id == User.id)\
             .filter(ClassEnrollment.student_id == user_id)\
             .all()
            
            classes = []
            for enrollment in enrollments:
                classes.append({
                    'id': enrollment.class_id,
                    'name': enrollment.name,
                    'description': enrollment.description,
                    'instructor_name': enrollment.instructor_name,
                    'schedule': enrollment.schedule,
                    'is_active': enrollment.is_active,
                    'created_at': enrollment.created_at.isoformat() if enrollment.created_at else None,
                    'enrollment_status': enrollment.status,
                    'enrolled_at': enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
                    'requested_at': enrollment.requested_at.isoformat() if enrollment.requested_at else None
                })
            
            return jsonify(classes), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/student/available-classes', methods=['GET'])
    @jwt_required()
    def get_student_available_classes():
        """Obter turmas disponíveis para o estudante"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            if user.role != 'student':
                return jsonify({'error': 'Acesso negado'}), 403
            
            # Buscar turmas ativas que o estudante não está matriculado
            # Incluir também turmas onde ele foi rejeitado ou tem solicitação pendente
            subquery = db.session.query(ClassEnrollment.class_id).filter_by(student_id=user_id)
            
            classes_query = db.session.query(
                Class.id,
                Class.name,
                Class.description,
                Class.schedule,
                Class.is_active,
                Class.created_at,
                User.name.label('instructor_name'),
                ClassEnrollment.status.label('enrollment_status')
            ).join(User, Class.instructor_id == User.id)\
             .outerjoin(ClassEnrollment, db.and_(
                 Class.id == ClassEnrollment.class_id,
                 ClassEnrollment.student_id == user_id
             ))\
             .filter(Class.is_active == True)
            
            classes = []
            for class_data in classes_query.all():
                classes.append({
                    'id': class_data.id,
                    'name': class_data.name,
                    'description': class_data.description,
                    'instructor_name': class_data.instructor_name,
                    'schedule': class_data.schedule,
                    'is_active': class_data.is_active,
                    'created_at': class_data.created_at.isoformat() if class_data.created_at else None,
                    'enrollment_status': class_data.enrollment_status
                })
            
            return jsonify(classes), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/student/exams', methods=['GET'])
    @jwt_required()
    def get_student_exams():
        """Obter provas disponíveis para o estudante"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            if user.role != 'student':
                return jsonify({'error': 'Acesso negado'}), 403
            
            # Buscar provas das turmas em que o estudante está matriculado
            # Removido filtro de status para mostrar todas as provas (inclusive perdidas)
            exams_query = db.session.query(
                Exam.id,
                Exam.title,
                Exam.description,
                Exam.duration_minutes,
                Exam.start_time,
                Exam.end_time,
                Exam.status,
                Class.id.label('class_id'),
                Class.name.label('class_name'),
                User.name.label('instructor_name'),
                db.func.count(ExamQuestion.id).label('questions_count')
            ).join(Class, Exam.class_id == Class.id)\
             .join(User, Class.instructor_id == User.id)\
             .join(ClassEnrollment, db.and_(
                 Class.id == ClassEnrollment.class_id,
                 ClassEnrollment.student_id == user_id,
                 ClassEnrollment.status == 'approved'
             ))\
             .outerjoin(ExamQuestion, Exam.id == ExamQuestion.exam_id)\
             .filter(Exam.status.in_(['published', 'finished']))\
             .group_by(Exam.id, Class.id, User.id)\
             .all()
            
            exams = []
            for exam_data in exams_query:
                # Verificar se o estudante já fez a prova
                exam_result = ExamEnrollment.query.filter_by(
                    exam_id=exam_data.id,
                    student_id=user_id
                ).first()
                
                result_data = None
                if exam_result:
                    # Calcular pontuação total das respostas
                    total_points = db.session.query(
                        db.func.sum(Answer.points_earned)
                    ).filter(Answer.enrollment_id == exam_result.id).scalar() or 0
                    
                    # Calcular pontuação máxima possível
                    max_points = db.session.query(
                        db.func.sum(ExamQuestion.points)
                    ).filter(ExamQuestion.exam_id == exam_data.id).scalar() or 0
                    
                    percentage = (total_points / max_points * 100) if max_points > 0 else 0
                    
                    result_data = {
                        'id': exam_result.id,
                        'total_points': float(total_points),
                        'max_points': float(max_points),
                        'percentage': float(percentage),
                        'status': exam_result.status,
                        'started_at': exam_result.start_time.isoformat() if exam_result.start_time else None,
                        'finished_at': exam_result.end_time.isoformat() if exam_result.end_time else None
                    }
                
                exams.append({
                    'id': exam_data.id,
                    'title': exam_data.title,
                    'description': exam_data.description,
                    'duration_minutes': exam_data.duration_minutes,
                    'start_time': exam_data.start_time.isoformat() if exam_data.start_time else None,
                    'end_time': exam_data.end_time.isoformat() if exam_data.end_time else None,
                    'status': exam_data.status,
                    'class_id': exam_data.class_id,
                    'class_name': exam_data.class_name,
                    'instructor_name': exam_data.instructor_name,
                    'questions_count': exam_data.questions_count,
                    'result': result_data
                })
            
            return jsonify(exams), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/student/results', methods=['GET'])
    @jwt_required()
    def get_student_results():
        """Listar todos os resultados de provas do estudante logado"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            if user.role != 'student':
                return jsonify({'error': 'Acesso negado'}), 403
            
            # Buscar todas as matrículas do estudante que foram finalizadas
            enrollments = ExamEnrollment.query.filter_by(
                student_id=user_id,
                status='completed'
            ).all()
            
            results = []
            for enrollment in enrollments:
                # Buscar dados da prova
                exam = Exam.query.get(enrollment.exam_id)
                if not exam:
                    continue
                
                # Buscar nome da turma se existir
                class_name = None
                if exam.class_id:
                    class_obj = Class.query.get(exam.class_id)
                    if class_obj:
                        class_name = class_obj.name
                
                # Buscar respostas do estudante
                answers = Answer.query.filter_by(enrollment_id=enrollment.id).all()
                
                # Contar questões da prova
                questions_count = db.session.query(ExamQuestion).filter_by(exam_id=exam.id).count()
                
                # Usar resultados salvos no enrollment
                total_points = float(enrollment.total_points) if enrollment.total_points else 0.0
                max_points = float(enrollment.max_points) if enrollment.max_points else 0.0
                percentage = float(enrollment.percentage) if enrollment.percentage else 0.0
                
                result = {
                    'id': enrollment.id,
                    'exam_id': exam.id,
                    'student_id': user_id,
                    'total_points': total_points,
                    'max_points': max_points,
                    'percentage': percentage,
                    'status': enrollment.status,
                    'started_at': enrollment.start_time.isoformat() if enrollment.start_time else None,
                    'finished_at': enrollment.end_time.isoformat() if enrollment.end_time else None,
                    'answers_count': len(answers),
                    'questions_count': questions_count,
                    'exam': {
                        'id': exam.id,
                        'title': exam.title,
                        'description': exam.description,
                        'duration_minutes': exam.duration_minutes,
                        'start_time': exam.start_time.isoformat(),
                        'end_time': exam.end_time.isoformat(),
                        'class_id': exam.class_id,
                        'class_name': class_name
                    }
                }
                results.append(result)
            
            # Ordenar por data de finalização (mais recente primeiro)
            results.sort(key=lambda x: x['finished_at'] or '', reverse=True)
            
            return jsonify(results), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/student/results/<int:exam_id>', methods=['GET'])
    @jwt_required()
    def get_student_exam_result(exam_id):
        """Obter resultado detalhado de uma prova do estudante"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            if user.role != 'student':
                return jsonify({'error': 'Acesso negado'}), 403
            
            # Buscar resultado da prova
            exam_result = ExamEnrollment.query.filter_by(
                exam_id=exam_id,
                student_id=user_id
            ).first()
            
            if not exam_result:
                return jsonify({'error': 'Resultado não encontrado'}), 404
            
            # Buscar dados da prova
            exam = Exam.query.get_or_404(exam_id)
            class_obj = Class.query.get_or_404(exam.class_id)
            instructor = User.query.get_or_404(class_obj.instructor_id)
            
            # Buscar respostas do estudante
            answers_query = db.session.query(
                Answer.id,
                Answer.question_id,
                Answer.answer_text,
                Answer.selected_alternatives,
                Answer.points_earned,
                ExamQuestion.question_snapshot,
                ExamQuestion.points.label('question_points')
            ).join(ExamQuestion, Answer.question_id == ExamQuestion.question_id)\
             .filter(Answer.enrollment_id == exam_result.id)\
             .filter(ExamQuestion.exam_id == exam_id)\
             .order_by(ExamQuestion.order_number)\
             .all()
            
            answers = []
            for answer_data in answers_query:
                # Obter dados da questão do snapshot
                question_snapshot = answer_data.question_snapshot or {}
                
                # Converter selected_alternatives de string para lista se necessário
                selected_alts = []
                if answer_data.selected_alternatives:
                    if isinstance(answer_data.selected_alternatives, str):
                        try:
                            import json
                            selected_alts = json.loads(answer_data.selected_alternatives)
                        except:
                            selected_alts = []
                    else:
                        selected_alts = answer_data.selected_alternatives
                
                answers.append({
                    'id': answer_data.id,
                    'question_id': answer_data.question_id,
                    'question_text': question_snapshot.get('question_text', ''),
                    'question_type': question_snapshot.get('question_type', ''),
                    'question_points': float(answer_data.question_points),
                    'answer_text': answer_data.answer_text,
                    'selected_alternatives': selected_alts,
                    'points_earned': float(answer_data.points_earned) if answer_data.points_earned else 0,
                    'alternatives': question_snapshot.get('alternatives', [])
                })
            
            result = {
                'id': exam_result.id,
                'exam_id': exam_id,
                'exam_title': exam.title,
                'exam_description': exam.description,
                'class_name': class_obj.name,
                'instructor_name': instructor.name,
                'total_points': float(exam_result.total_points) if exam_result.total_points else 0,
                'max_points': float(exam_result.max_points) if exam_result.max_points else 0,
                'percentage': float(exam_result.percentage) if exam_result.percentage else 0,
                'status': exam_result.status,
                'started_at': exam_result.start_time.isoformat() if exam_result.start_time else None,
                'finished_at': exam_result.end_time.isoformat() if exam_result.end_time else None,
                'duration_minutes': exam.duration_minutes,
                'answers': answers
            }
            
            return jsonify(result), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/teacher/results', methods=['GET'])
    @jwt_required()
    def get_teacher_results():
        """Buscar todos os resultados das provas do professor"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            # Verificar se o usuário é professor ou admin
            if user.role not in ['professor', 'admin']:
                return jsonify({'error': 'Acesso negado'}), 403
            
            # Buscar todas as matrículas com resultados
            query = db.session.query(
                ExamEnrollment,
                Exam,
                User,
                Class
            ).join(
                Exam, ExamEnrollment.exam_id == Exam.id
            ).join(
                User, ExamEnrollment.student_id == User.id
            ).join(
                Class, Exam.class_id == Class.id
            ).filter(
                ExamEnrollment.status == 'completed'
            )
            
            # Se for professor, filtrar por:
            # 1. Turmas onde é instrutor OU
            # 2. Provas que ele criou
            if user.role == 'professor':
                query = query.filter(
                    db.or_(
                        Class.instructor_id == int(user_id),
                        Exam.created_by == int(user_id)
                    )
                )
            
            results = query.all()
            
            results_data = []
            for enrollment, exam, student, class_obj in results:
                # Calcular tempo gasto se disponível
                time_taken = None
                if enrollment.start_time and enrollment.end_time:
                    time_diff = enrollment.end_time - enrollment.start_time
                    time_taken = int(time_diff.total_seconds() / 60)  # em minutos
                
                results_data.append({
                    'id': enrollment.id,
                    'exam_id': exam.id,
                    'exam_title': exam.title,
                    'class_name': class_obj.name,
                    'student_id': student.id,
                    'student_name': student.name,
                    'student_email': student.email,
                    'total_points': float(enrollment.total_points) if enrollment.total_points else 0,
                    'max_points': float(enrollment.max_points) if enrollment.max_points else 0,
                    'percentage': float(enrollment.percentage) if enrollment.percentage else 0,
                    'status': enrollment.status,
                    'started_at': enrollment.start_time.isoformat() if enrollment.start_time else None,
                    'finished_at': enrollment.end_time.isoformat() if enrollment.end_time else None,
                    'time_taken': time_taken
                })
            
            return jsonify(results_data), 200
            
        except Exception as e:
            print(f"Erro ao buscar resultados: {str(e)}")
            return jsonify({'error': 'Erro interno do servidor'}), 500

    @app.route('/api/teacher/results/manual-correction', methods=['POST'])
    @jwt_required()
    def manual_correction():
        """Correção manual de questões dissertativas"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            if user.role not in ['professor', 'admin']:
                return jsonify({'error': 'Apenas professores podem fazer correção manual'}), 403
            
            data = request.get_json()
            answer_id = data.get('answer_id')
            points_earned = data.get('points_earned')
            
            if not answer_id or points_earned is None:
                return jsonify({'error': 'ID da resposta e pontuação são obrigatórios'}), 400
            
            # Buscar a resposta
            answer = Answer.query.get_or_404(answer_id)
            
            # Verificar se o professor tem acesso a esta correção
            enrollment = ExamEnrollment.query.get(answer.enrollment_id)
            exam = Exam.query.get(enrollment.exam_id)
            
            if user.role != 'admin' and exam.created_by != int(user_id):
                return jsonify({'error': 'Sem permissão para corrigir esta resposta'}), 403
            
            # Buscar a questão para validar pontuação máxima
            exam_question = ExamQuestion.query.filter_by(
                exam_id=enrollment.exam_id,
                question_id=answer.question_id
            ).first()
            
            if not exam_question:
                return jsonify({'error': 'Questão não encontrada na prova'}), 404
            
            max_points = float(exam_question.points)
            if points_earned < 0 or points_earned > max_points:
                return jsonify({'error': f'Pontuação deve estar entre 0 e {max_points}'}), 400
            
            # Atualizar a resposta
            answer.points_earned = points_earned
            answer.correction_method = 'manual'
            
            # Recalcular pontuação total do estudante
            total_points = 0.0
            answers = Answer.query.filter_by(enrollment_id=enrollment.id).all()
            
            for ans in answers:
                if ans.points_earned is not None:
                    total_points += float(ans.points_earned)
            
            # Atualizar enrollment
            enrollment.total_points = total_points
            if enrollment.max_points > 0:
                enrollment.percentage = (total_points / enrollment.max_points * 100)
            
            db.session.commit()
            
            return jsonify({
                'message': 'Correção realizada com sucesso',
                'answer': answer.to_dict(),
                'new_total_points': float(total_points),
                'new_percentage': float(enrollment.percentage)
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/teacher/results/pending-corrections', methods=['GET'])
    @jwt_required()
    def get_pending_corrections():
        """Listar respostas dissertativas pendentes de correção"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            if user.role not in ['professor', 'admin']:
                return jsonify({'error': 'Apenas professores podem acessar correções'}), 403
            
            # Buscar provas do professor
            if user.role == 'admin':
                exams = Exam.query.all()
            else:
                exams = Exam.query.filter_by(created_by=user_id).all()
            
            exam_ids = [exam.id for exam in exams]
            
            # Buscar respostas dissertativas pendentes
            # Incluir tanto as que não têm pontuação quanto as que têm correction_method = 'pending'
            pending_answers = db.session.query(Answer, Question, User, Exam, ExamEnrollment)\
                .join(Question, Answer.question_id == Question.id)\
                .join(ExamEnrollment, Answer.enrollment_id == ExamEnrollment.id)\
                .join(User, ExamEnrollment.student_id == User.id)\
                .join(Exam, ExamEnrollment.exam_id == Exam.id)\
                .filter(
                    Question.question_type == 'essay',
                    db.or_(
                        Answer.correction_method == 'pending',
                        Answer.correction_method.is_(None),
                        Answer.points_earned.is_(None)
                    ),
                    Answer.answer_text.isnot(None),
                    Answer.answer_text != '',
                    Exam.id.in_(exam_ids)
                ).all()
            
            corrections_data = []
            for answer, question, student, exam, enrollment in pending_answers:
                # Buscar pontuação da questão na prova
                exam_question = ExamQuestion.query.filter_by(
                    exam_id=exam.id,
                    question_id=question.id
                ).first()
                
                corrections_data.append({
                    'answer_id': answer.id,
                    'question_id': question.id,
                    'question_text': question.question_text,
                    'expected_answer': question.expected_answer,
                    'student_answer': answer.answer_text,
                    'student_name': student.name,
                    'student_email': student.email,
                    'exam_title': exam.title,
                    'exam_id': exam.id,
                    'max_points': float(exam_question.points) if exam_question else 0.0,
                    'similarity_score': float(answer.similarity_score) if answer.similarity_score else None,
                    'correction_method': answer.correction_method,
                    'auto_correction_enabled': question.auto_correction_enabled,
                    'created_at': answer.created_at.isoformat()
                })
            
            return jsonify({
                'pending_corrections': corrections_data,
                'total_count': len(corrections_data)
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/teacher/results/recalculate', methods=['POST'])
    @jwt_required()
    def recalculate_results():
        """Recalcular notas de uma prova específica ou de um aluno específico"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            # Verificar se o usuário é professor ou admin
            if user.role not in ['professor', 'admin']:
                return jsonify({'error': 'Acesso negado'}), 403
            
            data = request.get_json()
            exam_id = data.get('exam_id')
            student_id = data.get('student_id')
            recorrect_essays = data.get('recorrect_essays', False)  # Nova opção
            
            if not exam_id and not student_id:
                return jsonify({'error': 'exam_id ou student_id deve ser fornecido'}), 400
            
            # Construir query base
            query = ExamEnrollment.query.filter(ExamEnrollment.status == 'completed')
            
            if exam_id:
                # Recalcular todas as notas de uma prova específica
                query = query.filter(ExamEnrollment.exam_id == exam_id)
                
                # Verificar se o professor tem acesso a esta prova
                if user.role == 'professor':
                    exam = Exam.query.get(exam_id)
                    if not exam:
                        return jsonify({'error': 'Prova não encontrada'}), 404
                    
                    # Professor tem acesso se:
                    # 1. É o instrutor da turma OU
                    # 2. É o criador da prova
                    class_obj = Class.query.get(exam.class_id)
                    has_access = False
                    
                    if class_obj and class_obj.instructor_id == int(user_id):
                        has_access = True
                    elif exam.created_by == int(user_id):
                        has_access = True
                    
                    if not has_access:
                        return jsonify({'error': 'Acesso negado a esta prova'}), 403
            
            if student_id:
                # Recalcular todas as notas de um aluno específico
                query = query.filter(ExamEnrollment.student_id == student_id)
                
                # Se for professor, verificar se tem acesso às turmas do aluno
                if user.role == 'professor':
                    query = query.join(Exam).join(Class).filter(
                        db.or_(
                            Class.instructor_id == int(user_id),
                            Exam.created_by == int(user_id)
                        )
                    )
            
            enrollments = query.all()
            
            if not enrollments:
                return jsonify({'error': 'Nenhuma matrícula encontrada para recálculo'}), 404
            
            recalculated_count = 0
            
            for enrollment in enrollments:
                # Buscar todas as respostas desta matrícula
                answers = Answer.query.filter_by(enrollment_id=enrollment.id).all()
                
                total_points = 0.0
                max_points = 0.0
                
                for answer in answers:
                    # Buscar a questão e suas alternativas
                    question = Question.query.get(answer.question_id)
                    if not question:
                        continue
                    
                    # Buscar pontuação da questão no exame
                    exam_question = ExamQuestion.query.filter_by(
                        exam_id=enrollment.exam_id,
                        question_id=question.id
                    ).first()
                    
                    points_for_question = float(exam_question.points) if exam_question else 1.0
                    max_points += points_for_question
                    
                    # Recalcular pontuação baseada no tipo de questão
                    if question.question_type == 'single_choice':
                        # Tratar selected_alternatives que pode ser string ou lista
                        if isinstance(answer.selected_alternatives, str):
                            selected_alternatives = [int(alt_id) for alt_id in answer.selected_alternatives.split(',') if alt_id.strip()]
                        elif isinstance(answer.selected_alternatives, list):
                            selected_alternatives = [int(alt_id) for alt_id in answer.selected_alternatives if alt_id]
                        else:
                            selected_alternatives = []
                        if selected_alternatives:
                            selected_alt = Alternative.query.get(selected_alternatives[0])
                            if selected_alt and selected_alt.is_correct:
                                answer.points_earned = points_for_question
                            else:
                                answer.points_earned = 0.0
                        else:
                            answer.points_earned = 0.0
                    
                    elif question.question_type == 'true_false':
                        # Tratar selected_alternatives que pode ser string ou lista
                        if isinstance(answer.selected_alternatives, str):
                            selected_alternatives = [int(alt_id) for alt_id in answer.selected_alternatives.split(',') if alt_id.strip()]
                        elif isinstance(answer.selected_alternatives, list):
                            selected_alternatives = [int(alt_id) for alt_id in answer.selected_alternatives if alt_id]
                        else:
                            selected_alternatives = []
                        if selected_alternatives:
                            selected_alt = Alternative.query.get(selected_alternatives[0])
                            if selected_alt and selected_alt.is_correct:
                                answer.points_earned = points_for_question
                            else:
                                answer.points_earned = 0.0
                        else:
                            answer.points_earned = 0.0
                    
                    elif question.question_type == 'multiple_choice':
                        # Tratar selected_alternatives que pode ser string ou lista
                        if isinstance(answer.selected_alternatives, str):
                            selected_alternatives = [int(alt_id) for alt_id in answer.selected_alternatives.split(',') if alt_id.strip()]
                        elif isinstance(answer.selected_alternatives, list):
                            selected_alternatives = [int(alt_id) for alt_id in answer.selected_alternatives if alt_id]
                        else:
                            selected_alternatives = []
                        correct_alternatives = Alternative.query.filter_by(question_id=question.id, is_correct=True).all()
                        
                        correct_ids = {alt.id for alt in correct_alternatives}
                        selected_ids = set(selected_alternatives)
                        
                        # Calcular acertos e erros
                        correct_selected = len(correct_ids.intersection(selected_ids))
                        incorrect_selected = len(selected_ids - correct_ids)
                        total_correct = len(correct_ids)
                        
                        if total_correct > 0:
                            # Acertos líquidos = corretas_selecionadas - incorretas_selecionadas
                            net_correct = correct_selected - incorrect_selected
                            
                            if net_correct > 0:
                                # Pontuação proporcional aos acertos líquidos
                                score_ratio = net_correct / total_correct
                                answer.points_earned = points_for_question * score_ratio
                            else:
                                # Se erros >= acertos, pontuação zero
                                answer.points_earned = 0.0
                        else:
                            answer.points_earned = 0.0
                    
                    elif question.question_type == 'essay':
                        # Para questões dissertativas
                        if recorrect_essays and question.auto_correction_enabled and question.expected_answer and answer.answer_text:
                            # Tentar correção automática se solicitado
                            try:
                                from auto_correction import auto_correction
                                print(f"🔄 Recorrigindo questão dissertativa ID: {question.id}")
                                points_earned, similarity_score = auto_correction.auto_correct_essay(
                                    question.expected_answer,
                                    answer.answer_text,
                                    points_for_question
                                )
                                
                                if points_earned is not None:
                                    answer.points_earned = points_earned
                                    answer.similarity_score = similarity_score
                                    answer.correction_method = 'auto'
                                    print(f"   - ✅ Recorreção automática: {points_earned} pontos")
                                else:
                                    # Se a correção automática falhar, manter valor atual ou zero
                                    if answer.points_earned is None:
                                        answer.points_earned = 0.0
                                    print(f"   - ⏳ Recorreção retornou None - mantida nota atual")
                            except Exception as e:
                                # Em caso de erro, manter pontuação atual ou zero
                                if answer.points_earned is None:
                                    answer.points_earned = 0.0
                                print(f"   - ❌ Erro na recorreção: {e}")
                        else:
                            # Manter pontuação manual para dissertativas
                            if answer.points_earned is None:
                                answer.points_earned = 0.0
                    
                    total_points += float(answer.points_earned) if answer.points_earned else 0.0
                
                # Atualizar totais da matrícula
                enrollment.total_points = total_points
                enrollment.max_points = max_points
                enrollment.percentage = (total_points / max_points * 100) if max_points > 0 else 0
                
                recalculated_count += 1
            
            # Salvar todas as alterações
            db.session.commit()
            
            message = f'{recalculated_count} resultado(s) recalculado(s) com sucesso'
            if recorrect_essays:
                message += ' (incluindo recorreção automática de questões dissertativas)'
            
            return jsonify({
                'message': message,
                'recalculated_count': recalculated_count,
                'recorrected_essays': recorrect_essays
            }), 200
            
        except Exception as e:
            db.session.rollback()
            import traceback
            print(f"Erro ao recalcular resultados: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

    # Rotas para Correção de Provas
    @app.route('/api/teacher/correction-review', methods=['GET'])
    @jwt_required()
    def get_correction_review():
        """Obter dados para página de revisão de correções"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            # Verificar se o usuário é professor ou admin
            if user.role not in ['professor', 'admin']:
                return jsonify({'error': 'Acesso negado'}), 403
            
            # Buscar provas do professor ou todas (se admin)
            if user.role == 'admin':
                exams = Exam.query.filter(Exam.status == 'published').all()
            else:
                # Buscar provas onde:
                # 1. Professor é instrutor da turma OU
                # 2. Professor é criador da prova
                classes = Class.query.filter_by(instructor_id=user_id).all()
                class_ids = [c.id for c in classes]
                
                exams = Exam.query.filter(
                                            db.or_(
                            Exam.class_id.in_(class_ids),
                            Exam.created_by == int(user_id)
                        ),
                    Exam.status == 'published'
                ).all()
            
            correction_data = []
            
            for exam in exams:
                # Buscar matrículas finalizadas para esta prova
                enrollments = ExamEnrollment.query.filter_by(
                    exam_id=exam.id,
                    status='completed'
                ).all()
                
                for enrollment in enrollments:
                    student = User.query.get(enrollment.student_id)
                    
                    # Buscar respostas dissertativas pendentes ou já corrigidas
                    essay_answers = db.session.query(Answer).join(Question).filter(
                        Answer.enrollment_id == enrollment.id,
                        Question.question_type == 'essay'
                    ).all()
                    
                    pending_count = sum(1 for answer in essay_answers 
                                      if answer.correction_method in ['pending', None])
                    
                    auto_corrected_count = sum(1 for answer in essay_answers 
                                             if answer.correction_method == 'auto')
                    
                    manual_corrected_count = sum(1 for answer in essay_answers 
                                               if answer.correction_method == 'manual')
                    
                    if essay_answers:  # Só incluir se houver questões dissertativas
                        correction_data.append({
                            'enrollment_id': enrollment.id,
                            'exam_id': exam.id,
                            'exam_title': exam.title,
                            'student_id': student.id,
                            'student_name': student.name,
                            'student_email': student.email,
                            'total_points': float(enrollment.total_points) if enrollment.total_points else 0.0,
                            'max_points': float(enrollment.max_points) if enrollment.max_points else 0.0,
                            'percentage': float(enrollment.percentage) if enrollment.percentage else 0.0,
                            'essay_questions_count': len(essay_answers),
                            'pending_corrections': pending_count,
                            'auto_corrected': auto_corrected_count,
                            'manual_corrected': manual_corrected_count,
                            'completed_at': enrollment.completed_at.isoformat() if enrollment.completed_at else None
                        })
            
            return jsonify({
                'corrections': correction_data,
                'total_count': len(correction_data)
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/teacher/student-exam/<int:enrollment_id>', methods=['GET'])
    @jwt_required()
    def get_student_exam_details(enrollment_id):
        """Obter detalhes da prova de um aluno específico"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            # Verificar se o usuário é professor ou admin
            if user.role not in ['professor', 'admin']:
                return jsonify({'error': 'Acesso negado'}), 403
            
            # Buscar matrícula
            enrollment = ExamEnrollment.query.get_or_404(enrollment_id)
            exam = Exam.query.get_or_404(enrollment.exam_id)
            student = User.query.get_or_404(enrollment.student_id)
            
            # Verificar se o professor tem acesso a esta prova
            if user.role == 'professor':
                # Professor tem acesso se:
                # 1. É o instrutor da turma da prova OU
                # 2. É o criador da prova
                class_obj = Class.query.get(exam.class_id)
                has_access = False
                
                if class_obj and class_obj.instructor_id == int(user_id):
                    has_access = True
                elif exam.created_by == int(user_id):
                    has_access = True
                
                if not has_access:
                    return jsonify({'error': 'Acesso negado a esta prova'}), 403
            
            # Buscar todas as respostas do aluno
            answers = Answer.query.filter_by(enrollment_id=enrollment_id).all()
            
            # Organizar respostas por questão
            answers_data = []
            for answer in answers:
                question = Question.query.get(answer.question_id)
                if not question:
                    continue
                
                # Buscar pontuação da questão no exame
                exam_question = ExamQuestion.query.filter_by(
                    exam_id=exam.id,
                    question_id=question.id
                ).first()
                
                answer_data = {
                    'id': answer.id,
                    'question_id': question.id,
                    'question_text': question.question_text,
                    'question_type': question.question_type,
                    'expected_answer': question.expected_answer,
                    'max_points': float(exam_question.points) if exam_question else 0.0,
                    'points_earned': float(answer.points_earned) if answer.points_earned else 0.0,
                    'correction_method': answer.correction_method or 'pending',
                    'similarity_score': float(answer.similarity_score) if answer.similarity_score else None,
                    'auto_correction_enabled': question.auto_correction_enabled,
                    'feedback': answer.feedback,
                    'answer_text': answer.answer_text,
                    'selected_alternatives': answer.selected_alternatives or []
                }
                
                # Para questões objetivas, buscar alternativas
                if question.question_type != 'essay':
                    alternatives = Alternative.query.filter_by(question_id=question.id).order_by(Alternative.order_number).all()
                    answer_data['alternatives'] = [
                        {
                            'id': alt.id,
                            'text': alt.alternative_text,
                            'is_correct': alt.is_correct,
                            'selected': alt.id in (answer.selected_alternatives or [])
                        }
                        for alt in alternatives
                    ]
                
                answers_data.append(answer_data)
            
            # Buscar informações da turma
            class_obj = Class.query.get(exam.class_id)
            
            # Calcular tempo gasto (se disponível)
            time_taken = None
            if enrollment.completed_at and enrollment.start_time:
                time_diff = enrollment.completed_at - enrollment.start_time
                time_taken = int(time_diff.total_seconds() / 60)  # em minutos
            
            return jsonify({
                'id': enrollment.id,
                'student_name': student.name,
                'student_email': student.email,
                'exam_title': exam.title,
                'exam_id': exam.id,
                'class_name': class_obj.name if class_obj else 'Turma não encontrada',
                'total_points': float(enrollment.total_points) if enrollment.total_points else 0.0,
                'max_points': float(enrollment.max_points) if enrollment.max_points else 0.0,
                'percentage': float(enrollment.percentage) if enrollment.percentage else 0.0,
                'time_taken': time_taken,
                'finished_at': enrollment.completed_at.isoformat() if enrollment.completed_at else None,
                'status': enrollment.status,
                'answers': answers_data
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 422

    @app.route('/api/teacher/manual-correction/<int:answer_id>', methods=['POST'])
    @jwt_required()
    def update_manual_correction(answer_id):
        """Atualizar correção manual de uma questão dissertativa"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            
            # Verificar se o usuário é professor ou admin
            if user.role not in ['professor', 'admin']:
                return jsonify({'error': 'Acesso negado'}), 403
            
            data = request.get_json()
            points_earned = data.get('points_earned')
            feedback = data.get('feedback', '')
            
            if points_earned is None:
                return jsonify({'error': 'points_earned é obrigatório'}), 400
            
            # Buscar resposta
            answer = Answer.query.get_or_404(answer_id)
            question = Question.query.get_or_404(answer.question_id)
            
            # Verificar se é questão dissertativa
            if question.question_type != 'essay':
                return jsonify({'error': 'Apenas questões dissertativas podem ser corrigidas manualmente'}), 400
            
            # Buscar matrícula e verificar acesso do professor
            enrollment = ExamEnrollment.query.get_or_404(answer.enrollment_id)
            exam = Exam.query.get_or_404(enrollment.exam_id)
            
            if user.role == 'professor':
                # Professor tem acesso se:
                # 1. É o instrutor da turma da prova OU
                # 2. É o criador da prova
                class_obj = Class.query.get(exam.class_id)
                has_access = False
                
                if class_obj and class_obj.instructor_id == int(user_id):
                    has_access = True
                elif exam.created_by == int(user_id):
                    has_access = True
                
                if not has_access:
                    return jsonify({'error': 'Acesso negado a esta prova'}), 403
            
            # Buscar pontuação máxima da questão
            exam_question = ExamQuestion.query.filter_by(
                exam_id=exam.id,
                question_id=question.id
            ).first()
            
            max_points = float(exam_question.points) if exam_question else 0.0
            
            # Validar pontuação
            if points_earned < 0 or points_earned > max_points:
                return jsonify({'error': f'Pontuação deve estar entre 0 e {max_points}'}), 400
            
            # Atualizar resposta
            answer.points_earned = points_earned
            answer.correction_method = 'manual'
            answer.feedback = feedback
            
            db.session.commit()
            
            # Recalcular nota total do aluno
            answers = Answer.query.filter_by(enrollment_id=enrollment.id).all()
            total_points = sum(float(ans.points_earned) for ans in answers if ans.points_earned is not None)
            
            enrollment.total_points = total_points
            enrollment.percentage = (total_points / enrollment.max_points * 100) if enrollment.max_points > 0 else 0
            
            db.session.commit()
            
            return jsonify({
                'message': 'Correção manual salva com sucesso',
                'answer': {
                    'id': answer.id,
                    'points_earned': float(answer.points_earned),
                    'correction_method': answer.correction_method,
                    'feedback': answer.feedback
                },
                'enrollment': {
                    'total_points': float(enrollment.total_points),
                    'percentage': float(enrollment.percentage)
                }
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 422

    # Rota de Healthcheck
    @app.route('/api/test', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy'}), 200 