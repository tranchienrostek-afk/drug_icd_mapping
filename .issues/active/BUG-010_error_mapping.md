curl -X 'POST'
  'http://localhost:8000/api/v1/drugs/agent-search'
  -H 'accept: application/json'
  -H 'Content-Type: application/json'
  -d '{
  "drugs": [
    "Berodual 200 liều (xịt) - 10ml",
    "Symbicort 120 liều"
  ]
}'

result:

{
  "status": "error",
  "raw_result": ""
}
