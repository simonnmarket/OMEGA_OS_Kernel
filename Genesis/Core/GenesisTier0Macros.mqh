// MEMORY_ID: T0PP_BOOTSTRAP
// TIMESTAMP: 2025-08-17T00:00:00Z
// AUTHOR: Cursor_Omega
#ifndef __GENESIS_TIER0_MACROS_MQH__
#define __GENESIS_TIER0_MACROS_MQH__

// ---------------------------------------------------------------------
// TIER-0++ compile-time flags (UI off by default for core headers)
// ---------------------------------------------------------------------
#ifndef GENESIS_ENABLE_UI
   #define GENESIS_ENABLE_UI 0
#endif

// ---------------------------------------------------------------------
// Minimal logging fallbacks to avoid hard dependency on LoggerInstitutional
// Use PrintFormat to keep zero-cost when not used and ensure ISO-like prefix
// ---------------------------------------------------------------------
inline void GEN_LOG_INFO(const string where, const string msg)
  {
   PrintFormat("[GENESIS][INFO][%s] %s", where, msg);
  }

inline void GEN_LOG_WARN(const string where, const string msg)
  {
   PrintFormat("[GENESIS][WARN][%s] %s", where, msg);
  }

inline void GEN_LOG_ERROR(const string where, const string msg)
  {
   PrintFormat("[GENESIS][ERROR][%s] %s", where, msg);
  }

// ---------------------------------------------------------------------
// Defensive helpers
// ---------------------------------------------------------------------
#define GEN_IS_NULL(p) ((p)==NULL)

inline bool GEN_REQUIRE(const bool condition, const string reason)
  {
   if(!condition)
     {
      GEN_LOG_ERROR("REQUIRE", reason);
      return(false);
     }
   return(true);
  }

#endif // __GENESIS_TIER0_MACROS_MQH__


