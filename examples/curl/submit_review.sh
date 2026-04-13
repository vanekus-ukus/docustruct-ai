curl -X POST "http://localhost:8000/review/tasks/<TASK_ID>/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "edit",
    "final_value": "INV-2024-001",
    "reviewer": "qa@example.com",
    "comment": "Исправлено после визуальной проверки"
  }'
