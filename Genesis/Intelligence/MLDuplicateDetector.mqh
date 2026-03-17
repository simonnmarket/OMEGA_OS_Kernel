//+------------------------------------------------------------------+
//| ml_duplicate_detector.mqh - Detector ML de Duplicatas            |
//| Projeto: Genesis                                                |
//| Pasta: Include/Intelligence/                                     |
//| Versão: v1.0 (ML Anti-Duplicação)                                |
//+------------------------------------------------------------------+
#ifndef __ML_DUPLICATE_DETECTOR_MQH__
#define __ML_DUPLICATE_DETECTOR_MQH__

#include <Genesis/Utils/LoggerInstitutional.mqh>
#include <Genesis/Audit/AuditNomenclatureValidator.mqh>

struct DetectedPattern {
   string pattern_type;
   string filename;
   double confidence;
   string description;
   datetime detected_time;
   string recommendation;
};

struct MLAnalysis {
   int total_files_analyzed;
   int duplicates_detected;
   int naming_patterns_found;
   int potential_conflicts;
   double ml_confidence;
   datetime analysis_time;
};

class MLDuplicateDetector
{
private:
   logger_institutional &m_logger;
   AuditNomenclatureValidator &m_nomenclature_validator;
   DetectedPattern m_detected_patterns[];
   MLAnalysis m_ml_analysis;
   string m_learning_history[];

   int CalculateSemanticHash(string filename)
   {
      int hash = 0; string normalized = StringLower(filename);
      for(int i = 0; i < StringLen(normalized); i++) hash = (hash * 31 + StringGetCharacter(normalized, i)) % 1000000;
      return hash;
   }

   bool DetectNamingPattern(string filename)
   {
      string normalized = StringLower(filename);
      if(StringFind(normalized, "quantum") >= 0 && StringFind(normalized, "data") >= 0)
      {
         DetectedPattern pattern; pattern.pattern_type = "QUANTUM_DATA_PATTERN"; pattern.filename = filename; pattern.confidence = 0.95; pattern.description = "Padrão quântico de dados detectado"; pattern.detected_time = TimeCurrent(); pattern.recommendation = "Verificar duplicatas"; ArrayPushBack(m_detected_patterns, pattern); m_logger.log_info("[ML] Padrão quântico detectado: " + filename); return true;
      }
      if(StringFind(normalized, "market") >= 0)
      {
         DetectedPattern pattern; pattern.pattern_type = "MARKET_PATTERN"; pattern.filename = filename; pattern.confidence = 0.85; pattern.description = "Padrão de mercado detectado"; pattern.detected_time = TimeCurrent(); pattern.recommendation = "Verificar consistência"; ArrayPushBack(m_detected_patterns, pattern); m_logger.log_info("[ML] Padrão de mercado detectado: " + filename); return true;
      }
      return false;
   }

   void LearnFromPattern(string pattern_type, string filename, bool was_duplicate)
   {
      string learning_entry = pattern_type + "|" + filename + "|" + (was_duplicate ? "DUPLICATE" : "UNIQUE") + "|" + TimeToString(TimeCurrent());
      ArrayPushBack(m_learning_history, learning_entry);
      m_logger.log_info("[ML] Aprendizado registrado: " + learning_entry);
   }

   double PredictDuplicateProbability(string filename)
   {
      double probability = 0.0; int similar_patterns = 0; int total_patterns = 0;
      for(int i = 0; i < ArraySize(m_learning_history); i++)
      {
         string parts[]; StringSplit(m_learning_history[i], '|', parts);
         if(ArraySize(parts) >= 3)
         {
            if(parts[0] == "QUANTUM_DATA_PATTERN" && StringFind(StringLower(filename), "quantum") >= 0 && StringFind(StringLower(filename), "data") >= 0)
            { total_patterns++; if(parts[2] == "DUPLICATE") similar_patterns++; }
         }
      }
      if(total_patterns > 0) probability = (double)similar_patterns / total_patterns; return probability;
   }

public:
   MLDuplicateDetector(logger_institutional &logger, AuditNomenclatureValidator &nomenclature_validator) : m_logger(logger), m_nomenclature_validator(nomenclature_validator)
   {
      m_ml_analysis.total_files_analyzed = 0; m_ml_analysis.duplicates_detected = 0; m_ml_analysis.naming_patterns_found = 0; m_ml_analysis.potential_conflicts = 0; m_ml_analysis.ml_confidence = 0.0; m_ml_analysis.analysis_time = TimeCurrent();
   }

   bool AnalyzeFile(string filename, string full_path, string module)
   {
      m_logger.log_info("[ML] Analisando arquivo: " + filename);
      m_nomenclature_validator.AddFile(filename, full_path, module);
      bool pattern_found = DetectNamingPattern(filename); if(pattern_found) m_ml_analysis.naming_patterns_found++;
      double duplicate_prob = PredictDuplicateProbability(filename);
      if(duplicate_prob > 0.7) { m_logger.log_warning("[ML] Alta probabilidade de duplicata: " + filename + " (prob: " + DoubleToString(duplicate_prob, 2) + ")"); m_ml_analysis.potential_conflicts++; }
      m_ml_analysis.total_files_analyzed++;
      return true;
   }

   bool RunMLAnalysis()
   {
      m_logger.log_info("[ML] Iniciando análise ML de duplicatas...");
      if(!m_nomenclature_validator.RunNomenclatureAudit()) { m_logger.log_error("[ML] Falha na auditoria de nomenclatura"); return false; }
      int total_files, duplicates, case_errors, typo_errors; m_nomenclature_validator.GetAuditStatistics(total_files, duplicates, case_errors, typo_errors);
      m_ml_analysis.duplicates_detected = duplicates; m_ml_analysis.analysis_time = TimeCurrent();
      double confidence = 0.0; if(total_files > 0){ double error_rate = (double)(duplicates + case_errors + typo_errors) / total_files; confidence = 1.0 - error_rate; } m_ml_analysis.ml_confidence = confidence;
      m_logger.log_info("[ML] Análise ML concluída");
      return true;
   }

   void GetMLAnalysis(MLAnalysis &analysis) { analysis = m_ml_analysis; }
   void GetDetectedPatterns(DetectedPattern &patterns[]) { ArrayCopy(patterns, m_detected_patterns); }
   void RegisterLearning(string pattern_type, string filename, bool was_duplicate) { LearnFromPattern(pattern_type, filename, was_duplicate); }
};

#endif // __ML_DUPLICATE_DETECTOR_MQH__


