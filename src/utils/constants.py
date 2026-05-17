

class STATUS:
    PENDING    = "pending"
    PROCESSING = "processing"
    DELIVERED  = "delivered"
    FAILED     = "failed"
    DEAD       = "dead"

class OUTCOME:
    SUCCESS = "success"
    FAILED  = "failed"

RETRY_INTERVALS = [30, 300, 1800]

MAX_RETRIES = 3  
