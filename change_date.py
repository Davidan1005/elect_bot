import pymupdf
import os

def change_date(file_path):

    input_pdf = file_path
    file_name = os.path.basename(input_pdf)

    output_pdf = f"{file_name} edited.pdf"

    doc = pymupdf.open(input_pdf)
    page = doc[0]


    rects = page.search_for("September 27")

    if rects:
        target_rect = rects[0]

    
        redact_box = pymupdf.Rect(
            target_rect.x0 - 1,
            target_rect.y0,       # Reduced top height shift by 2 points
            target_rect.x0 + 160, 
            target_rect.y1 + 2    # Reduced bottom height padding by 2 points
        )

        # 2. Apply redaction
        page.add_redact_annot(redact_box, fill=(1, 1, 1))
        page.apply_redactions()

        # 3. Define target box for new text
        insert_box = pymupdf.Rect(
            target_rect.x0,
            target_rect.y0 - 2,
            target_rect.x0 + 180,
            target_rect.y1 + 10
        )

        # HTML string with 12pt font size and bold "October 2nd"
        html_content = (
            '<span style="font-family: \'Times New Roman\', Times, serif; font-size: 12pt; color: black;">'
            '<b>October 2<sup>nd</sup>, 2026.</b>'
            '</span>'
        )

        # Render replacement text
        page.insert_htmlbox(insert_box, html_content)

    doc.save(output_pdf, garbage=4, deflate=True)
    doc.close()

    return output_pdf
