//+------------------------------------------------------------------+
//| TimeUtils.mqh - Utilitários de Tempo com DST (Nova Iorque)       |
//| Projeto: Genesis                                                 |
//| Pasta: Include/Utils/                                            |
//| Versão: v1.0                                                     |
//+------------------------------------------------------------------+
#ifndef __TIMEUTILS_MQH__
#define __TIMEUTILS_MQH__

// Cria um datetime a partir de componentes em UTC
static datetime MakeDateTimeUTC(const int year, const int mon, const int day, const int hour)
{
   MqlDateTime dt; dt.year = year; dt.mon = mon; dt.day = day; dt.hour = hour; dt.min = 0; dt.sec = 0;
   return StructToTime(dt);
}

// Verifica se está em horário de verão (DST) em Nova Iorque
// Regra: 2º domingo de março às 2h até 1º domingo de novembro às 2h
static bool IsDSTActive(const MqlDateTime &date)
{
   if(date.mon < 3 || date.mon > 11) return false;      // Jan, Fev, Dez
   if(date.mon > 3 && date.mon < 11) return true;       // Abr-Out

   if(date.mon == 3)
   {
      datetime firstMar = MakeDateTimeUTC(date.year, 3, 1, 0);
      MqlDateTime fm; TimeToStruct(firstMar, fm);
      int dow = fm.day_of_week; // 0=Dom
      int second_sunday = 8 + (7 - dow) % 7;
      if(date.day > second_sunday) return true;
      if(date.day == second_sunday && date.hour >= 2) return true;
      return false;
   }

   if(date.mon == 11)
   {
      datetime firstNov = MakeDateTimeUTC(date.year, 11, 1, 0);
      MqlDateTime fn; TimeToStruct(firstNov, fn);
      int dow = fn.day_of_week;
      int first_sunday = 1 + (7 - dow) % 7;
      if(date.day < first_sunday) return true;
      if(date.day == first_sunday && date.hour < 2) return true;
      return false;
   }

   return false;
}

// Retorna a hora em Nova Iorque (com DST automático)
static int GetNewYorkHour()
{
   MqlDateTime utc; TimeToStruct(TimeCurrent(), utc);
   int offset = IsDSTActive(utc) ? -4 : -5; // EDT/EST
   return (utc.hour + offset + 24) % 24;
}

// Retorna se está no horário comercial de Nova Iorque (09:00–17:00)
static bool IsNewYorkTradingHours()
{
   int hour = GetNewYorkHour();
   return hour >= 9 && hour < 17;
}

// Converte timestamp para hora de Nova Iorque
static int TimeToNewYorkHour(const datetime time)
{
   MqlDateTime utc; TimeToStruct(time, utc);
   int offset = IsDSTActive(utc) ? -4 : -5;
   return (utc.hour + offset + 24) % 24;
}

// Verifica se dois horários estão no mesmo dia de Nova Iorque
static bool IsSameNewYorkDay(const datetime time1, const datetime time2)
{
   MqlDateTime u1, u2; TimeToStruct(time1, u1); TimeToStruct(time2, u2);
   int off1 = IsDSTActive(u1) ? -4 : -5; int off2 = IsDSTActive(u2) ? -4 : -5;
   datetime ny1 = time1 + off1 * 3600; datetime ny2 = time2 + off2 * 3600;
   return (ny1 / 86400) == (ny2 / 86400);
}

#endif // __TIMEUTILS_MQH__


