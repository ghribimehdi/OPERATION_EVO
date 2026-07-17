import sys
sys.path.insert(0, r'backend')
import app as backend_app
client = backend_app.app.test_client()
resp = client.get('/api/tickets/problem-groups/1/suggest-assignee')
print('STATUS', resp.status_code)
print(resp.get_data(as_text=True)[:4000])
