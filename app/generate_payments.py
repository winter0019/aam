def create_payment_receipt(receipt_details, school_details, filename="Payment_Receipt.pdf"):
    """
    Generates a small, official Payment Receipt PDF document.
    
    Args:
        receipt_details (dict): A dictionary containing all required information.
        school_details (dict): A dictionary with school name, motto, and logo path.
        filename (str): The name of the output PDF file.
    """
    try:
        # Define the smaller page size for the receipt
        receipt_width = 4 * inch
        receipt_height = 6 * inch
        receipt_size = (receipt_width, receipt_height)
        
        c = canvas.Canvas(filename, pagesize=receipt_size)
        
        # --- Header Section: Logo, School Name, Motto ---
        # Logo on top-left. Using the school_details dict.
        logo_path = school_details.get("logo_path")
        c.drawImage(logo_path, 0.2 * inch, receipt_height - 0.8 * inch, width=60, height=60)
        
        # School Name and Motto from the school_details dict
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1.5 * inch, receipt_height - 0.5 * inch, school_details.get("name"))
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(1.5 * inch, receipt_height - 0.7 * inch, school_details.get("motto"))
        
        c.line(0.1 * inch, receipt_height - 1.2 * inch, receipt_width - 0.1 * inch, receipt_height - 1.2 * inch)
        
        # --- Title and Receipt Number ---
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(receipt_width / 2, receipt_height - 1.5 * inch, "OFFICIAL RECEIPT")
        
        c.setFont("Helvetica", 10)
        c.drawString(0.2 * inch, receipt_height - 1.8 * inch, f"Receipt No.: {receipt_details.get('receipt_no')}")
        c.drawRightString(receipt_width - 0.2 * inch, receipt_height - 1.8 * inch, f"Date: {receipt_details.get('date')}")
        
        # --- Payment Details ---
        y_position = receipt_height - 2.5 * inch
        x_position_label = 0.2 * inch
        x_position_value = 1.5 * inch

        # A list of tuples for the fields: (label, value)
        fields = [
            ("Student's Name:", receipt_details.get("student_name")),
            ("Admission No.:", receipt_details.get("admission_no")),
            ("Class:", receipt_details.get("class")),
            ("Amount Paid:", f"NGN {receipt_details.get('amount_paid'):,.2f}"),
            ("Payment Method:", receipt_details.get("payment_method")),
            ("Balance:", f"NGN {receipt_details.get('balance'):,.2f}"),
        ]

        for label, value in fields:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_position_label, y_position, label)
            c.setFont("Helvetica", 10)
            c.drawString(x_position_value, y_position, str(value))
            y_position -= 20

        # --- Signature Line ---
        y_signatures = 1.5 * inch
        c.line(0.2 * inch, y_signatures, receipt_width - 0.2 * inch, y_signatures)
        c.drawCentredString(receipt_width / 2, y_signatures - 15, "Bursar/Cashier")
        
        # Save the PDF
        c.save()
        print(f"Payment Receipt {receipt_details['receipt_no']} created successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")