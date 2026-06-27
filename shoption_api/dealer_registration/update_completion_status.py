def update_completion_status(doc, method):
    # If document is submitted → mark completed
    if doc.docstatus == 1:
        doc.is_completed = 1
    else:
        doc.is_completed = 0
