import logging
import os
import re
from typing import Optional, Tuple

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoCorrection:
    def __init__(self):
        """Inicializar o sistema de correção automática"""
        self.api_key = os.getenv('GOOGLE_GENAI_API_KEY')
        if not self.api_key:
            logger.warning("GOOGLE_GENAI_API_KEY não encontrada. Correção automática será desabilitada.")
            self.enabled = False
            return
        
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.enabled = True
            logger.info("Sistema de correção automática inicializado com sucesso")
        except ImportError:
            logger.error("Biblioteca google-genai não encontrada. Instale com: pip install google-genai")
            self.enabled = False
        except Exception as e:
            logger.error(f"Erro ao inicializar correção automática: {str(e)}")
            self.enabled = False

    def calculate_similarity(self, teacher_answer: str, student_answer: str) -> Optional[float]:
        """
        Calcular similaridade entre resposta do professor e do estudante
        Usando o modelo Gemini para análise de similaridade
        
        Args:
            teacher_answer: Resposta esperada (gabarito do professor)
            student_answer: Resposta do estudante
            
        Returns:
            Score de similaridade de 0 a 10, ou None se houver erro
        """
        if not self.enabled:
            logger.warning("Correção automática não está habilitada")
            return None
        
        if not teacher_answer or not student_answer:
            logger.warning("Resposta do professor ou estudante está vazia")
            return 0.0
        
        try:
            # Prompt para o modelo analisar similaridade
            prompt = f"""
Analise a similaridade entre estas duas respostas sobre o mesmo tópico.

RESPOSTA ESPERADA (GABARITO):
{teacher_answer.strip()}

RESPOSTA DO ESTUDANTE:
{student_answer.strip()}

Avalie a similaridade considerando:
- Conceitos corretos mencionados
- Precisão das informações
- Compreensão do tema
- Linguagem e termos utilizados

Responda APENAS com um número de 0 a 100 (pode usar decimais como 75.5):
- 90-100: Resposta perfeita, idêntica em conceitos
- 80-89: Resposta muito boa, conceitos corretos
- 70-79: Resposta boa, conceitos principais corretos
- 60-69: Resposta satisfatória, conceitos básicos corretos
- 40-59: Resposta parcial, alguns conceitos corretos
- 20-39: Resposta fraca, poucos conceitos corretos
- 0-19: Resposta incorreta ou muito diferente

SCORE:"""

            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
            )
            
            # Extrair número da resposta
            response_text = response.text.strip()
            logger.info(f"Resposta do modelo: {response_text}")
            
            # Buscar por número no texto
            score_match = re.search(r'(\d+(?:\.\d+)?)', response_text)
            if score_match:
                raw_score = float(score_match.group(1))
                logger.info(f"Score bruto extraído: {raw_score}")
                
                # Garantir que o score esteja no intervalo [0, 100]
                final_score = max(0.0, min(100.0, raw_score))
                
                if raw_score != final_score:
                    logger.warning(f"Score ajustado de {raw_score} para {final_score}")
                
                logger.info(f"Similaridade final: {final_score:.2f}")
                return round(final_score, 2)
            else:
                logger.error(f"Não foi possível extrair score da resposta: {response_text}")
                return None
            
        except Exception as e:
            logger.error(f"Erro ao calcular similaridade: {str(e)}")
            return None

    def auto_correct_essay(self, teacher_answer: str, student_answer: str, max_points: float) -> Tuple[Optional[float], Optional[float]]:
        """
        Corrigir questão dissertativa automaticamente
        
        Args:
            teacher_answer: Resposta esperada (gabarito do professor)
            student_answer: Resposta do estudante
            max_points: Pontuação máxima da questão
            
        Returns:
            Tupla (pontos_obtidos, score_similaridade)
        """
        if not self.enabled:
            return None, None
        
        similarity_score = self.calculate_similarity(teacher_answer, student_answer)
        
        if similarity_score is None:
            return None, None
        
        # Calcular pontos baseado na similaridade usando intervalos
        points_earned = self._calculate_points_by_intervals(similarity_score, max_points)
        
        logger.info(f"Cálculo de pontos:")
        logger.info(f"  - Similaridade: {similarity_score}/100")
        logger.info(f"  - Pontos máximos: {max_points}")
        logger.info(f"  - Pontos atribuídos: {points_earned}")
        logger.info(f"  - Resultado final: {points_earned}/{max_points} pontos")
        
        return points_earned, similarity_score

    def _calculate_points_by_intervals(self, similarity_score: float, max_points: float) -> float:
        """
        Calcular pontuação baseada em intervalos de similaridade
        
        Sistema de intervalos para atribuição de pontos:
        - 90-100%: Nota máxima (100% dos pontos)
        - 80-89%: 85-99% dos pontos
        - 70-79%: 70-84% dos pontos  
        - 60-69%: 60-69% dos pontos
        - 40-59%: 30-59% dos pontos
        - 20-39%: 10-29% dos pontos
        - 0-19%: 0-9% dos pontos
        
        Args:
            similarity_score: Score de similaridade (0-100)
            max_points: Pontuação máxima da questão
            
        Returns:
            Pontos obtidos baseado nos intervalos
        """
        if similarity_score >= 90:
            # 90-100%: Nota máxima
            percentage = 1.0
        elif similarity_score >= 80:
            # 80-89%: 85-99% da nota
            percentage = 0.85 + (similarity_score - 80) * 0.015  # 0.85 a 0.99
        elif similarity_score >= 70:
            # 70-79%: 70-84% da nota
            percentage = 0.70 + (similarity_score - 70) * 0.015  # 0.70 a 0.84
        elif similarity_score >= 60:
            # 60-69%: 60-69% da nota
            percentage = 0.60 + (similarity_score - 60) * 0.01   # 0.60 a 0.69
        elif similarity_score >= 40:
            # 40-59%: 30-59% da nota
            percentage = 0.30 + (similarity_score - 40) * 0.015  # 0.30 a 0.59
        elif similarity_score >= 20:
            # 20-39%: 10-29% da nota
            percentage = 0.10 + (similarity_score - 20) * 0.01   # 0.10 a 0.29
        else:
            # 0-19%: 0-9% da nota
            percentage = similarity_score * 0.005                # 0.00 a 0.09
        
        points_earned = max_points * percentage
        return round(points_earned, 2)

    def is_enabled(self) -> bool:
        """Verificar se a correção automática está habilitada"""
        return self.enabled

# Instância global do sistema de correção
auto_correction = AutoCorrection() 