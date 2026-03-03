"""
Leaky server simulation with memory leaks.
Fix this so memory stays under 50MB after 100K iterations.
"""

import hashlib


class Request:
    def __init__(self, request_id, payload):
        self.request_id = request_id
        self.payload = payload
        self.response = None  # Circular reference: Request -> Response -> Request


class Response:
    def __init__(self, request, result):
        self.request = request  # Circular reference: Response -> Request -> Response
        self.result = result
        self.status = "ok"


class LeakyServer:
    def __init__(self):
        self.cache = {}  # Memory leak: grows forever, never evicted
        self.request_log = []  # Memory leak: keeps all requests forever

    def process_request(self, request_id, payload):
        """Process a request and return the result."""
        # Check cache first
        cache_key = self._make_cache_key(payload)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Create request/response objects with circular references
        request = Request(request_id, payload)
        result = self._compute(payload)
        response = Response(request, result)
        request.response = response  # Creates circular reference

        # Store in unbounded cache (LEAK: never evicted)
        self.cache[cache_key] = result

        # Log everything (LEAK: list grows forever)
        self.request_log.append({
            "id": request_id,
            "payload": payload,
            "result": result,
            "request_obj": request,   # Holds circular ref
            "response_obj": response,  # Holds circular ref
        })

        return result

    def _make_cache_key(self, payload):
        return hashlib.md5(payload.encode()).hexdigest()

    def _compute(self, payload):
        """Simulate some computation on the payload."""
        return hashlib.sha256(payload.encode()).hexdigest()

    def get_cache_size(self):
        return len(self.cache)

    def get_log_size(self):
        return len(self.request_log)
