from pypdf import PdfReader, PdfWriter
import os
from io import BytesIO
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

def get_injected_asset_path(asset, injected_assets_dir=None, attack_label=None):
    if injected_assets_dir is None:
        asset_dir = os.path.dirname(os.path.abspath(asset))
        if os.path.basename(asset_dir) == "clean":
            injected_assets_dir = os.path.join(os.path.dirname(asset_dir), "injected")
        else:
            injected_assets_dir = "tests/payloads/shared/injected"

    os.makedirs(injected_assets_dir, exist_ok=True)

    filename = os.path.basename(asset)
    stem, ext = os.path.splitext(filename)
    if attack_label:
        sanitized_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in attack_label)
        filename = f"{stem}-{sanitized_label}{ext}"

    return os.path.join(injected_assets_dir, filename)

def get_asset_type(asset):
    if asset.endswith(".pdf"):
        return "pdf"
    elif asset.endswith(".html"):
        return "html"
    elif asset.endswith(".txt") and "email" in asset.lower():
        return "email"
    elif asset.endswith(".ics"):
        return "calendar"
    elif asset.endswith(".md") and "claude" in asset.lower():
        return "claude_markdown"
    else:
        return None


def inject_attack_into_pdf(asset, attack, injected_assets_dir=None, attack_label=None):
    reader = PdfReader(asset)
    writer = PdfWriter()

    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        # Draw an overlay containing the payload and merge it into the page.
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(width, height))
        c.setFont("Helvetica", 10)

        x_margin = 36
        y = 48
        max_text_width = max(100, width - (2 * x_margin))
        lines = simpleSplit(f"Injected payload: {attack}", "Helvetica", 10, max_text_width)
        for line in lines:
            c.drawString(x_margin, y, line)
            y += 12

        c.save()
        packet.seek(0)

        overlay_page = PdfReader(packet).pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)
read_text


    injected_pdf_path = get_injected_asset_path(asset, injected_assets_dir, attack_label)
    with open(injected_pdf_path, "wb") as out_file:
        writer.write(out_file)
    return injected_pdf_path

def inject_attack_into_html(asset, attack, injected_assets_dir=None, attack_label=None):
    with open(asset, "r") as f:
        html_content = f.read()

    modified_html_content = html_content + f"\n<!-- Injected payload: {attack} -->"

    injected_html_path = get_injected_asset_path(asset, injected_assets_dir, attack_label)
    with open(injected_html_path, "w") as f:
        f.write(modified_html_content)

    return injected_html_path

def inject_attack_into_email(asset, attack, injected_assets_dir=None, attack_label=None):
    with open (asset, "r") as f:
        email_content = f.read()
        

    modified_email_content = email_content + f"\n\nInjected payload: {attack}"

    injected_email_path = get_injected_asset_path(asset, injected_assets_dir, attack_label)
    with open(injected_email_path, "w") as f:
        f.write(modified_email_content)

    return injected_email_path

def inject_attack_into_calendar(asset, attack, injected_assets_dir=None, attack_label=None):
    with open(asset, "r") as f:
        calendar_content = f.read()

    modified_calendar_content = calendar_content + f"\n\nInjected payload: {attack}"

    injected_calendar_path = get_injected_asset_path(asset, injected_assets_dir, attack_label)
    with open(injected_calendar_path, "w") as f:
        f.write(modified_calendar_content)

    return injected_calendar_path

def inject_attack_into_claude_markdown(asset, attack, injected_assets_dir=None, attack_label=None):
    with open(asset, "r") as f:
        markdown_content = f.read()

    modified_markdown_content = markdown_content + f"\n\nInjected payload: {attack}"

    injected_markdown_path = get_injected_asset_path(asset, injected_assets_dir, attack_label)
    with open(injected_markdown_path, "w") as f:
        f.write(modified_markdown_content)

    return injected_markdown_path





def inject_attack(asset, attack, injected_assets_dir=None, attack_label=None):
    asset_type = get_asset_type(asset)

    if asset_type == "pdf":
        return inject_attack_into_pdf(asset, attack, injected_assets_dir, attack_label)
    
    elif asset_type == "html":
        return inject_attack_into_html(asset, attack, injected_assets_dir, attack_label)
    
    elif asset_type == "email":
        return inject_attack_into_email(asset, attack, injected_assets_dir, attack_label)
    
    elif asset_type == "calendar":
        return inject_attack_into_calendar(asset, attack, injected_assets_dir, attack_label)
    
    elif asset_type == "claude_markdown":
        return inject_attack_into_claude_markdown(asset, attack, injected_assets_dir, attack_label)
    
    else:
        print(f"Unsupported asset type for '{asset}'. Skipping injection.")
        return None



# test all paths
# if __name__ == "__main__":
#     test_assets = [
#         "tests/payloads/pdf_payload/clean/pdf-sample_0.pdf",
#         "tests/payloads/html_payload/clean/ai-research-overview.html",
#         "tests/payloads/email_payload/clean/email-shipping-update.txt",
#         "tests/payloads/calendar_payload/clean/calendar-invite-quarterly-planning.ics",
#         "tests/payloads/claude_payload/clean/claude.md"
#     ]

#     attack_payload = "This is a test payload for injection."

#     for asset in test_assets:
#         injected_asset_path = inject_attack(asset, attack_payload)
#         if injected_asset_path:
#             print(f"Injected payload into '{asset}' and saved to '{injected_asset_path}'.")
#         else:
#             print(f"Failed to inject payload into '{asset}'.")
        