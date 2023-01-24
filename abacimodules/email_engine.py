import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from django.conf import settings

def subscription_payment_success_template(name, subscription_plan):
    html = f'''
                Hi {name},
                You have successfully paid for the subscription plan '{subscription_plan.title}' with amount {subscription_plan.rate_month}.
            '''
    return html

def forgot_email_template(name, otp):
    html = f'''<!DOCTYPE html>
            <html lang="en">

            <head>
            <meta charset="UTF-8" />
            <meta http-equiv="X-UA-Compatible" content="IE=edge" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Email</title>
            </head>

            <body>
            <div style="
                    width: 100%;
                    height: 4rem;
                    text-align: center;
                    vertical-align: middle;

                    background: rgb(34, 195, 160);
                    background: linear-gradient(
                    90deg,
                    rgba(34, 195, 160, 1) 0%,
                    rgba(45, 168, 253, 1) 100%
                    );
                " >
                <h1 style="
                    font-family: Verdana, Geneva, Tahoma, sans-serif;
                    font-size: 2rem;
                    padding-top: 1rem;
                    color: white;
                    ">
                Fogwatch
                </h1>
            </div>
            <div style="text-align: center">
                <h1 style="
                    font-family: Verdana, Geneva, Tahoma, sans-serif;
                    font-size: 1.5rem;
                    padding-top: 1rem;
                    color: rgb(104, 100, 100);
                    ">
                Hi {name}
                Forgot your password? No problem!
                </h1>
                <br />
                <h1 style="
                    font-family: Verdana, Geneva, Tahoma, sans-serif;
                    font-size: 1rem;
                    padding-top: 1rem;
                    color: rgb(104, 100, 100);
                    ">
                You can reset a new one now! Pleas use the below OTP to create a new
                one...
                </h1>
                <br />
                <br />
                <div style="
                    position:
                    relative;
                    margin:
                    auto;
                    height:
                    75px;
                    width:
                    150px;
                    background-color:
                    rgb(66,
                    61,
                    61);
                    border-radius:
                    5px;
                    text-align:
                    center;
                    ">
                <h1 style="
                        font-family:Verdana,
                        Geneva,
                        Tahoma,
                        sans-serif;
                        font-size:
                        1.5rem;
                        padding-top:
                        1.4rem;
                        color:
                        white;
                    ">
                    {otp}
                </h1>
                </div>
                <br />
                <br />
                <h1 style="
                    font-family:Verdana,
                    Geneva,
                    Tahoma,
                    sans-serif;
                    font-size:
                    1rem;
                    padding-top:
                    1rem;
                    color:
                    rgb(104,
                    100,
                    100);
                    ">
                If you didn't request a password reset you can delete this email.
                </h1>

                <hr />
                <h1 style="
                    font-family:Verdana,
                    Geneva,
                    Tahoma,
                    sans-serif;
                    font-size:
                    .6rem;
                    padding-top:
                    1rem;
                    font-weight:
                    100;
                    color:
                    rgb(104,
                    100,
                    100);
                    ">
                This is a transactional email. © 2021 Suez. All rights
                reserved.
                </h1>
            </div>
            </body>

            </html>'''
    text = f'''
    Subject: Fogwatch password reset

    Hi {name} Forgot your password? No problem!

    You can reset a new one now! Pleas use the below OTP to create a new one... 

    OTP : {otp}
    
     '''
    return text, html

def invite_email_template(invitee, inviter, link):
    html = f''' 
    <!DOCTYPE html>
        <html lang="en">

        <head>
        <meta charset="UTF-8" />
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Email</title>
        </head>

        <body>
        <div style="
                width: 100%;
                height: 4rem;
                text-align: center;
                vertical-align: middle;

                background: rgb(34, 195, 160);
                background: linear-gradient(
                90deg,
                rgba(34, 195, 160, 1) 0%,
                rgba(45, 168, 253, 1) 100%
                );
            " >
            <h1 style="
                font-family: Verdana, Geneva, Tahoma, sans-serif;
                font-size: 2rem;
                padding-top: 1rem;
                color: white;
                ">
            Welcome to Fogwatch
            </h1>
        </div>
        <div style="text-align: center">
            <h1 style="
                font-family: Verdana, Geneva, Tahoma, sans-serif;
                font-size: 1.5rem;
                padding-top: 1rem;
                color: rgb(104, 100, 100);
                ">
            Hi {invitee}
            You have been invited to Join Fogwatch by {inviter}
            </h1>
            <br />
            <h1 style="
                font-family: Verdana, Geneva, Tahoma, sans-serif;
                font-size: 1rem;
                padding-top: 1rem;
                color: rgb(104, 100, 100);
                ">
            Please click the below link to Sign UP !!


            </h1>
            <br />
            <br />
            <div style="
                position:
                relative;
                margin:
                auto;
                height:
                75px;
                width:
                auto;
                background-color:
                rgb(66,
                61,
                61);
                border-radius:
                5px;
                text-align:
                center;
                ">
            <h1 style="
                    font-family:Verdana,
                    Geneva,
                    Tahoma,
                    sans-serif;
                    font-size:
                    1.5rem;
                    padding-top:
                    1.4rem;
                    color:
                    white;
                ">
                <a href={link}>Click Here to Join !</a>
            </h1>
            </div>
            <br />
            <br />
            <h1 style="
                font-family:Verdana,
                Geneva,
                Tahoma,
                sans-serif;
                font-size:
                1rem;
                padding-top:
                1rem;
                color:
                rgb(104,
                100,
                100);
                ">
            </h1>

            <hr />
            <h1 style="
                font-family:Verdana,
                Geneva,
                Tahoma,
                sans-serif;
                font-size:
                .6rem;
                padding-top:
                1rem;
                font-weight:
                100;
                color:
                rgb(104,
                100,
                100);
                ">
            This is a transactional email. © 2021 Fogwatch. All rights
            reserved.
            </h1>
        </div>
        </body>

        </html>
        '''
    text = f'''
    Welcome to Fogwatch !

    Hi {invitee} You have been invited to Join Fogwatch by {inviter}

    Please follow the below link to Sign UP !!

    {link}

    This is a transactional email. © 2021 Fogwatch. All rights reserved.

    '''
    return text, html


def abaci_send_email(receiver_email, subject, message_content):
    port = settings.EMAIL_PORT
    smtp_server = settings.SMTP_SERVER
    sender_email = settings.SENDER_EMAIL
    username = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email
    # Create the plain-text and HTML version of your message
    text, html = message_content
    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        # server.ehlo()  # Can be omitted
        server.starttls(context=context)
        # server.ehlo()  # Can be omitted
        server.login(username, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit

class SendEmail(threading.Thread):
    def __init__(self, subject, message_content, receiver_email):
        self.subject = subject
        self.message_content = message_content
        self.receiver_email = receiver_email
        threading.Thread.__init__(self)

    def run(self):
        abaci_send_email(self.receiver_email, self.subject, self.message_content)

