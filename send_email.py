"""Send the onboarding email with PDF attachment via Brevo SMTP."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
FROM_EMAIL = os.environ.get("FROM_EMAIL", "no-reply@example.com")
FROM_NAME = os.environ.get("FROM_NAME", "eCornell Personalized Learning")
TO_EMAIL = os.environ.get("TO_EMAIL", "recipient@example.com")
PDF_PATH = os.environ.get("PDF_PATH", "learning_pathway_report.pdf")

HTML_BODY = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Welcome to Your eCornell Learning Pathway</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">

<!-- Wrapper -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f5f5;">
<tr><td align="center" style="padding:20px 10px;">

<!-- Main Container -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

<!-- Header -->
<tr>
<td style="background: linear-gradient(135deg, #B31B1B 0%, #8B1515 100%); padding:40px 30px; text-align:center;">
    <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:700;letter-spacing:-0.5px;line-height:1.3;">
        Welcome to Your<br>Learning Journey
    </h1>
    <p style="margin:12px 0 0;color:rgba(255,255,255,0.85);font-size:14px;font-weight:400;">
        eCornell Personalized Learning Pathway
    </p>
</td>
</tr>

<!-- Body -->
<tr>
<td style="padding:32px 28px;">

    <!-- Greeting -->
    <p style="margin:0 0 20px;font-size:16px;color:#333;line-height:1.6;">
        Dear Nandesh,
    </p>

    <p style="margin:0 0 20px;font-size:15px;color:#444;line-height:1.7;">
        Your personalized learning pathway is ready. We've analyzed your career vision across <strong>6 strategic dimensions</strong> and matched you with <strong>29 courses</strong> from Cornell's most relevant programs.
    </p>

    <!-- Stats Bar -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;border-radius:8px;overflow:hidden;">
    <tr>
        <td width="33%" style="background:#B31B1B;padding:16px 8px;text-align:center;">
            <div style="color:#fff;font-size:24px;font-weight:700;">29</div>
            <div style="color:rgba(255,255,255,0.8);font-size:11px;text-transform:uppercase;letter-spacing:1px;">Courses</div>
        </td>
        <td width="34%" style="background:#9B1717;padding:16px 8px;text-align:center;">
            <div style="color:#fff;font-size:24px;font-weight:700;">6</div>
            <div style="color:rgba(255,255,255,0.8);font-size:11px;text-transform:uppercase;letter-spacing:1px;">Phases</div>
        </td>
        <td width="33%" style="background:#7B1313;padding:16px 8px;text-align:center;">
            <div style="color:#fff;font-size:24px;font-weight:700;">90+</div>
            <div style="color:rgba(255,255,255,0.8);font-size:11px;text-transform:uppercase;letter-spacing:1px;">LinkedIn Posts</div>
        </td>
    </tr>
    </table>

    <!-- Phase Overview -->
    <h2 style="margin:28px 0 16px;font-size:18px;color:#B31B1B;font-weight:700;border-bottom:2px solid #B31B1B;padding-bottom:8px;">
        Your 6 Learning Phases
    </h2>

    <!-- Phase Cards -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
    <tr>
    <td style="padding:14px 16px;background:#fef7f7;border-left:4px solid #B31B1B;border-radius:6px;margin-bottom:8px;">
        <div style="font-size:11px;color:#B31B1B;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Phase 1 &middot; Month 1-2</div>
        <div style="font-size:15px;color:#333;font-weight:600;margin:4px 0 2px;">Psychology + Behavioral Science</div>
        <div style="font-size:13px;color:#666;line-height:1.5;">5 courses covering decision-making, cognitive biases, consumer behavior, and emotional journey design. The intellectual foundation for everything.</div>
    </td>
    </tr>
    </table>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
    <tr>
    <td style="padding:14px 16px;background:#f7f9fe;border-left:4px solid #4f8cf7;border-radius:6px;">
        <div style="font-size:11px;color:#4f8cf7;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Phase 2 &middot; Month 2-3</div>
        <div style="font-size:15px;color:#333;font-weight:600;margin:4px 0 2px;">AI Adoption + Change Management</div>
        <div style="font-size:13px;color:#666;line-height:1.5;">5 courses on AI cultural challenges, generative AI for business, organizational change, and AI resilience. Your competitive moat.</div>
    </td>
    </tr>
    </table>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
    <tr>
    <td style="padding:14px 16px;background:#f7fdf9;border-left:4px solid #34d399;border-radius:6px;">
        <div style="font-size:11px;color:#1a9a6a;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Phase 3 &middot; Month 3-4</div>
        <div style="font-size:15px;color:#333;font-weight:600;margin:4px 0 2px;">Strategic Leadership + Productivity</div>
        <div style="font-size:13px;color:#666;line-height:1.5;">5 courses on leadership strategy, credibility, culture-productivity interconnection, and systems thinking. Become the productivity leader.</div>
    </td>
    </tr>
    </table>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
    <tr>
    <td style="padding:14px 16px;background:#fefaf5;border-left:4px solid #f59e42;border-radius:6px;">
        <div style="font-size:11px;color:#c47a20;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Phase 4 &middot; Month 4-5</div>
        <div style="font-size:15px;color:#333;font-weight:600;margin:4px 0 2px;">Marketing + Content Strategy</div>
        <div style="font-size:13px;color:#666;line-height:1.5;">5 courses on digital marketing, brand storytelling, behavioral pricing, and analytics. Turn every course into LinkedIn content.</div>
    </td>
    </tr>
    </table>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
    <tr>
    <td style="padding:14px 16px;background:#f5faf7;border-left:4px solid #2d8a5e;border-radius:6px;">
        <div style="font-size:11px;color:#2d8a5e;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Phase 5 &middot; Month 5</div>
        <div style="font-size:15px;color:#333;font-weight:600;margin:4px 0 2px;">Environmental Sciences + Sustainability</div>
        <div style="font-size:13px;color:#666;line-height:1.5;">4 courses on sustainable business, climate science, and risk management. The differentiator nobody else has.</div>
    </td>
    </tr>
    </table>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;">
    <tr>
    <td style="padding:14px 16px;background:#f5f7fa;border-left:4px solid #6366f1;border-radius:6px;">
        <div style="font-size:11px;color:#6366f1;text-transform:uppercase;letter-spacing:1px;font-weight:600;">Phase 6 &middot; Month 5-6</div>
        <div style="font-size:15px;color:#333;font-weight:600;margin:4px 0 2px;">Data Science for AI Marketing</div>
        <div style="font-size:13px;color:#666;line-height:1.5;">4 courses on trend analysis, product analytics, data communication, and AI accountability. Technical credibility for your product.</div>
    </td>
    </tr>
    </table>

    <!-- CTA -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:28px 0 20px;">
    <tr>
    <td align="center">
        <div style="background:#B31B1B;border-radius:8px;padding:16px 32px;display:inline-block;">
            <span style="color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;letter-spacing:0.3px;">
                &#128206; Your detailed learning plan is attached as a PDF
            </span>
        </div>
    </td>
    </tr>
    </table>

    <p style="margin:0 0 16px;font-size:14px;color:#666;line-height:1.7;text-align:center;">
        The attached report includes <strong>every course link</strong>, detailed rationale, suggested assignments, real-world applications, LinkedIn post ideas, and leadership development insights.
    </p>

    <!-- Divider -->
    <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">

    <!-- Quote -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr>
    <td style="padding:20px 24px;background:#fef7f7;border-radius:8px;text-align:center;">
        <p style="margin:0;font-size:15px;color:#B31B1B;font-style:italic;line-height:1.6;">
            "Productivity isn't about doing more things.<br>It's about doing the right things, sustainably,<br>with systems that scale."
        </p>
        <p style="margin:10px 0 0;font-size:12px;color:#999;">
            &mdash; Your Learning Pathway Philosophy
        </p>
    </td>
    </tr>
    </table>

    <!-- Next Steps -->
    <h2 style="margin:28px 0 12px;font-size:16px;color:#333;font-weight:700;">
        Your First Week
    </h2>

    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr>
        <td width="28" valign="top" style="padding:4px 0;"><span style="background:#B31B1B;color:#fff;border-radius:50%;width:22px;height:22px;display:inline-block;text-align:center;font-size:12px;line-height:22px;font-weight:600;">1</span></td>
        <td style="padding:4px 0 10px 10px;font-size:14px;color:#444;line-height:1.5;">Open the attached PDF and review your Phase 1 courses</td>
    </tr>
    <tr>
        <td width="28" valign="top" style="padding:4px 0;"><span style="background:#B31B1B;color:#fff;border-radius:50%;width:22px;height:22px;display:inline-block;text-align:center;font-size:12px;line-height:22px;font-weight:600;">2</span></td>
        <td style="padding:4px 0 10px 10px;font-size:14px;color:#444;line-height:1.5;">Start with <strong>"Explore the Psychology of Daily Decision Making"</strong> &mdash; block 2 hours</td>
    </tr>
    <tr>
        <td width="28" valign="top" style="padding:4px 0;"><span style="background:#B31B1B;color:#fff;border-radius:50%;width:22px;height:22px;display:inline-block;text-align:center;font-size:12px;line-height:22px;font-weight:600;">3</span></td>
        <td style="padding:4px 0 10px 10px;font-size:14px;color:#444;line-height:1.5;">Write your first LinkedIn post: <em>"I'm starting a 6-month learning journey at Cornell. Here's what I'm building toward..."</em></td>
    </tr>
    </table>

</td>
</tr>

<!-- Footer -->
<tr>
<td style="background:#1a1a2e;padding:28px;text-align:center;">
    <p style="margin:0 0 8px;color:#ffffff;font-size:14px;font-weight:600;">
        eCornell Personalized Learning
    </p>
    <p style="margin:0 0 4px;color:rgba(255,255,255,0.5);font-size:12px;">
        Powered by GraphRAG &middot; 2,176 courses &middot; 682 programs &middot; 226 instructors
    </p>
    <p style="margin:0;color:rgba(255,255,255,0.4);font-size:11px;">
        cornell.learnleadai.com
    </p>
</td>
</tr>

</table>
<!-- End Main Container -->

</td></tr>
</table>
<!-- End Wrapper -->

</body>
</html>
"""

def send():
    msg = MIMEMultipart('mixed')
    msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg['To'] = TO_EMAIL
    msg['Subject'] = "Your eCornell Learning Pathway is Ready - 29 Courses, 6 Phases, 1 Vision"

    # HTML body
    html_part = MIMEText(HTML_BODY, 'html', 'utf-8')
    msg.attach(html_part)

    # PDF attachment
    with open(PDF_PATH, 'rb') as f:
        pdf_part = MIMEBase('application', 'pdf')
        pdf_part.set_payload(f.read())
    encoders.encode_base64(pdf_part)
    pdf_part.add_header(
        'Content-Disposition', 'attachment',
        filename='eCornell_Learning_Pathway_Nandesh_Goudar.pdf'
    )
    msg.attach(pdf_part)

    # Send
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

    print(f"Email sent to {TO_EMAIL}")


if __name__ == "__main__":
    send()
