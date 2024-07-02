from twilio.rest import Client


account_sid = 'replace your sid'
auth_token = 'replace your authorization token'
client = Client(account_sid, auth_token)


message = client.messages.create(
    from_='whatsapp:+14155238886',
    body='Hello there!',
    to='whatsapp:+917397250247'
)

print(message.sid)
