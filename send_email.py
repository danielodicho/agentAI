import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Email configuration
subject = "Your Instagram Digest for 2025-03-13"
sender_email = "neelshettigar@gmail.com"
recipient_email = "neelshettigar@gmail.com"
sender_password = "rncs vnct iqyv yxzg"  # Use your app-specific password if using Gmail with 2FA
smtp_server = "smtp.gmail.com"
smtp_port = 465

# Create the root message as 'related' so that HTML and inline images can be linked
msg = MIMEMultipart("related")
msg["Subject"] = subject
msg["From"] = sender_email
msg["To"] = recipient_email

# Create an 'alternative' part for plain text and HTML versions
alternative = MIMEMultipart("alternative")
msg.attach(alternative)

# Plain text fallback
plain_text = "This email contains HTML content with inline images. Please view it in an HTML-capable email client."
alternative.attach(MIMEText(plain_text, "plain"))

# HTML snippet with inline image references via cid:
html_snippet = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram Highlights: Friendship, Fun, and Finds!</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #fafafa;
            color: #333;
        }
        .container {
            width: 100%;
            max-width: 600px;
            margin: auto;
            background-color: #fff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .header {
            background-color: #E1306C;
            padding: 20px;
            text-align: center;
            color: #fff;
        }
        .content {
            padding: 20px;
        }
        .section {
            margin-bottom: 20px;
        }
        .section h2 {
            color: #E1306C;
            margin-bottom: 10px;
        }
        .story {
            margin-bottom: 10px;
        }
        .story img {
            width: 100%;
            border-radius: 8px;
        }
        .story p {
            margin: 8px 0;
        }
        .footer {
            background-color: #F1F1F1;
            text-align: center;
            padding: 10px;
            font-size: 14px;
        }
        .footer a {
            color: #E1306C;
            text-decoration: none;
        }
    </style>
</head>
<body>

    <div class="container">
        <div class="header">
            <h1>Instagram Highlights</h1>
            <p>Your latest updates on friendships, fun explorations, events, and more!</p>
        </div>

        <div class="content">
            <p>Hello Instagram Subscriber,</p>
            <p>We're excited to share the latest stories from your friends and favorite influencers. Dive into the exciting updates below!</p>
            
            <!-- Friends Updates Section -->
            <div class="section" id="friends-updates">
                <h2>Friends Updates</h2>
                
                <div class="story">
                    <img src="cid:story_sample_1.png" alt="Maria Nashef's Story">
                    <p><strong>Maria Nashef</strong> shares a stylish selfie with a friend. They're looking fabulous in city fashion!</p>
                </div>

                <div class="story">
                    <img src="cid:story_sample_4.png" alt="Lady Pary's Farewell">
                    <p><strong>Lady Pary</strong> bids a heartfelt farewell. Good luck to the friend heading to Chicago! "Literally the cutest 🥰," she says.</p>
                </div>
            </div>

            <!-- Influencer Highlights Section -->
            <div class="section" id="influencer-highlights">
                <h2>Influencer Highlights</h2>

                <div class="story">
                    <img src="cid:story_sample_2.png" alt="Elite Champaign's Promotion">
                    <p><strong>Elite Champaign</strong> invites you to cool down with their refreshing drinks! "Good morning ☀️ UV is 6 today!! Come grab a refreshing drink! Open 8-5pm✨"</p>
                </div>

                <div class="story">
                    <img src="cid:story_sample_3.png" alt="KSI Fight Promo">
                    <p>Gear up for excitement with <strong>KSI</strong>'s upcoming match. Get ready for "UNFINISHED BUSINESS" in the ring!</p>
                </div>
            </div>

            <!-- Culinary Explorations Section -->
            <div class="section" id="culinary-explorations">
                <h2>Culinary Explorations</h2>

                <div class="story">
                    <img src="cid:story_sample_5.png" alt="Coffee Spot Explore">
                    <p><strong>Lady Pary</strong> explores BrewLab Coffee! She’s on the hunt for the best brews. Have any recommendations? 😎</p>
                </div>

                <div class="story">
                    <img src="cid:story_sample_6.png" alt="Dessert Adventure">
                    <p>Satisfy your sweet tooth with <strong>Lady Pary's</strong> dessert adventure at Matcha En Champaign. Discover her tailed cone treat!</p>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Thanks for catching up with us! More stories next week! Follow us on <a href="#">Instagram</a> for daily inspiration.</p>
        </div>
    </div>

    <!-- Instagram Story Images -->
    <div style='margin-top: 30px; border-top: 1px solid #ccc; padding-top: 20px;'>
        <h2 style='text-align: center; color: #ff5722;'>Original Instagram Stories</h2>
        <h3 style='margin-top: 25px; text-align: center; color: #3897f0;'>✨ Friend Stories ✨</h3>
        <div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 20px;'>
            <div style='max-width: 300px; text-align: center;'>
                <img src='cid:story_sample_1.png' style='max-width: 100%; border-radius: 8px; border: 1px solid #ddd;'>
                <p style='margin-top: 5px; font-weight: bold;'>maria.nashef</p>
            </div>
            <div style='max-width: 300px; text-align: center;'>
                <img src='cid:story_sample_4.png' style='max-width: 100%; border-radius: 8px; border: 1px solid #ddd;'>
                <p style='margin-top: 5px; font-weight: bold;'>ladypary_</p>
            </div>
            <div style='max-width: 300px; text-align: center;'>
                <img src='cid:story_sample_5.png' style='max-width: 100%; border-radius: 8px; border: 1px solid #ddd;'>
                <p style='margin-top: 5px; font-weight: bold;'>ladypary_</p>
            </div>
            <div style='max-width: 300px; text-align: center;'>
                <img src='cid:story_sample_6.png' style='max-width: 100%; border-radius: 8px; border: 1px solid #ddd;'>
                <p style='margin-top: 5px; font-weight: bold;'>ladypary_</p>
            </div>
        </div>
        <h3 style='margin-top: 25px; text-align: center; color: #e1306c;'>🔥 Influencer Content 🔥</h3>
        <div style='display: flex; flex-wrap: wrap; justify-content: center; gap: 20px;'>
            <div style='max-width: 300px; text-align: center;'>
                <img src='cid:story_sample_2.png' style='max-width: 100%; border-radius: 8px; border: 1px solid #ddd;'>
                <p style='margin-top: 5px; font-weight: bold;'>elite.champaign</p>
            </div>
            <div style='max-width: 300px; text-align: center;'>
                <img src='cid:story_sample_3.png' style='max-width: 100%; border-radius: 8px; border: 1px solid #ddd;'>
                <p style='margin-top: 5px; font-weight: bold;'>ksi</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Attach the HTML content
alternative.attach(MIMEText(html_snippet, "html"))

# Define the folder that contains the images
image_folder = "instagram_stories"

# List of expected image filenames referenced in the HTML snippet
image_filenames = [
    "story_sample_1.png",
    "story_sample_4.png",
    "story_sample_2.png",
    "story_sample_3.png",
    "story_sample_5.png",
    "story_sample_6.png"
]

# Attach each image as an inline image using its filename as the Content-ID.
for filename in image_filenames:
    filepath = os.path.join(image_folder, filename)
    try:
        with open(filepath, "rb") as img_file:
            img_data = img_file.read()
        img = MIMEImage(img_data)
        # The Content-ID must be wrapped in angle brackets.
        img.add_header("Content-ID", f"<{filename}>")
        img.add_header("Content-Disposition", "inline", filename=filename)
        msg.attach(img)
    except Exception as e:
        print(f"Error attaching {filename}: {e}")

# Send the email using SMTP_SSL
with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, recipient_email, msg.as_string())

print("Email sent successfully!")
