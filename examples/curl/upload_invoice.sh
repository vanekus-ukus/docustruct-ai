curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@examples/generated/demo_invoice.pdf" \
  -F "document_type=invoice" \
  -F "external_id=invoice-demo-001"
