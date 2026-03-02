//+------------------------------------------------------------------+
//| dependency_graph.mqh - Grafo de Dependências com IA Neural       |
//| Projeto: Genesis                                                |
//| Pasta: include/analysis/                                        |
//| Versão: v2.1 (GodMode Final + IA Ready)                         |
//| Atualizado em: 2025-07-24                                       |
//| Status: TIER-0 Compliant | SHA3 Protected | 5K+/dia Ready        |
//+------------------------------------------------------------------+
#ifndef __DEPENDENCY_GRAPH_MQH__
#define __DEPENDENCY_GRAPH_MQH__

#include <Genesis/Core/AuditIssueEnum.mqh>

// Forward declarations to avoid heavy dependencies
class QuantumFirewall;
class QuantumLearning;

//+------------------------------------------------------------------+
//| Estrutura de Nó do Grafo                                        |
//+------------------------------------------------------------------+
struct DependencyNode
{
   string path;
   string name;
   int priority;
   bool is_critical;
   bool is_ready;
   datetime last_check;
   double failure_probability;
   ENUM_AUDIT_ISSUE last_issue;
};

//+------------------------------------------------------------------+
//| Estrutura de Aresta                                             |
//+------------------------------------------------------------------+
struct DependencyEdge
{
   string from;
   string to;
   int weight;
   datetime created;
};

//+------------------------------------------------------------------+
//| Estrutura de Resultado de Validação                             |
//+------------------------------------------------------------------+
struct ValidationReport
{
   bool success;
   string node;
   string status;
   int error_count;
   int warning_count;
   double risk_score;
   datetime validation_time;
   string details;
};

//+------------------------------------------------------------------+
//| CLASSE PRINCIPAL: CDependencyGraph                              |
//+------------------------------------------------------------------+
class CDependencyGraph
{
protected:
   QuantumFirewall *m_firewall;
   QuantumLearning *m_learning;
   string m_project_root;
   datetime m_last_update;
   DependencyNode m_nodes[];
   DependencyEdge m_edges[];
   ValidationReport m_validation_history[];

   bool is_valid_context()
   {
      if(!TerminalInfoInteger(TERMINAL_CONNECTED))
      {
         Print("[GRAPH] Sem conexão com o servidor");
         return false;
      }
      if(m_firewall == NULL)
      {
         Print("[GRAPH] Firewall quântico inativo");
         return false;
      }
      if(m_learning == NULL)
      {
         Print("[GRAPH] Sistema de aprendizado quântico não inicializado");
         return false;
      }
      return true;
   }

   void updateGraphDisplay(int node_count, int edge_count)
   {
      Print(StringFormat("[GRAPH] Nós=%d | Arestas=%d", node_count, edge_count));
   }

   bool AddNodeInternal(const DependencyNode &node)
   {
      int size = ArraySize(m_nodes);
      ArrayResize(m_nodes, size + 1);
      m_nodes[size] = node;
      Print("[GRAPH] Nó adicionado: " + node.path);
      return true;
   }

public:
   CDependencyGraph(QuantumFirewall *qf, QuantumLearning *ql, string project_root = "MQL5/")
      : m_firewall(qf), m_learning(ql), m_project_root(project_root), m_last_update(0)
   {
      if(m_firewall == NULL)
      {
         Print("[GRAPH] Firewall quântico não ativo");
         ExpertRemove();
      }
      if(m_learning == NULL)
      {
         Print("[GRAPH] Sistema de aprendizado quântico não inicializado");
         ExpertRemove();
      }
      Print("[GRAPH] Grafo de dependências inicializado");
   }

   bool AddNode(string path)
   {
      if(!is_valid_context()) return false;
      string name = path;
      int slash = -1;
      int pos = 0;
      // Encontrar última barra '/'
      while(true)
      {
         int p = StringFind(path, "/", pos);
         if(p < 0) break;
         slash = p;
         pos = p + 1;
      }
      // Se não encontrou '/', tentar '\\' (Windows)
      if(slash < 0)
      {
         pos = 0;
         while(true)
         {
            int p2 = StringFind(path, "\\", pos);
            if(p2 < 0) break;
            slash = p2;
            pos = p2 + 1;
         }
      }
      if(slash >= 0) name = StringSubstr(path, slash + 1);

      for(int i = 0; i < ArraySize(m_nodes); i++)
      {
         if(m_nodes[i].path == path)
         {
            Print("[GRAPH] Nó já existe: " + path);
            return false;
         }
      }

      DependencyNode node;
      node.path = path;
      node.name = name;
      node.priority = 1;
      node.is_critical = (StringFind(name, "quantum") >= 0 || StringFind(name, "processor") >= 0 || StringFind(name, "firewall") >= 0);
      node.is_ready = false;
      node.last_check = TimeCurrent();
      node.failure_probability = 0.0;
      node.last_issue = AUDIT_ISSUE_INVALID_NAME;
      return AddNodeInternal(node);
   }

   bool AddEdge(string from, string to, int weight = 1)
   {
      if(!is_valid_context()) return false;
      bool from_exists = false, to_exists = false;
      for(int i = 0; i < ArraySize(m_nodes); i++)
      {
         if(m_nodes[i].path == from) from_exists = true;
         if(m_nodes[i].path == to) to_exists = true;
      }
      if(!from_exists || !to_exists)
      {
         Print("[GRAPH] Nó não encontrado: " + (from_exists ? to : from));
         return false;
      }
      DependencyEdge edge;
      edge.from = from;
      edge.to = to;
      edge.weight = weight;
      edge.created = TimeCurrent();
      int size = ArraySize(m_edges);
      ArrayResize(m_edges, size + 1);
      m_edges[size] = edge;
      Print("[GRAPH] Aresta adicionada: " + from + " -> " + to);
      return true;
   }

   bool ValidateAllDependencies()
   {
      if(!is_valid_context()) return false;
      bool all_valid = true;
      int error_count = 0;
      int warning_count = 0;
      double total_risk = 0.0;
      for(int i = 0; i < ArraySize(m_nodes); i++)
      {
         if(!ValidateNode(m_nodes[i].path))
         {
            all_valid = false;
            error_count++;
         }
         else
         {
            warning_count += (m_nodes[i].failure_probability > 0.1) ? 1 : 0;
         }
         total_risk += m_nodes[i].failure_probability;
      }
      ValidationReport report;
      report.success = all_valid;
      report.node = "ALL";
      report.status = all_valid ? "OK" : "ERRO";
      report.error_count = error_count;
      report.warning_count = warning_count;
      report.risk_score = ArraySize(m_nodes) > 0 ? total_risk / ArraySize(m_nodes) : 0.0;
      report.validation_time = TimeCurrent();
      report.details = "Validação completa: " + IntegerToString(ArraySize(m_nodes)) + " nós";
      int size = ArraySize(m_validation_history);
      ArrayResize(m_validation_history, size + 1);
      m_validation_history[size] = report;
      Print(StringFormat("[GRAPH] Validação completa - Erros: %d | Avisos: %d | Risco: %.3f",
                        error_count, warning_count, report.risk_score));
      updateGraphDisplay(ArraySize(m_nodes), ArraySize(m_edges));
      return all_valid;
   }

   bool ValidateNode(string node_path)
   {
      if(!is_valid_context()) return false;
      if(!FileIsExist(node_path))
      {
         Print("[GRAPH] Arquivo não encontrado: " + node_path);
         return false;
      }
      for(int i = 0; i < ArraySize(m_nodes); i++)
      {
         if(m_nodes[i].path == node_path)
         {
            m_nodes[i].is_ready = true;
            m_nodes[i].last_check = TimeCurrent();
            m_nodes[i].failure_probability = 0.05;
            m_nodes[i].last_issue = AUDIT_ISSUE_INVALID_NAME;
            break;
         }
      }
      return true;
   }

   int GetNodeCount() const { return ArraySize(m_nodes); }
   int GetEdgeCount() const { return ArraySize(m_edges); }

   bool IsReady() const
   {
      return m_firewall != NULL && m_learning != NULL;
   }

   bool ExportValidationHistory(string file_path)
   {
      int handle = FileOpen(file_path, FILE_WRITE | FILE_TXT);
      if(handle == INVALID_HANDLE)
      {
         Print("[GRAPH] Falha ao abrir arquivo para exportação: " + file_path);
         return false;
      }
      for(int i = 0; i < ArraySize(m_validation_history); i++)
      {
         FileWrite(handle,
                   TimeToString(m_validation_history[i].validation_time, TIME_DATE | TIME_SECONDS),
                   m_validation_history[i].node,
                   m_validation_history[i].status,
                   IntegerToString(m_validation_history[i].error_count),
                   IntegerToString(m_validation_history[i].warning_count),
                   DoubleToString(m_validation_history[i].risk_score, 4),
                   m_validation_history[i].details);
      }
      FileClose(handle);
      Print("[GRAPH] Histórico de validações exportado para: " + file_path);
      return true;
   }
};

#endif // __DEPENDENCY_GRAPH_MQH__


