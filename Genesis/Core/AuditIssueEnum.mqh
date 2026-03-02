//+------------------------------------------------------------------+
//| audit_issue_enum.mqh - Tipos de Problemas de Auditoria           |
//| Projeto: Genesis / EA Genesis                                    |
//| Pasta: Include/Types/                                           |
//| Versão: v1.0 (TIER-0 Compliant)                               |
//| Atualizado em: 2025-01-27             |
//+------------------------------------------------------------------+
#ifndef __GENESIS_AUDIT_ISSUE_ENUM_MQH__
#define __GENESIS_AUDIT_ISSUE_ENUM_MQH__

//+------------------------------------------------------------------+
//| Enumeração de Problemas de Auditoria                             |
//+------------------------------------------------------------------+
enum ENUM_AUDIT_ISSUE
{
   AUDIT_ISSUE_INVALID_NAME,           // Nome de arquivo inválido
   AUDIT_ISSUE_MISSING_HASH,           // Falta proteção SHA3
   AUDIT_ISSUE_MISSING_BLOCKCHAIN,     // Falta registro no blockchain
   AUDIT_ISSUE_CIRCULAR_DEPENDENCY,    // Dependência circular detectada
   AUDIT_ISSUE_SECURITY_VULNERABILITY, // Vulnerabilidade de segurança
   AUDIT_ISSUE_UNDECLARED_VARIABLE,    // Variável não declarada
   AUDIT_ISSUE_INVALID_INCLUDE,        // Include inválido
   AUDIT_ISSUE_DEPRECATED_FUNCTION,    // Função obsoleta
   AUDIT_ISSUE_PERFORMANCE_ISSUE,      // Problema de performance
   AUDIT_ISSUE_MEMORY_LEAK,           // Vazamento de memória
   AUDIT_ISSUE_THREAD_SAFETY,         // Problema de thread safety
   AUDIT_ISSUE_MISSING_VALIDATION,     // Falta validação
   AUDIT_ISSUE_INVALID_PARAMETER,      // Parâmetro inválido
   AUDIT_ISSUE_MISSING_ERROR_HANDLING, // Falta tratamento de erro
   AUDIT_ISSUE_INCONSISTENT_NAMING     // Nomenclatura inconsistente
};

//+------------------------------------------------------------------+
//| Enumeração de Severidade                                          |
//+------------------------------------------------------------------+
enum ENUM_ISSUE_SEVERITY
{
   SEVERITY_LOW,      // Baixa severidade
   SEVERITY_MEDIUM,   // Média severidade
   SEVERITY_HIGH,     // Alta severidade
   SEVERITY_CRITICAL  // Severidade crítica
};

//+------------------------------------------------------------------+
//| Classe Utilitária para Conversão                                 |
//+------------------------------------------------------------------+
class CGenesisAuditIssueUtils
{
public:
   string ToString(ENUM_AUDIT_ISSUE issue)
   {
      switch(issue)
      {
         case AUDIT_ISSUE_INVALID_NAME: return "INVALID_NAME";
         case AUDIT_ISSUE_MISSING_HASH: return "MISSING_HASH";
         case AUDIT_ISSUE_MISSING_BLOCKCHAIN: return "MISSING_BLOCKCHAIN";
         case AUDIT_ISSUE_CIRCULAR_DEPENDENCY: return "CIRCULAR_DEPENDENCY";
         case AUDIT_ISSUE_SECURITY_VULNERABILITY: return "SECURITY_VULNERABILITY";
         case AUDIT_ISSUE_UNDECLARED_VARIABLE: return "UNDECLARED_VARIABLE";
         case AUDIT_ISSUE_INVALID_INCLUDE: return "INVALID_INCLUDE";
         case AUDIT_ISSUE_DEPRECATED_FUNCTION: return "DEPRECATED_FUNCTION";
         case AUDIT_ISSUE_PERFORMANCE_ISSUE: return "PERFORMANCE_ISSUE";
         case AUDIT_ISSUE_MEMORY_LEAK: return "MEMORY_LEAK";
         case AUDIT_ISSUE_THREAD_SAFETY: return "THREAD_SAFETY";
         case AUDIT_ISSUE_MISSING_VALIDATION: return "MISSING_VALIDATION";
         case AUDIT_ISSUE_INVALID_PARAMETER: return "INVALID_PARAMETER";
         case AUDIT_ISSUE_MISSING_ERROR_HANDLING: return "MISSING_ERROR_HANDLING";
         case AUDIT_ISSUE_INCONSISTENT_NAMING: return "INCONSISTENT_NAMING";
         default: return "UNKNOWN";
      }
   }

   string SeverityToString(ENUM_ISSUE_SEVERITY severity)
   {
      switch(severity)
      {
         case SEVERITY_LOW: return "BAIXA";
         case SEVERITY_MEDIUM: return "MÉDIA";
         case SEVERITY_HIGH: return "ALTA";
         case SEVERITY_CRITICAL: return "CRÍTICA";
         default: return "DESCONHECIDA";
      }
   }

   string GetDescription(ENUM_AUDIT_ISSUE issue)
   {
      switch(issue)
      {
         case AUDIT_ISSUE_INVALID_NAME: return "Nome de arquivo não segue padrão de nomenclatura";
         case AUDIT_ISSUE_MISSING_HASH: return "Arquivo sem proteção SHA3-256";
         case AUDIT_ISSUE_MISSING_BLOCKCHAIN: return "Arquivo não registrado no blockchain";
         case AUDIT_ISSUE_CIRCULAR_DEPENDENCY: return "Dependência circular detectada";
         case AUDIT_ISSUE_SECURITY_VULNERABILITY: return "Vulnerabilidade de segurança identificada";
         case AUDIT_ISSUE_UNDECLARED_VARIABLE: return "Variável utilizada sem declaração";
         case AUDIT_ISSUE_INVALID_INCLUDE: return "Include de arquivo inexistente ou inválido";
         case AUDIT_ISSUE_DEPRECATED_FUNCTION: return "Função obsoleta utilizada";
         case AUDIT_ISSUE_PERFORMANCE_ISSUE: return "Problema de performance detectado";
         case AUDIT_ISSUE_MEMORY_LEAK: return "Possível vazamento de memória";
         case AUDIT_ISSUE_THREAD_SAFETY: return "Problema de thread safety";
         case AUDIT_ISSUE_MISSING_VALIDATION: return "Falta validação de entrada";
         case AUDIT_ISSUE_INVALID_PARAMETER: return "Parâmetro inválido passado";
         case AUDIT_ISSUE_MISSING_ERROR_HANDLING: return "Falta tratamento de exceções";
         case AUDIT_ISSUE_INCONSISTENT_NAMING: return "Nomenclatura inconsistente";
         default: return "Problema desconhecido";
      }
   }

   ENUM_ISSUE_SEVERITY GetRecommendedSeverity(ENUM_AUDIT_ISSUE issue)
   {
      switch(issue)
      {
         case AUDIT_ISSUE_MISSING_HASH:
         case AUDIT_ISSUE_SECURITY_VULNERABILITY:
         case AUDIT_ISSUE_CIRCULAR_DEPENDENCY:
            return SEVERITY_CRITICAL;
         case AUDIT_ISSUE_MISSING_BLOCKCHAIN:
         case AUDIT_ISSUE_UNDECLARED_VARIABLE:
         case AUDIT_ISSUE_INVALID_INCLUDE:
         case AUDIT_ISSUE_MEMORY_LEAK:
            return SEVERITY_HIGH;
         case AUDIT_ISSUE_DEPRECATED_FUNCTION:
         case AUDIT_ISSUE_PERFORMANCE_ISSUE:
         case AUDIT_ISSUE_THREAD_SAFETY:
         case AUDIT_ISSUE_MISSING_VALIDATION:
         case AUDIT_ISSUE_INVALID_PARAMETER:
         case AUDIT_ISSUE_MISSING_ERROR_HANDLING:
            return SEVERITY_MEDIUM;
         case AUDIT_ISSUE_INVALID_NAME:
         case AUDIT_ISSUE_INCONSISTENT_NAMING:
            return SEVERITY_LOW;
         default:
            return SEVERITY_MEDIUM;
      }
   }
};

#endif // __GENESIS_AUDIT_ISSUE_ENUM_MQH__ 


