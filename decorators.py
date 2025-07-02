import calendar
import logging
from datetime import datetime
from functools import wraps

from database import db
from models import Exam

logger = logging.getLogger(__name__)

def auto_update_expired_exams(f):
    """
    Decorator que atualiza automaticamente provas expiradas antes de executar a rota.
    Também verifica se provas finished deveriam voltar para published.
    Deve ser aplicado em rotas relacionadas a provas.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            now = datetime.utcnow()
            
            # Verificar se há provas expiradas para atualizar (published -> finished)
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
            
            # Verificar se há provas que deveriam voltar para published (finished -> published)
            reactivated_exams = Exam.query.filter(
                Exam.status == 'finished',
                Exam.end_time > now
            ).all()
            
            if reactivated_exams:
                reactivated_count = 0
                for exam in reactivated_exams:
                    exam.status = 'published'
                    reactivated_count += 1
                
                db.session.commit()
                logger.info(f"Auto-reativadas {reactivated_count} provas reagendadas")
                
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
    Também verifica se provas finished deveriam voltar para published.
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
                    # Atualizar provas expiradas (published -> finished)
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
                    
                    # Verificar provas que deveriam voltar para published (finished -> published)
                    reactivated_exams = Exam.query.filter(
                        Exam.status == 'finished',
                        Exam.end_time > now
                    ).all()
                    
                    if reactivated_exams:
                        reactivated_count = 0
                        for exam in reactivated_exams:
                            exam.status = 'published'
                            reactivated_count += 1
                        
                        db.session.commit()
                        logger.info(f"Smart-reativadas {reactivated_count} provas reagendadas")
                    
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
    Também verifica se uma prova finished deveria voltar para published.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Tentar extrair exam_id dos parâmetros
            exam_id = kwargs.get('exam_id') or (args[0] if args else None)
            
            if exam_id:
                now = datetime.utcnow()
                exam = Exam.query.get(exam_id)
                
                if exam and exam.end_time:
                    # Converter end_time para UTC se necessário para comparação consistente
                    exam_end_time = exam.end_time
                    if exam_end_time.tzinfo is not None:
                        # Se tem timezone, converter para UTC
                        exam_end_time = exam_end_time.utctimetuple()
                        exam_end_time = datetime.fromtimestamp(calendar.timegm(exam_end_time))
                    
                    # Verificar se prova published expirou
                    if exam.status == 'published' and exam_end_time < now:
                        exam.status = 'finished'
                        db.session.commit()
                        logger.info(f"Prova ID {exam_id} atualizada para 'finished' no acesso")
                    
                    # Verificar se prova finished deveria voltar para published
                    elif exam.status == 'finished' and exam_end_time > now:
                        exam.status = 'published'
                        db.session.commit()
                        logger.info(f"Prova ID {exam_id} atualizada para 'published' no acesso (reagendada)")
                    
        except Exception as e:
            logger.error(f"Erro ao verificar prova específica: {e}")
            db.session.rollback()
        
        return f(*args, **kwargs)
    
    return decorated_function 