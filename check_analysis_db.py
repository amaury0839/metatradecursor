"""Check analysis data in database"""
from app.core.database import get_database_manager

db = get_database_manager()
data = db.get_analysis_history(days=1)

print(f'✅ Análisis guardados en las últimas 24h: {len(data)}')

if len(data) > 0:
    print('\nÚltimos 3 registros:')
    for i, record in enumerate(data[:3], 1):
        print(f"\n{i}. Timestamp: {record.get('timestamp')}")
        print(f"   Symbol: {record.get('symbol')}")
        print(f"   Tech Signal: {record.get('tech_signal')}")
        print(f"   Sentiment: {record.get('sentiment_score')}")
        print(f"   Final Signal: {record.get('final_signal')}")
        print(f"   Confidence: {record.get('confidence')}")
else:
    print('⚠️ No hay análisis guardados')
