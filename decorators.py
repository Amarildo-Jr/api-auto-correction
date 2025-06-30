import logging
from datetime import datetime
from functools import wraps

from database import db
from models import Exam

logger = logging.getLogger(__name__)

def auto_update_expired_exams(f):
    """
    Decorator que atualiza automaticamente provas expiradas antes de executar a rota.
    Deve ser aplicado em rotas relacionadas a provas.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Verificar se há provas expiradas para atualizar
            now = datetime.utcnow()
            expired_exams = Exam.query.filter(
                Exam.status == 'published',
                Exam.end_time < now
            ).all()
            
            if expired_exams:
                updated_count = 0
                for exam in expired_exams:
                    exam.status = 'finished'
                    updated_count += 1
                
                db.session.commit()
                logger.info(f"Auto-atualizadas {updated_count} provas expiradas")
                
        except Exception as e:
            logger.error(f"Erro ao auto-atualizar provas expiradas: {e}")
            db.session.rollback()
        
        # Continuar com a execução da rota original
        return f(*args, **kwargs)
    
    return decorated_function

def smart_update_expired_exams(update_interval_minutes=15):
    """
    Decorator inteligente que só atualiza provas expiradas se a última verificação
    foi há mais de X minutos (padrão: 15 minutos).
    Mais eficiente para rotas muito chamadas.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Verificar timestamp da última atualização
                from flask import current_app
                
                last_check = getattr(current_app, '_last_exam_check', None)
                now = datetime.utcnow()
                
                should_check = (
                    last_check is None or 
                    (now - last_check).total_seconds() > (update_interval_minutes * 60)
                )
                
                if should_check:
                    # Atualizar provas expiradas
                    expired_exams = Exam.query.filter(
                        Exam.status == 'published',
                        Exam.end_time < now
                    ).all()
                    
                    if expired_exams:
                        updated_count = 0
                        for exam in expired_exams:
                            exam.status = 'finished'
                            updated_count += 1
                        
                        db.session.commit()
                        logger.info(f"Smart-atualizadas {updated_count} provas expiradas")
                    
                    # Atualizar timestamp da última verificação
                    current_app._last_exam_check = now
                    
            except Exception as e:
                logger.error(f"Erro no smart update de provas expiradas: {e}")
                db.session.rollback()
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def on_exam_access(f):
    """
    Decorator específico para quando uma prova é acessada.
    Verifica se a própria prova expirou e atualiza apenas ela se necessário.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Tentar extrair exam_id dos parâmetros
            exam_id = kwargs.get('exam_id') or (args[0] if args else None)
            
            if exam_id:
                now = datetime.utcnow()
                exam = Exam.query.get(exam_id)
                
                if exam and exam.status == 'published' and exam.end_time < now:
                    exam.status = 'finished'
                    db.session.commit()
                    logger.info(f"Prova ID {exam_id} atualizada para 'finished' no acesso")
                    
        except Exception as e:
            logger.error(f"Erro ao verificar prova específica: {e}")
            db.session.rollback()
        
        return f(*args, **kwargs)
    
    return decorated_function 