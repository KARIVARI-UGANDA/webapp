"""
Email service — SMTP transactional emails with PDF receipt attachments.
All HTML uses inline styles (Gmail strips <style> blocks).
"""
import io
import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.config import settings

logger = logging.getLogger(__name__)

_UGX_PER_USD = 3700
_UGX_PER_EUR = 4050


# ── Helpers ────────────────────────────────────────────────────────────────────

def _ugx_to_display(amount_ugx: int) -> str:
    usd = amount_ugx / _UGX_PER_USD
    eur = amount_ugx / _UGX_PER_EUR
    return f"${usd:,.2f} <span style='color:#777;font-size:13px;font-weight:400;'>/ €{eur:,.2f}</span>"


def _send(to_email: str, subject: str, html: str, attachments: list[tuple[str, bytes]] | None = None) -> None:
    # ── Resend HTTP API (works on Render and any host that blocks SMTP) ────────
    if settings.resend_api_key:
        import base64
        import resend
        resend.api_key = settings.resend_api_key

        params: dict = {
            "from": f"{settings.smtp_from_name} <{settings.smtp_from_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html,
        }
        if attachments:
            params["attachments"] = [
                {"filename": name, "content": base64.b64encode(data).decode()}
                for name, data in attachments
            ]
        resend.Emails.send(params)
        return

    # ── SMTP fallback (local dev) ──────────────────────────────────────────────
    if not settings.smtp_host or not settings.smtp_username:
        logger.warning("No email provider configured — skipping send to %s", to_email)
        return

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = formataddr((settings.smtp_from_name, settings.smtp_from_email))
    msg["To"] = to_email

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html, "html"))
    msg.attach(alt)

    for filename, data in (attachments or []):
        part = MIMEApplication(data, _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)

    with smtplib.SMTP(settings.smtp_host.strip(), settings.smtp_port) as server:
        server.ehlo()
        if settings.smtp_use_tls:
            server.starttls()
            server.ehlo()
        server.login(settings.smtp_username, settings.smtp_password)
        server.sendmail(settings.smtp_from_email, to_email, msg.as_string())


# ── HTML email wrapper ─────────────────────────────────────────────────────────

def _wrap(body: str) -> str:
    base = settings.app_base_url
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#eef2eb;font-family:Arial,Helvetica,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#eef2eb;padding:40px 16px;">
  <tr><td align="center">
  <table width="600" cellpadding="0" cellspacing="0" border="0"
         style="max-width:600px;width:100%;background:#ffffff;border-radius:14px;
                overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.10);">

    <!-- ── Header ── -->
    <tr>
      <td style="background:#1a2e17;padding:36px 48px 28px;text-align:center;">
        <p style="margin:0 0 6px;font-size:24px;font-weight:700;
                  color:#ffffff;letter-spacing:0.6px;line-height:1.2;">
          🌿 Kari Vari Uganda
        </p>
        <p style="margin:0;font-size:13px;color:#93c287;letter-spacing:0.3px;">
          Premium 4×4 Car Rentals — Pearl of Africa
        </p>
      </td>
    </tr>

    <!-- ── Body ── -->
    <tr>
      <td style="padding:40px 48px 32px;">
        {body}
      </td>
    </tr>

    <!-- ── Divider ── -->
    <tr>
      <td style="padding:0 48px;">
        <hr style="border:none;border-top:1px solid #e8ede6;margin:0;">
      </td>
    </tr>

    <!-- ── Footer ── -->
    <tr>
      <td style="padding:24px 48px 32px;text-align:center;
                 font-size:12px;color:#999999;line-height:1.8;">
        <p style="margin:0 0 6px;">
          © 2026 Kari Vari Uganda &nbsp;·&nbsp;
          <a href="{base}" style="color:#3a7a34;text-decoration:none;">karivari.ug</a>
          &nbsp;·&nbsp;
          <a href="{base}/support" style="color:#3a7a34;text-decoration:none;">Support</a>
        </p>
        <p style="margin:0;font-size:11px;color:#bbbbbb;">
          Kampala &amp; Entebbe, Uganda
        </p>
      </td>
    </tr>

  </table>
  </td></tr>
  </table>

</body>
</html>"""


# ── Shared sub-components ──────────────────────────────────────────────────────

def _detail_table(rows: list[tuple[str, str]], last_big: bool = False) -> str:
    """Render a bordered detail table. Each row is (label, value).
    If last_big=True the last row gets larger, bold value text."""
    html = (
        '<table width="100%" cellpadding="0" cellspacing="0" border="0" '
        'style="border:1px solid #e2e8de;border-radius:10px;'
        'overflow:hidden;margin:24px 0;font-size:14px;">'
    )
    for i, (label, value) in enumerate(rows):
        is_last   = (i == len(rows) - 1)
        bg        = "#f7faf6" if i % 2 == 0 else "#ffffff"
        border    = "" if is_last else "border-bottom:1px solid #e8ede6;"
        val_style = (
            "font-weight:700;color:#1a2e17;font-size:16px;"
            if (is_last and last_big)
            else "font-weight:600;color:#1a1c1e;"
        )
        html += f"""
        <tr style="background:{bg};">
          <td style="padding:13px 20px;color:#555555;{border}">{label}</td>
          <td style="padding:13px 20px;text-align:right;{border}">
            <span style="{val_style}">{value}</span>
          </td>
        </tr>"""
    html += "</table>"
    return html


def _btn(text: str, url: str) -> str:
    return (
        f'<a href="{url}" '
        'style="display:inline-block;margin:8px 0 24px;padding:14px 36px;'
        'background:#2d6a27;color:#ffffff;text-decoration:none;'
        'border-radius:8px;font-weight:700;font-size:15px;'
        'letter-spacing:0.3px;">'
        f'{text}</a>'
    )


def _h2(text: str) -> str:
    return (
        f'<h2 style="margin:0 0 12px;font-size:22px;font-weight:700;'
        f'color:#1a2e17;line-height:1.3;">{text}</h2>'
    )


def _p(text: str, style: str = "") -> str:
    base = "margin:0 0 16px;font-size:15px;color:#444444;line-height:1.75;"
    return f'<p style="{base}{style}">{text}</p>'


# ── PDF receipt generator ──────────────────────────────────────────────────────

def _build_receipt_pdf(
    booking_ref: str,
    customer_name: str,
    customer_email: str,
    vehicle_name: str,
    pickup_date: str,
    return_date: str,
    total_days: int,
    amount_ugx: int,
    payment_method: str,
    gateway_ref: str,
) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

    buf   = io.BytesIO()
    doc   = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm,
    )

    styles = getSampleStyleSheet()
    dark   = colors.HexColor("#1a2e17")
    green  = colors.HexColor("#2d6a27")
    light  = colors.HexColor("#f7faf6")
    grey   = colors.HexColor("#777777")
    border = colors.HexColor("#d4e0d0")

    usd = amount_ugx / _UGX_PER_USD
    eur = amount_ugx / _UGX_PER_EUR
    ref = booking_ref[:8].upper()
    days_label = f"{total_days} day{'s' if total_days != 1 else ''}"

    title_style  = ParagraphStyle("title",  fontSize=22, textColor=colors.white,
                                  fontName="Helvetica-Bold", alignment=TA_CENTER, leading=28)
    sub_style    = ParagraphStyle("sub",    fontSize=11, textColor=colors.HexColor("#93c287"),
                                  fontName="Helvetica", alignment=TA_CENTER, leading=16)
    label_style  = ParagraphStyle("label",  fontSize=11, textColor=grey,
                                  fontName="Helvetica", alignment=TA_LEFT)
    value_style  = ParagraphStyle("value",  fontSize=11, textColor=dark,
                                  fontName="Helvetica-Bold", alignment=TA_RIGHT)
    total_style  = ParagraphStyle("total",  fontSize=14, textColor=green,
                                  fontName="Helvetica-Bold", alignment=TA_RIGHT)
    section_style = ParagraphStyle("section", fontSize=10, textColor=grey,
                                   fontName="Helvetica-Bold", alignment=TA_LEFT,
                                   spaceBefore=6)
    footer_style  = ParagraphStyle("footer",  fontSize=9,  textColor=grey,
                                   fontName="Helvetica", alignment=TA_CENTER, leading=14)

    # ── Header banner ──
    header_data = [[
        Paragraph("🌿 Kari Vari Uganda", title_style),
    ]]
    header_table = Table(header_data, colWidths=[170*mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), dark),
        ("TOPPADDING",    (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("ROUNDEDCORNERS", [6], ),
    ]))
    sub_data = [[Paragraph("Premium 4×4 Car Rentals — Pearl of Africa", sub_style)]]
    sub_table = Table(sub_data, colWidths=[170*mm])
    sub_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), dark),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))

    def row(label: str, value: str, big: bool = False):
        vs = total_style if big else value_style
        return [Paragraph(label, label_style), Paragraph(value, vs)]

    detail_rows = [
        row("Receipt Number",    f"#{ref}"),
        row("Customer Name",     customer_name),
        row("Customer Email",    customer_email),
        row("Vehicle",           vehicle_name),
        row("Rental Period",     f"{pickup_date}  →  {return_date}"),
        row("Duration",          days_label),
        row("Payment Method",    payment_method.replace("_", " ").title()),
        row("Transaction ID",    gateway_ref),
        row(f"Amount Paid  (USD / EUR)",
            f"${usd:,.2f}  /  €{eur:,.2f}", big=True),
    ]

    detail_table = Table(detail_rows, colWidths=[85*mm, 85*mm])
    detail_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.white),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [light, colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, border),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("LINEABOVE",     (0, -1), (-1, -1), 1.5, green),
    ]))

    story = [
        header_table,
        sub_table,
        Spacer(1, 10*mm),
        Paragraph("PAYMENT RECEIPT", section_style),
        HRFlowable(width="100%", thickness=1, color=border, spaceAfter=6),
        detail_table,
        Spacer(1, 8*mm),
        Paragraph(
            "Thank you for choosing Kari Vari Uganda. Please keep this receipt "
            "as proof of payment. For any questions contact support@karivari.ug.",
            footer_style,
        ),
        Spacer(1, 4*mm),
        HRFlowable(width="100%", thickness=0.5, color=border),
        Spacer(1, 3*mm),
        Paragraph("© 2026 Kari Vari Uganda · Kampala &amp; Entebbe, Uganda", footer_style),
    ]

    doc.build(story)
    return buf.getvalue()


# ── Public email functions ─────────────────────────────────────────────────────

def send_password_reset(to_email: str, full_name: str, reset_token: str) -> None:
    reset_url = f"{settings.app_base_url}/reset-password?token={reset_token}"
    body = "\n".join([
        _h2("Reset Your Password"),
        _p(f"Hi {full_name},"),
        _p(
            "We received a request to reset your Kari Vari Uganda password. "
            "Click the button below to choose a new password. "
            "This link is valid for <strong>1 hour</strong>."
        ),
        _btn("Reset Password", reset_url),
        _p(
            "If you didn't request this, you can safely ignore this email — "
            "your password will not change.",
            "font-size:13px;color:#888888;"
        ),
        f'<p style="font-size:12px;color:#bbbbbb;word-break:break-all;margin:0;">'
        f'Or copy this link:<br>{reset_url}</p>',
    ])
    _send(to_email, "Reset your Kari Vari Uganda password", _wrap(body))


def send_booking_confirmation(
    to_email: str,
    full_name: str,
    booking_ref: str,
    vehicle_name: str,
    pickup_date: str,
    return_date: str,
    total_days: int,
    amount_ugx: int,
) -> None:
    days_label = f"{total_days} day{'s' if total_days != 1 else ''}"
    ref = booking_ref[:8].upper()

    rows = [
        ("Booking Reference", f"#{ref}"),
        ("Vehicle",           vehicle_name),
        ("Pickup Date",       pickup_date),
        ("Return Date",       return_date),
        ("Duration",          days_label),
        ("Amount Paid",       _ugx_to_display(amount_ugx)),
        ("Status",            '<span style="color:#2d6a27;font-weight:700;">✓ Confirmed</span>'),
    ]

    body = "\n".join([
        _h2("Your Rental is Confirmed ✓"),
        _p(f"Hi {full_name},"),
        _p(
            "Great news — your 4×4 car rental with Kari Vari Uganda is confirmed. "
            "Your trip details are below."
        ),
        _detail_table(rows),
        _btn("View My Bookings", f"{settings.app_base_url}/my-bookings"),
        _p(
            "Your driver will reach out 24 hours before the pickup date. "
            "Have a wonderful trip through Uganda!",
            "font-size:13px;color:#666666;"
        ),
    ])
    _send(to_email, f"Rental Confirmed — {vehicle_name} · Kari Vari Uganda", _wrap(body))


def send_invoice(
    to_email: str,
    full_name: str,
    booking_ref: str,
    vehicle_name: str,
    pickup_date: str,
    return_date: str,
    total_days: int,
    amount_ugx: int,
    payment_method: str,
    gateway_ref: str,
) -> None:
    days_label = f"{total_days} day{'s' if total_days != 1 else ''}"
    ref = booking_ref[:8].upper()
    usd = amount_ugx / _UGX_PER_USD
    eur = amount_ugx / _UGX_PER_EUR

    rows = [
        ("Receipt Number",   f"#{ref}"),
        ("Vehicle",          vehicle_name),
        ("Rental Period",    f"{pickup_date} → {return_date}"),
        ("Duration",         days_label),
        ("Payment Method",   payment_method.replace("_", " ").title()),
        ("Transaction ID",   f'<span style="font-size:12px;color:#555;">{gateway_ref}</span>'),
        ("Amount Paid",      _ugx_to_display(amount_ugx)),
    ]

    # Build PDF receipt
    try:
        pdf_bytes = _build_receipt_pdf(
            booking_ref=booking_ref,
            customer_name=full_name,
            customer_email=to_email,
            vehicle_name=vehicle_name,
            pickup_date=pickup_date,
            return_date=return_date,
            total_days=total_days,
            amount_ugx=amount_ugx,
            payment_method=payment_method,
            gateway_ref=gateway_ref,
        )
        attachments = [(f"KariVari_Receipt_{ref}.pdf", pdf_bytes)]
    except Exception as exc:
        logger.error("PDF generation failed: %s", exc)
        attachments = []

    body = "\n".join([
        _h2("Payment Receipt"),
        _p(f"Hi {full_name},"),
        _p(
            "Thank you for your payment. Your receipt is attached as a PDF. "
            "A summary of your transaction is also shown below."
        ),
        _detail_table(rows, last_big=True),
        _p(
            f"<strong>Total: ${usd:,.2f} USD &nbsp;/&nbsp; €{eur:,.2f} EUR</strong>",
            "font-size:16px;color:#2d6a27;margin-bottom:20px;"
        ),
        _btn("View My Bookings", f"{settings.app_base_url}/my-bookings"),
        _p(
            "Please keep the attached PDF as your official proof of payment. "
            'For any questions visit our <a href="'
            + settings.app_base_url
            + '/support" style="color:#2d6a27;">support page</a>.',
            "font-size:13px;color:#666666;"
        ),
    ])
    _send(
        to_email,
        f"Payment Receipt — Kari Vari Car Rental #{ref}",
        _wrap(body),
        attachments=attachments,
    )


def send_newsletter_welcome(to_email: str) -> None:
    items = [
        ("🦁", "Safari destination highlights from Uganda"),
        ("🚗", "New verified 4×4 listings added each week"),
        ("💸", "Exclusive subscriber deals and early access"),
        ("🗺️", "Travel tips for the Pearl of Africa"),
    ]
    list_html = "".join(
        f'<tr><td style="padding:8px 0;font-size:15px;color:#444444;vertical-align:top;">'
        f'{icon}&nbsp;</td>'
        f'<td style="padding:8px 0;font-size:15px;color:#444444;line-height:1.6;">{text}</td></tr>'
        for icon, text in items
    )

    body = "\n".join([
        _h2("Welcome to Kari Vari Uganda 🌿"),
        _p("You're now on our list. Here's what to expect:"),
        f'<table cellpadding="0" cellspacing="0" border="0" style="margin:8px 0 24px;">'
        f'{list_html}</table>',
        _btn("Browse Rental Vehicles", f"{settings.app_base_url}/vehicles"),
        _p(
            "You can unsubscribe at any time by replying &ldquo;unsubscribe&rdquo; to this email.",
            "font-size:12px;color:#aaaaaa;"
        ),
    ])
    _send(to_email, "Welcome to Kari Vari Uganda — You're on the list!", _wrap(body))
